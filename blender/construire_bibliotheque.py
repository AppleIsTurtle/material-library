r"""Construit bibliotheque\blender_<X.Y>\bibliotheque_matieres.blend (chunk-06) : la bibliothèque d'assets de Lou pour l'Asset Browser,
un fichier par version de Blender (celle qui lance le script ; 4.4 n'ouvre pas un .blend de la 5.x).
    blender -b --factory-startup --python blender\construire_bibliotheque.py -- [quick]
    (lancer via D:\Claude\MFS\outils\blender_garde.ps1 ; pour la 4.4 : F:\Blender\blender.exe)
Contenu, tout marqué comme asset, rangé dans des catalogues (blender_assets.cats.txt à côté du .blend, uuid stables) :
  - une matière par fiche du catalogue (material_library.matieres.catalogue), description = fiche (procédé, source, décision) ;
  - les variantes de procédé utiles à la main (FDM de l'imprimeur FDM en buses 0,4 / 0,2, PLA naturel translucide) ;
  - quelques pièces de visserie toutes faites (une collection par pièce : tête + tige) ;
aperçu rendu pour chaque asset (boule ou pièce, Cycles), images packées. Unités : 1 unité = 1 mm (échelle 0,001), comme les
scènes de MFS — les grains et les couches sont en mm.
Le fichier est GÉNÉRÉ : jamais retouché à la main (les retouches vont dans le catalogue) ; l'ancien est archivé dans
G:\Blender\Bibliotheque\_archives\ (hors git) avant chaque régénération. Déclaration dans Blender : methode/matieres.md § Bibliothèque dans Blender."""
import datetime
import math
import os
import shutil
import sys
import tempfile
import uuid

import bmesh
import bpy
from mathutils import Vector

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
import material_library as SP                                   # noqa: E402
from material_library import aretes as AR                       # noqa: E402
from material_library.imperfections import uv_mm                # noqa: E402
from material_library.matieres import catalogue as CAT          # noqa: E402
from material_library.matieres import procedes as PR            # noqa: E402
from material_library.visserie import pieces as PC              # noqa: E402

ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
QUICK = "quick" in ARGV
VERSION_BLENDER = "{}.{}".format(*bpy.app.version[:2])        # un .blend par version : Blender 4.4 n'ouvre pas ceux de la 5.x
DOSSIER = os.path.join(RACINE, "bibliotheque", f"blender_{VERSION_BLENDER}")   # suivi par git (le dépôt suffit pour installer)
FICHIER = os.path.join(DOSSIER, "bibliotheque_matieres.blend")
AUTEUR = "Lou · material-library"
ESPACE = uuid.UUID("6f1c3a52-6b0e-4d1f-9a57-3d0c2f8e9b11")   # uuid des catalogues = uuid5(ESPACE, chemin) : stables

VARIANTES = [  # (nom de la matière, catalogue, description, fabrique)
    ("SP_PLA_noir_FDM_02", "Impression FDM/Couches", "PLA noir imprimé chez l'imprimeur FDM, buse 0,4 : couches de 0,2 le long de l'axe Y "
     "de l'objet, face -Y sur le plateau texturé (grain brillant) (couches procédurales ; vrais trajets de la buse : vue 3D > Material library > Impression FDM > Recalculer les trajets)", lambda: PR.fdm("pla_noir", buse=0.4, axe="Y", plateau="-Y")),
    ("SP_PLA_noir_FDM_01", "Impression FDM/Couches", "PLA noir, buse 0,2 : couches de 0,1 le long de Y, face -Y sur le plateau (couches procédurales ; vrais trajets de la buse : vue 3D > Material library > Impression FDM > Recalculer les trajets)",
     lambda: PR.fdm("pla_noir", buse=0.2, axe="Y", plateau="-Y")),
    ("SP_PLA_blanc_FDM_02", "Impression FDM/Couches", "PLA blanc (#c9c7c1), buse 0,4 : couches de 0,2 le long de Y (couches procédurales ; vrais trajets de la buse : vue 3D > Material library > Impression FDM > Recalculer les trajets)",
     lambda: PR.fdm("pla_blanc", buse=0.4, axe="Y")),
    ("SP_PLA_naturel_FDM_02", "Impression FDM/Couches", "PLA naturel translucide (guides de lumière), buse 0,4, couches le long de Y (couches procédurales ; vrais trajets de la buse : vue 3D > Material library > Impression FDM > Recalculer les trajets)",
     lambda: PR.fdm("pla_naturel", buse=0.4, axe="Y", translucide=0.45)),
]
VISSERIE = ["M4 x 8 DIN 84 inox", "M3 x 10 ISO 7046 oxyde", "M3 x 8 ISO 7045 inox", "M3 x 8 ISO 4762 inox",
            "M3 ISO 4032 inox", "M3 DIN 125 inox", "M3 INSERT laiton"]


def catalogue_id(chemin, cats):
    cats.setdefault(chemin, str(uuid.uuid5(ESPACE, chemin)))
    return cats[chemin]


def ecrire_catalogues(dossier, cats):
    lignes = ["# This is an Asset Catalog Definition file for Blender.", "# Généré par material-library/blender/construire_bibliotheque.py",
              "", "VERSION 1", ""]
    tous = dict(cats)
    for chemin in list(cats):                                  # parents (« Impression FDM » pour « Impression FDM/Couches »)
        parts = chemin.split("/")
        for k in range(1, len(parts)): catalogue_id("/".join(parts[:k]), tous)
    for chemin, u in sorted(tous.items()):
        lignes.append(f"{u}:{chemin}:{chemin.replace('/', '-')}")
    with open(os.path.join(dossier, "blender_assets.cats.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lignes) + "\n")


# ------------------------------------------------------------------ scène vide en mm et petit studio pour les aperçus
for o in list(bpy.data.objects): bpy.data.objects.remove(o)    # scène d'usine (--factory-startup) vidée
bpy.data.orphans_purge(do_recursive=True)
sc = bpy.context.scene
sc.unit_settings.system = "METRIC"; sc.unit_settings.scale_length = 0.001; sc.unit_settings.length_unit = "MILLIMETERS"
sc.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"; prefs.get_devices()
for d in prefs.devices: d.use = d.type == "OPTIX"
sc.cycles.device = "GPU"; sc.cycles.samples = 24 if QUICK else 96; sc.cycles.use_denoising = True
sc.render.resolution_x = sc.render.resolution_y = 256; sc.render.film_transparent = True
sc.view_settings.view_transform = "AgX"
STUDIO = bpy.data.collections.new("_APERCU"); sc.collection.children.link(STUDIO)
w = bpy.data.worlds.new("_apercu"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.35, 0.38, 0.42, 1); w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6


def lampe(nom, loc, taille, puissance):
    l = bpy.data.lights.new(nom, "AREA"); l.size = taille; l.energy = puissance
    o = bpy.data.objects.new(nom, l); STUDIO.objects.link(o); o.location = loc
    o.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


lampe("_cle", (-60, -70, 80), 60, 2.0e5); lampe("_contre", (70, 60, 50), 40, 1.0e5); lampe("_bas", (40, -80, -20), 50, 3.0e4)
cd = bpy.data.cameras.new("_cam"); cd.lens = 85; cd.clip_start = 1; cd.clip_end = 2000
CAM = bpy.data.objects.new("_cam", cd); STUDIO.objects.link(CAM); sc.camera = CAM
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=96, v_segments=48, radius=10.0)
me = bpy.data.meshes.new("_boule"); bm.to_mesh(me); bm.free(); me.shade_smooth()
BOULE = bpy.data.objects.new("_boule", me); STUDIO.objects.link(BOULE); uv_mm.uv_plan_mm(BOULE)
APERCUS = os.path.join(tempfile.gettempdir(), "sp_apercus"); os.makedirs(APERCUS, exist_ok=True)


def viser(objets, marge=0.95):
    """Caméra de trois quarts cadrée sur les objets (sphère englobante)."""
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in objets for c in o.bound_box]
    c = sum(pts, Vector()) / len(pts); r = max((p - c).length for p in pts)
    d = r * marge / math.tan(CAM.data.angle / 2)
    CAM.location = c + Vector((-0.55, -0.75, 0.45)).normalized() * d
    CAM.rotation_euler = (c - CAM.location).to_track_quat("-Z", "Y").to_euler()


def apercu(id_, objets):
    """Rend l'aperçu de l'asset id_ (seuls `objets` visibles) et le charge comme aperçu personnalisé."""
    for o in sc.objects:
        if o.type in ("MESH", "CURVE"): o.hide_render = o not in objets
    viser(objets)
    f = os.path.join(APERCUS, f"{id_.name}.png"); sc.render.filepath = f
    bpy.ops.render.render(write_still=True)
    with bpy.context.temp_override(id=id_):
        bpy.ops.ed.lib_id_load_custom_preview(filepath=f)


def marquer(id_, catalogue, description, tags, cats):
    id_.asset_mark()
    a = id_.asset_data; a.catalog_id = catalogue_id(catalogue, cats); a.description = description; a.author = AUTEUR
    for t in tags: a.tags.new(t, skip_if_exists=True)


# ------------------------------------------------------------------ matières du catalogue et variantes
cats = {}
assets = []
for nom, f in CAT.CATALOGUE.items():
    m = CAT.construire(nom)
    desc = f"{f['titre']}. Procédé : {f['procede']}. Base {f['base']} (studio du site)" + (f", cible {f['cible']}" if f["cible"] else "")
    desc += f". Bevel {f['bevel']} mm. Source : {f['source']} ({f['date']})." + (f" Décision : {f['decision']}." if f["decision"] else "")
    desc += " Unités : mm (échelle 0,001)."
    marquer(m, f["famille"], desc, (f["famille"], nom), cats); assets.append((m, [BOULE]))
for nom, catal, desc, fab in VARIANTES:
    m = fab(); m.name = nom
    marquer(m, catal, desc + ". Unités : mm (échelle 0,001).", ("FDM", "procédé"), cats); assets.append((m, [BOULE]))

# ------------------------------------------------------------------ visserie toute faite (une collection par pièce)
for k, des in enumerate(VISSERIE):
    c = bpy.data.collections.new(des.replace(" x ", "x").replace(" ", "_")); sc.collection.children.link(c)
    objs = PC.piece(des, 0.0, 0.0, 0.0, col=c, prefixe="SP_" + c.name)
    marquer(c, "Visserie", f"{des} (material_library.visserie.pieces). Axe le long de Y, tête côté -Y, posée en y = 0. Unités : mm.",
            ("visserie",), cats)
    assets.append((c, objs))

# ------------------------------------------------------------------ aperçus, puis on retire le studio
for id_, objets in assets:
    if isinstance(id_, bpy.types.Material):
        BOULE.data.materials.clear(); BOULE.data.materials.append(id_)
    apercu(id_, objets)
    print("ASSET", type(id_).__name__, id_.name, flush=True)
for o in list(STUDIO.objects): bpy.data.objects.remove(o)
bpy.data.collections.remove(STUDIO)
for c in [c for c in sc.collection.children]: sc.collection.children.unlink(c)   # pièces : assets seulement, hors de la scène
sc.world = None; bpy.data.worlds.remove(w)
bpy.data.orphans_purge(do_recursive=True)                     # restes du studio (les assets ont un faux utilisateur)

# ------------------------------------------------------------------ images packées, archive, enregistrement
for im in bpy.data.images:
    if im.source == "FILE" and not im.packed_file and im.filepath: im.pack()
os.makedirs(DOSSIER, exist_ok=True)
if os.path.exists(FICHIER):
    arch = os.path.join(SP.DONNEES, "_archives"); os.makedirs(arch, exist_ok=True)
    dst = os.path.join(arch, f"bibliotheque_matieres_{datetime.datetime.now():%Y-%m-%d_%H%M}_blender_{VERSION_BLENDER}.blend")
    shutil.move(FICHIER, dst); print("ARCHIVE", dst, flush=True)
bpy.ops.wm.save_as_mainfile(filepath=FICHIER, compress=True, check_existing=False)
ecrire_catalogues(DOSSIER, cats)
nm = sum(1 for i, _ in assets if isinstance(i, bpy.types.Material)); nc = len(assets) - nm
print(f"FINI {FICHIER} : {nm} matières, {nc} pièces de visserie, {len(cats)} catalogues", flush=True)
