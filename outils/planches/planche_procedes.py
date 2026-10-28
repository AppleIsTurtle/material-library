r"""Planche « une pièce, tous les procédés » (chunk-04) : la même plaque 36 × 22 × 4 (inscription « COM 1 », fenêtre à congé),
imprimée ou fabriquée par chaque procédé ; vue de trois quarts (face) et gros plan rasant de la tranche (couches).
Trois étapes :
  1. blender -b G:\Blender\MFS\plans_fixes\site\hero.blend --python outils\planches\planche_procedes.py -- etape=stl
     → <sortie>\stl\piece.stl, lettres.stl
  2. Python système (numpy, scipy, shapely, Pillow) :
     (trajets FDM : lancés tout seuls au rendu, impression\tranchage.py <sortie>\trajets_0.4.npz 0.4 piece.stl --plateau -Y)
     python material_library\impression\lettres.py <sortie>\stl\lettres.stl <sortie>\lettres_0.4.npz 0.4   (idem 0.2, exact)
  3. blender -b …hero.blend --python outils\planches\planche_procedes.py -- [quick]   puis assembler.py
Repère des maquettes : face avant en y = 0 (sur le plateau pour le FDM), -y vers l'utilisateur."""
import json
import math
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import studio as ST                                   # noqa: E402
import material_library as SP                           # noqa: E402
import bpy                                            # noqa: E402
import numpy as np                                    # noqa: E402
from mathutils import Matrix                          # noqa: E402
from material_library import aretes as AR               # noqa: E402
from material_library.imperfections import uv_mm        # noqa: E402
from material_library.matieres import procedes as PR    # noqa: E402

ETAPE = next((a[6:] for a in ST.ARGV if a.startswith("etape=")), "rendu")
sc, col, SORTIE = ST.preparer("procedes", res=(1000, 750))
W, H, E = 36.0, 22.0, 4.0
TEXTE, CAP, TX, TZ = "COM 1", 4.0, -5.0, 15.5
FEN = (14.0, 6.0, 1.0, 6.0, 6.0)                       # fenêtre : w, h, rayon, x, z


def piece(nom):
    bm = AR.plaque(W, H, 2.0, 0.0, E, (0.4, 0.4), cz=H / 2)
    me = bpy.data.meshes.new(nom); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(nom, me); col.objects.link(o)
    fw, fh, fr, fx, fz = FEN
    AR.retrancher(o, [AR.coupe(AR.contour_rrect(fw, fh, fr), -1.0, E + 1.0, conge=0.4, cx=fx, cz=fz)])
    uv_mm.uv_plan_mm(o)
    return o


def lettres():
    """Inscription en prisme de 0,6 (y 0 → 0,6), face avant à fleur : son STL donne le masque (premier calque à y = 0,1)."""
    cu = bpy.data.curves.new("txt", "FONT"); cu.body = TEXTE
    cu.font = bpy.data.fonts.load(r"C:\Windows\Fonts\arialbd.ttf", check_existing=True)
    cu.size = CAP / 0.716; cu.extrude = 0.3; cu.align_x = "CENTER"; cu.align_y = "CENTER"
    o = bpy.data.objects.new("txt", cu); col.objects.link(o)
    o.rotation_euler = (math.radians(90), 0, 0); o.location = (TX, 0.3, TZ)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg)); me.transform(o.matrix_basis)
    zs = [v.co.z for v in me.vertices]; me.transform(Matrix.Translation((0, 0, TZ - (min(zs) + max(zs)) / 2)))
    bpy.data.objects.remove(o); bpy.data.curves.remove(cu)
    ob = bpy.data.objects.new("PROC_lettres", me); col.objects.link(ob)
    return ob


if ETAPE == "stl":
    d = os.path.join(SORTIE, "stl"); os.makedirs(d, exist_ok=True)
    for o, f in ((piece("PROC_piece"), "piece.stl"), (lettres(), "lettres.stl")):
        for x in bpy.context.view_layer.objects: x.select_set(False)
        o.select_set(True); bpy.context.view_layer.objects.active = o
        bpy.ops.wm.stl_export(filepath=os.path.join(d, f), export_selected_objects=True, apply_modifiers=True, global_scale=1.0)
        print("STL", os.path.join(d, f), flush=True)
    sys.exit(0)

charge = lambda n: np.load(os.path.join(SORTIE, n))


def trajets(buse):
    """Trajets simulés de la pièce (fdm-trajets) : tranchage.py par le Python système, une fois par buse."""
    npz = os.path.join(SORTIE, f"trajets_{buse}.npz")
    if not os.path.exists(npz):
        r = subprocess.run([SP.PYTHON_SYSTEME, os.path.join(SP.RACINE, "material_library", "impression", "tranchage.py"), npz, str(buse),
                            os.path.join(SORTIE, "stl", "piece.stl"), "--plateau", "-Y"], capture_output=True, text=True)
        if r.returncode: raise RuntimeError(r.stdout[-1500:] + r.stderr[-1500:])
    return npz


COLONNES = [  # (clé, titre, note, fabrique(objet) -> matière)
    ("fdm04", "FDM PLA noir, buse 0,4", "l'imprimeur FDM (U1) : trajets réels simulés (profil U1), face sur le plateau",
     lambda o: PR.lettres_imprimees(PR.trajets(PR.poser(o, PR.fdm("pla_noir", buse=0.4, axe="Y", plateau="-Y", nom="PROC_fdm04")),
                                               trajets(0.4)), charge("lettres_0.4.npz"))),
    ("fdm02", "FDM PLA noir, buse 0,2", "couches 0,1, cordons 0,22 : lettres plus nettes",
     lambda o: PR.lettres_imprimees(PR.trajets(PR.poser(o, PR.fdm("pla_noir", buse=0.2, axe="Y", plateau="-Y", nom="PROC_fdm02")),
                                               trajets(0.2)), charge("lettres_0.2.npz"))),
    ("sla_huilee", "SLA JLC Black poncée huilée", "JLC3DP : satinée, grain fin, aspect « injecté »",
     lambda o: PR.poser(o, PR.sla("sla_jlc_black", "poncee_huilee")).data.materials[0]),
    ("sla_9600", "SLA 9600 blanche brute", "JLC3DP : lumière qui s'arrondit dans les bords",
     lambda o: PR.poser(o, PR.sla("resine_9600_blanche", "brute")).data.materials[0]),
    ("mjf", "MJF PA12 teint noir", "JLC3DP : grain de poudre en relief, teinte uniforme",
     lambda o: PR.poser(o, PR.mjf("nylon_pa12_noir")).data.materials[0]),
    ("acrylique_jour", "Acrylique laser peint — jour", "FS 36118 satinée, lettres jusqu'à la sous-couche",
     lambda o: PR.poser(o, PR.acrylique_laser("peinture_fs36118", charge("lettres_exact.npz"), nom="PROC_acrylique_jour")).data.materials[0]),
    ("acrylique_nuit", "Acrylique laser peint — lettres allumées", "blanc chaud (force_lettres 1,5), studio de jour",
     lambda o: PR.poser(o, PR.acrylique_laser("peinture_fs36118", charge("lettres_exact.npz"), nom="PROC_acrylique_nuit")).data.materials[0]),
    ("alu", "Alu 6061 sablé anodisé", "JLCCNC : usiné, gris foncé",
     lambda o: PR.poser(o, PR.metal("alu_anodise_gris_fonce")).data.materials[0]),
]
pieces = {}
for cle, titre, note, fab in COLONNES:
    o = piece(f"PROC_{cle}"); o.rotation_euler.z = math.radians(-22)
    m = fab(o)
    if cle == "acrylique_nuit": m.node_tree.nodes["force_lettres"].inputs[1].default_value = 1.5
    pieces[cle] = o

CAMS = {"face": ST.camera(col, "CAM_face", (-52, -105, 44), (1.0, 0.0, 11.0), 85, 8.0),
        "tranche": ST.camera(col, "CAM_tranche", (55.9, -63.7, 23.0), (17.4, -4.9, 11.0), 200, 11.0)}   # flanc droit, à 35° de sa normale
tous = list(pieces.values())
imgs = {v: [] for v in CAMS}
for cle, *_ in COLONNES:
    ST.montrer([pieces[cle]], tous)
    for v, cam in CAMS.items():
        imgs[v].append(ST.rendre(sc, cam, os.path.join(SORTIE, f"{cle}_{v}.png")))

# deux lignes de 4 procédés, chacune vue de face puis de la tranche
lignes = []
for k in (0, 4):
    for v, t in (("face", "face (trois quarts)"), ("tranche", "tranche (gros plan rasant)")):
        lignes.append(dict(titre=t, images=imgs[v][k:k + 4],
                           notes=[f"{c[1]}\n{c[2][:70]}" for c in COLONNES[k:k + 4]] if v == "tranche" else None))
g = dict(titre="Une pièce, tous les procédés (studio du site)", colonnes=["", "", "", ""], lignes=lignes,
         pied="Trajets FDM simulés et calés sur OrcaSlicer (impression/tranchage.py), lettres simulées (lettres.py), à confirmer sur une impression "
              "d'essai chez l'imprimeur FDM.")
with open(os.path.join(SORTIE, "grille_quick.json" if ST.QUICK else "grille.json"), "w", encoding="utf-8") as fh:
    json.dump(g, fh, ensure_ascii=False, indent=1)
print("FINI", SORTIE, flush=True)
