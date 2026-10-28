r"""Essai de la méthode de conception (methode/conception_boitier.md) sur un panneau gabarit simple de 5 crans : une fenêtre
d'afficheur, un bouton rond, deux inscriptions éclairées, quatre attaches sur les côtés, deux petites vis traversantes. Il passe
par les étapes 1 à 8 avec les seuls outils de material_library.conception (aucun code propre au F-COM2) et écrit sa fiche de
chiffrage. Scène vide, rien n'est lu ; enregistre un asset d'essai et rend des aperçus (Cycles, peu d'échantillons).
    (lancer via D:\Claude\MFS\outils\blender_garde.ps1)
    blender -b --factory-startup --python D:\Claude\material-library\methode\essai\essai_panneau_gabarit.py -- [sans_rendu]
Sorties : aperçus et journal dans D:\Claude\material-library\methode\essai\ ; asset G:\Blender\Bibliotheque\essais\panneau_gabarit.blend.
Repère des maquettes : x à droite, y vers l'arrière (0 = face avant), z en haut (0 = bas de la façade), mm (1 unité = 1 mm).
"""
import math, os, sys
import bpy, bmesh
from mathutils import Vector

sys.path.insert(0, r"D:\Claude\material-library")
import material_library as SPR
from material_library import aretes as AR
from material_library.conception import panneau as PA, caisson as CA, supports as SU, controles as CT, chiffrage as CH

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ICI = os.path.dirname(os.path.abspath(__file__))
ASSET = os.path.join(SPR.DONNEES, "essais", "panneau_gabarit.blend")
PX = "GAB_"                                   # préfixe de tous les objets de l'essai

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.unit_settings.system = "METRIC"; sc.unit_settings.scale_length = 0.001; sc.unit_settings.length_unit = "MILLIMETERS"
COLL = bpy.data.collections.new("PANNEAU_GABARIT"); sc.collection.children.link(COLL)
RAC = bpy.data.objects.new(PX + "ORIGINE", None); COLL.objects.link(RAC)


def mat(nom, hexa, rough=0.5, metal=0.0, emission=None, force=0.0, trans=0.0, bevel=None):
    """Matière simple d'essai (le catalogue des matières est le chunk-03) ; bevel = rayon du nœud Bevel (aretes.bevel_rendu)."""
    m = bpy.data.materials.new(nom); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    h = hexa.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    b.inputs["Base Color"].default_value = (*c, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Transmission Weight"].default_value = trans
    if emission:
        b.inputs["Emission Color"].default_value = (*emission, 1); b.inputs["Emission Strength"].default_value = force
    return AR.bevel_rendu(m, bevel) if bevel else m


def objet(nom, bm, m, lisse=35.0):
    me = bpy.data.meshes.new(PX + nom); bm.to_mesh(me); bm.free(); me.materials.append(m)
    o = bpy.data.objects.new(PX + nom, me); COLL.objects.link(o); o.parent = RAC
    AR.lisser(o, lisse)
    return o


def cyl(x, z, y0, y1, r, n=32, arr=(0.0, 0.0)):
    return AR.plaque(2 * r, 2 * r, r - 1e-3, y0, y1, arr, cx=x, cz=z, n=n // 4)


def etape(n, titre):
    print(f"\n===== ÉTAPE {n} : {titre}", flush=True)


# ============================================================ 1. références et normes
etape(1, "références et normes")
W, H = PA.taille(5)
for k in ("largeur_nominale", "pas_hauteur", "jeu"):
    print(f"  {k} = {PA.NORMES[k]['valeur']:.3f} ({PA.NORMES[k]['statut']}) — {PA.NORMES[k]['source']}")
print(f"  panneau de 5 crans : {W} × {H} (estimé)")

# ============================================================ 2. taille et architecture : dessin à plat, empilage
etape(2, "taille et architecture")
E = PA.EMPILAGE
T_PL, T_EMB = E["plaque"], E["embase"]; T = T_PL + T_EMB          # dos de la façade
Y_PCB = round(T + E["boite_lumiere"], 3); E_PCB = E["carte"]       # face avant de la carte
X_ATT = W / 2 - 6.5
p = PA.Panneau(
    "gabarit", W, H,
    ouvertures=[dict(nom="fenetre", x=-30.0, z=24.0, l=50.0, h=14.0, r=1.2), dict(nom="bouton", x=40.0, z=22.0, l=8.8, h=8.8, r=4.4)],
    inscriptions=[dict(texte="GABARIT", x=-30.0, z=37.5, cap=4.5), dict(texte="TEST", x=40.0, z=33.0, cap=4.0)],
    attaches=[(sx * X_ATT, H / 2 + sz * PA.NORMES["entraxe_attaches_z"]["valeur"] / 2) for sz in (-1, 1) for sx in (-1, 1)],
    vis=[(0.0, 8.0), (10.0, 40.0)])
print(f"  empilage (y) : plaque 0 → {T_PL}, embase → {T}, boîte à lumière → {Y_PCB}, carte → {Y_PCB + E_PCB}, caisson de 30")

# ============================================================ 3. matériaux et lieu de fabrication (chiffrage à l'étape 9)
etape(3, "matériaux et lieu de fabrication")
M_FAC = mat("acrylique_peint_gris", "#3b3f45", 0.4, bevel=AR.RAYONS["acrylique"])    # base compensée à la pipette (F-COM2)
M_LET = mat("lettres_blanches", "#e4dfdf", 0.6, emission=(1.0, 0.75, 0.45), force=0.0)
M_PLA = mat("pla_noir_imprimeur", "#18181a", 0.45, bevel=AR.RAYONS["pla"])
M_SLA = mat("sla_jlc_black", "#141416", 0.5, bevel=AR.RAYONS["resine"])
M_PCB = mat("vernis_pcb", "#3a8c5d", 0.32)
M_INOX = mat("inox", "#c8c8c6", 0.3, metal=1.0, bevel=AR.RAYONS["vis"])
M_NOIR = mat("acier_noir", "#2a2a2c", 0.45, metal=1.0, bevel=AR.RAYONS["vis"])
M_LAITON = mat("laiton", "#b5a26a", 0.35, metal=1.0)
M_VITRE = mat("acrylique_fume", "#3a3836", 0.03, trans=1.0)
M_AFF = mat("afficheur", "#0c0c0c", 0.4, emission=(1.0, 0.52, 0.0), force=0.0)
M_SEG = mat("segments", "#202020", 0.4, emission=(1.0, 0.52, 0.0), force=6.0)
M_LED = mat("led", "#ffffff", 0.3, emission=(1.0, 0.7, 0.3), force=0.0)
M_PATIN = mat("patin_3m", "#101010", 0.8)
print("  plaque acrylique « jour / nuit » (atelier laser) ; embase, boîte à lumière, collerettes, bouton : PLA chez l'imprimeur FDM ;\n"
      "  caisson et supports : SLA JLC Black ; inserts posés par JLC ; visserie du commerce")

# ============================================================ 4. fixations (contrôle du dessin à plat d'abord)
etape(4, "fixations")
erreurs, remarques = PA.verifier(p)
if erreurs: raise SystemExit("dessin à corriger avant la 3D")
ch = PA.chambres(p); jours = PA.jours_embase(ch)

# --- façade : plaque (lettres) et embase
plaque = objet("PLAQUE", AR.plaque(W - 0.6, H - 0.6, 1.0, 0.0, T_PL, (0.6, 0.2), cz=H / 2), M_FAC)
outils = [AR.coupe(AR.contour_rrect(o["l"], o["h"], o["r"]), -1.0, T_PL + 1, conge=0.6, cx=o["x"], cz=o["z"]) for o in p.ouvertures]
outils += [AR.coupe(AR.encoche_u(p.r_trou_attache, W / 2 - 0.3 - abs(x), math.copysign(1, x)), -1.0, T_PL + 1, conge=0.6, cx=x, cz=z)
           if W / 2 - 0.3 - abs(x) - p.r_trou_attache < PA.REGLES["bord_min"] else
           AR.coupe(AR.contour_cercle(p.r_trou_attache), -1.0, T_PL + 1, conge=0.6, cx=x, cz=z) for x, z in p.attaches]
outils += [AR.coupe(AR.contour_cercle(1.7), -1.0, T_PL + 1, chanf=1.15, cx=x, cz=z) for x, z in p.vis]     # fraisage 90° M3
AR.retrancher(plaque, outils)
embase = objet("EMBASE", AR.plaque(W, H, 1.2, T_PL, T, (0.35, 0.3), cz=H / 2), M_PLA)
fen = p.ouvertures[0]; bou = p.ouvertures[1]
AR.retrancher(embase, [AR.coupe(AR.contour_rrect(fen["l"] - 4, fen["h"] - 4, 1.0), T_PL - 1, T + 1, cx=fen["x"], cz=fen["z"]),
                       cyl(bou["x"], bou["z"], T_PL - 1, T + 1, bou["l"] / 2)]
               + [cyl(x, z, T_PL - 1, T + 1, 2.2) for x, z in p.attaches] + [cyl(x, z, T_PL - 1, T + 1, 1.7) for x, z in p.vis])
# lettres gravées (blanc rétroéclairé), à fleur de la face avant
POL = bpy.data.fonts.load(r"C:\Windows\Fonts\arialbd.ttf")
for i in p.inscriptions:
    cu = bpy.data.curves.new("txt", "FONT"); cu.body = i["texte"]; cu.font = POL; cu.size = i["cap"] / 0.716
    cu.align_x = "CENTER"; cu.align_y = "CENTER"; cu.extrude = 0.02
    t = bpy.data.objects.new("txt", cu); COLL.objects.link(t); t.rotation_euler = (math.radians(90), 0, 0)
    t.location = (i["x"], -0.005, i["z"]); bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(t.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    me.transform(t.matrix_world); bpy.data.objects.remove(t)
    me.materials.append(M_LET); o = bpy.data.objects.new(PX + "LETTRES_" + i["texte"], me); COLL.objects.link(o); o.parent = RAC

# --- caisson : colonnes d'insert aux attaches (rayon borné), inserts au dos, rainures du clipsage
x_boite = None
rc, autour, _ = CA.rayon_colonne(X_ATT, W - 2 * CA.REGLES["retrait"])
x_boite = X_ATT - rc - CA.REGLES["jeu_obstacle"]                    # la boîte à lumière s'arrête avant les colonnes
print(f"  colonnes : R {rc:.2f}, {autour:.2f} de matière autour de l'insert M4 ; boîte à lumière jusqu'à x ± {x_boite:.2f}")
INS_DOS = [(sx * 40.0, H / 2 + sz * 12.0) for sz in (-1, 1) for sx in (-1, 1)]
cai, D, _ = CA.construire(COLL, RAC, PX, p, 30.0, T, M_SLA, inserts_dos=INS_DOS, y_butee=17.5)
for k, (x, z) in enumerate(p.attaches):              # inserts M4 posés par JLC, face contre la façade
    ins = CA.INSERTS["M4"]; bm = cyl(x, z, T + 0.05, T + ins["l"], ins["d"] / 2)
    o = objet(f"INSERT_M4_{k}", bm, M_LAITON); AR.retrancher(o, [cyl(x, z, T - 1, T + ins["l"] + 1, 1.95)])

# --- attaches : collerette PLA (Ø 9,5, fond 0,8 percé Ø 4,4) posée sur l'embase, sommet à fleur ; M4 × 8 DIN 84 inox
for k, (x, z) in enumerate(p.attaches):
    c = objet(f"COLLERETTE_{k}", cyl(x, z, 0.0, T_PL, 4.75, 48, (0.4, 0.0)), M_PLA)
    AR.retrancher(c, [cyl(x, z, -1.0, T_PL - 0.8, 3.75, 48), cyl(x, z, -1.0, T_PL + 1, 2.2, 32)])
    tete = objet(f"VIS_ATT_{k}", cyl(x, z, T_PL - 0.8 - 2.6, T_PL - 0.8, 3.5, 48, (0.3, 0.0)), M_INOX)
    AR.retrancher(tete, [AR.plaque(8.0, 1.2, 0.05, -2.0, T_PL - 0.8 - 1.5, (0.0, 0.0), cx=x, cz=z, n=2)])
    objet(f"VIS_ATT_{k}_tige", cyl(x, z, T_PL - 0.8, T_PL - 0.8 + 8.0, 1.95, 24), M_INOX)

# --- petites vis M3 fraisées traversantes (façade + embase + boîte à lumière + carte), écrou au dos de la carte
for k, (x, z) in enumerate(p.vis):
    bm = bmesh.new(); anneaux = []
    for y, r in ((0.0, 2.75), (1.65 - 0.4, 1.5), (Y_PCB + E_PCB + 2.6, 1.5)):
        anneaux.append([Vector((x + r * math.cos(2 * math.pi * i / 32), y, z + r * math.sin(2 * math.pi * i / 32))) for i in range(32)])
    AR.loft(bm, anneaux); objet(f"VIS_PL_{k}", bm, M_NOIR)
    e = objet(f"ECROU_PL_{k}", cyl(x, z, Y_PCB + E_PCB, Y_PCB + E_PCB + 2.4, 3.1, 6, (0.2, 0.2)), M_INOX)
    AR.retrancher(e, [cyl(x, z, Y_PCB, Y_PCB + E_PCB + 3.5, 1.55, 24)])

# ============================================================ 5. lumière : chambres, jours dans l'embase, LED derrière chaque inscription
etape(5, "lumière")
boite = objet("BOITE_LUMIERE", AR.plaque(2 * x_boite, H - 2 * 3.3, 1.5, T + 0.02, Y_PCB, (0.3, 0.3), cz=H / 2), M_PLA)
AR.retrancher(boite, [AR.plaque(fen["l"] + 2, fen["h"] + 2, 1.0, T - 1, Y_PCB + 1, (0, 0), cx=fen["x"], cz=fen["z"]),
                      cyl(bou["x"], bou["z"], T - 1, Y_PCB + 1, 6.2)]
              + [AR.plaque(c["l"], c["h"], 0.8, T - 1, Y_PCB + 1, (0, 0), cx=c["x"], cz=c["z"]) for c in ch]
              + [cyl(x, z, T - 1, Y_PCB + 1, 1.7) for x, z in p.vis])
axes_lumiere = [(c["x"], c["z"]) for c in ch]
print("  sans jours dans l'embase (piège du F-COM2) :")
sans_jours = CT.trous(axes_lumiere, [PX + "EMBASE", PX + "BOITE_LUMIERE"])
AR.retrancher(embase, [AR.plaque(j["l"], j["h"], 0.8, T_PL - 1, T + 1, (0, 0), cx=j["x"], cz=j["z"]) for j in jours])
print("  avec les jours :")
avec_jours = CT.trous(axes_lumiere, [PX + "EMBASE", PX + "BOITE_LUMIERE"])
carte = objet("PCB", AR.plaque(2 * x_boite - 4, H - 2 * 4.5, 2.0, Y_PCB, Y_PCB + E_PCB, (0.1, 0.1), cz=H / 2), M_PCB)
AR.retrancher(carte, [cyl(x, z, Y_PCB - 1, Y_PCB + E_PCB + 1, 1.7) for x, z in p.vis])
for k, (x, z) in enumerate(axes_lumiere):
    objet(f"LED_{k}", AR.plaque(3.2, 1.6, 0.2, Y_PCB - 0.8, Y_PCB, (0.1, 0.0), cx=x, cz=z, n=2), M_LED)
aff = objet("AFFICHEUR", AR.plaque(fen["l"], fen["h"], 0.5, T + 1.1, Y_PCB, (0.2, 0.0), cx=fen["x"], cz=fen["z"]), M_AFF)
objet("VITRE", AR.plaque(fen["l"] - 0.3, fen["h"] - 0.3, 1.05, 1.0, T_PL - 0.01, (0.1, 0.1), cx=fen["x"], cz=fen["z"]), M_VITRE, 0)
cu = bpy.data.curves.new("seg", "FONT"); cu.body = "118.705"; cu.font = POL; cu.size = 9.0; cu.align_x = "CENTER"; cu.align_y = "CENTER"
t = bpy.data.objects.new("seg", cu); COLL.objects.link(t); t.rotation_euler = (math.radians(90), 0, 0); t.location = (fen["x"], T + 1.09, fen["z"])
bpy.context.view_layer.update(); me = bpy.data.meshes.new_from_object(t.evaluated_get(bpy.context.evaluated_depsgraph_get()))
me.transform(t.matrix_world); bpy.data.objects.remove(t); me.materials.append(M_SEG)
o = bpy.data.objects.new(PX + "SEGMENTS", me); COLL.objects.link(o); o.parent = RAC
# bouton : capuchon Ø 8, collerette derrière l'embase (recul 0,6 avant butée), tige jusqu'à 0,2 du bouton tactile
btn = objet("BOUTON", cyl(bou["x"], bou["z"], -2.0, T, 4.0, 48, (0.8, 0.0)), M_PLA)
AR.retrancher(btn, [cyl(bou["x"], bou["z"], T - 0.01, T + 1.0, 5.6, 48), cyl(bou["x"], bou["z"], T + 0.9, Y_PCB - 4.5 - 0.2, 2.0)], op="UNION")
objet("PCB_SW", AR.plaque(6.0, 6.0, 0.3, Y_PCB - 4.5, Y_PCB, (0.2, 0.0), cx=bou["x"], cz=bou["z"], n=2), M_NOIR)

# ============================================================ 6. supports et pose
etape(6, "supports et pose")
sups, patins, pose = SU.construire(COLL, RAC, PX, D["largeur"], D["z0"], T, D["y1"], D["y_butee"], M_SLA, M_PATIN)
print(f"  supports clipsés {len(sups)}, patins {len(patins)}, pose inclinée de {SU.POSE['INCL']}°")

# ============================================================ 7. contrôles automatiques
etape(7, "contrôles automatiques")
bilan = {}
bilan["trous"] = CT.trous(p.vis, [PX + n for n in ("PLAQUE", "EMBASE", "BOITE_LUMIERE", "PCB")])
bilan["trous_attaches"] = CT.trous(p.attaches, [PX + "EMBASE"])
bilan["lumiere"] = avec_jours
bilan["collisions"], contacts = CT.collisions(
    prefixes=[PX + n for n in ("PLAQUE", "EMBASE", "CAISSON", "BOITE_LUMIERE", "PCB", "LED_", "AFFICHEUR", "VITRE", "BOUTON",
                                "COLLERETTE_", "VIS_", "ECROU_", "INSERT_", "SUPPORT_", "PATIN_")],
    voulus=[(PX + "CAISSON", PX + "INSERT_"), (PX + "SUPPORT_", PX + "PATIN_"), (PX + "PCB", PX + "LED_"), (PX + "PCB", PX + "PCB_SW")],
    meme_piece=lambda a, b: a.split("_tige")[0] == b.split("_tige")[0])
bilan["parois_boite"] = CT.parois([PX + "BOITE_LUMIERE"], PA.REGLES["mur_min"])
bilan["parois_collerettes"] = CT.parois([], 0.8, prefixes=[PX + "COLLERETTE_"])
bilan["parois_caisson"] = CT.parois([PX + "CAISSON"], 1.0)
bilan["aretes_vives"] = {n: len(AR.aretes_vives(bpy.data.objects[PX + n])) for n in ("PLAQUE", "CAISSON", "BOITE_LUMIERE")}
print(f"  arêtes de plus de 45° (avant le nœud Bevel du rendu) : {bilan['aretes_vives']}")

# ============================================================ 9. chiffrage (avant le rendu : il sert à la revue)
etape(9, "revue de faisabilité et chiffrage")
v = {n: CT.volume_cm3(PX + n) for n in ("CAISSON", "SUPPORT_G", "BOITE_LUMIERE", "EMBASE")}
for n, x in v.items(): print(f"  volume {n} : {x:.1f} cm³")
lignes = [
    ("Caisson SLA JLC Black", True, CH.sla_jlc(v["CAISSON"]), f"{v['CAISSON']:.1f} cm³, poncé + huilé"),
    ("2 supports SLA JLC Black", True, 2 * CH.sla_jlc(v["SUPPORT_G"]), "clipsés, pose à 15°"),
    ("8 inserts posés par JLC", "dos : oui", CH.inserts_jlc(4 + len(INS_DOS)), "4 M4 (attaches) + 4 M3 (pupitre)"),
    ("Embase + boîte à lumière + collerettes + bouton, PLA chez l'imprimeur FDM", "embase : oui",
     CH.pla_imprimeur(v["EMBASE"] + v["BOITE_LUMIERE"] + 2.0), "pièces cachées : le moins cher"),
    ("Plaque acrylique « jour / nuit »", True, (3.0, 15.0), "⚠ prix inconnu : échantillon obligatoire"),
    ("Visserie (4 M4 × 8 DIN 84 inox, 2 M3 fraisées + écrous)", True, (0.8, 1.5), "au détail"),
    ("Port JLC des pièces SLA", False, CH.port_jlc((v["CAISSON"] + 2 * v["SUPPORT_G"]) * CH.PRIX["sla_densite"]),
     "au poids ; une commande groupée par série ⚠"),
]
TAB = CH.tableau(lignes)
print(TAB)

# ============================================================ 8. rendu : asset, aperçus
etape(8, "rendu : asset → aperçus")
for o in COLL.objects:
    if o.name.startswith("_outil"): bpy.data.objects.remove(o)
RAC.rotation_euler = pose["rotation"]; RAC.location = pose["location"]; bpy.context.view_layer.update()
zmin = min((o.matrix_world @ v.co).z for o in COLL.objects if o.type == "MESH" for v in o.data.vertices)   # bound_box : périmé
print(f"  posé : point le plus bas à z = {zmin:.2f} (patins sur le bureau attendus à 0)")
os.makedirs(os.path.dirname(ASSET), exist_ok=True)
# studio d'essai neutre (le vrai studio est un asset du projet, lié dans ses plans fixes)
sol = bpy.data.meshes.new("sol"); bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=600); bm.to_mesh(sol); bm.free()
sol.materials.append(mat("sol_gris", "#8a8c8e", 0.6)); so = bpy.data.objects.new("STUDIO_sol", sol); sc.collection.objects.link(so)
w = bpy.data.worlds.new("monde"); w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.5, 0.52, 0.55, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.35; sc.world = w
for nom, rot, f, ang in (("cle", (50, 0, 35), 3.2, 12), ("contre", (60, 0, 200), 1.5, 25), ("bouche", (75, 0, -60), 0.8, 40)):
    li = bpy.data.lights.new(nom, "SUN"); li.energy = f; li.angle = math.radians(ang)
    lo = bpy.data.objects.new("STUDIO_" + nom, li); lo.rotation_euler = [math.radians(a) for a in rot]; sc.collection.objects.link(lo)
bpy.ops.wm.save_as_mainfile(filepath=ASSET)
print(f"  asset d'essai : {ASSET}")


def camera(nom, loc, cible, lens):
    cd = bpy.data.cameras.new(nom); cd.lens = lens; cd.clip_start = 5; cd.clip_end = 5000
    c = bpy.data.objects.new(nom, cd); sc.collection.objects.link(c); c.location = loc
    c.rotation_euler = (Vector(cible) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return c


if "sans_rendu" not in argv:
    sc.render.engine = "CYCLES"; sc.cycles.samples = 48; sc.cycles.use_denoising = True
    try:                                       # carte graphique si elle est là (--factory-startup : CPU par défaut)
        cp = bpy.context.preferences.addons["cycles"].preferences
        for t in ("OPTIX", "CUDA", "HIP", "ONEAPI"):
            try:
                cp.compute_device_type = t; cp.get_devices()
                if any(d.type == t for d in cp.devices): break
            except TypeError:
                continue
        for d in cp.devices: d.use = d.type != "CPU"
        sc.cycles.device = "GPU"
    except Exception as e:
        print("  rendu sur CPU :", e)
    sc.render.resolution_x, sc.render.resolution_y = 1400, 900
    sc.view_settings.view_transform = "AgX"
    sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 90     # aperçus légers, dans git
    centre = (0.0, 20.0, 25.0)
    for nom, loc, lens, nuit in (("apercu_hero", (-240, -340, 175), 60, False), ("apercu_face", (0, -420, 30), 90, False),
                                 ("apercu_dos", (250, 330, 170), 60, False), ("apercu_nuit", (-240, -340, 175), 60, True)):
        sc.camera = camera(nom, loc, centre, lens)
        M_LED.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 400.0 if nuit else 0.0
        M_LET.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 1.5 if nuit else 0.0
        w.node_tree.nodes["Background"].inputs[1].default_value = 0.02 if nuit else 0.35
        for lo in [o for o in sc.objects if o.type == "LIGHT"]: lo.data.energy *= (0.03 if nuit else 1.0)
        sc.render.filepath = os.path.join(ICI, nom + ".jpg"); bpy.ops.render.render(write_still=True)
        for lo in [o for o in sc.objects if o.type == "LIGHT"]: lo.data.energy /= (0.03 if nuit else 1.0)
        print(f"  aperçu {nom}.jpg", flush=True)

# ============================================================ bilan
print("\n===== BILAN DE L'ESSAI", flush=True)
print(f"  dessin : {len(erreurs)} erreur(s), {len(remarques)} remarque(s) ; trous bouchés : {len(bilan['trous'])} (vis), "
      f"{len(bilan['trous_attaches'])} (attaches) ; lumière : {len(sans_jours)} bouchée(s) sans jours → {len(avec_jours)} avec ; "
      f"collisions : {len(bilan['collisions'])} ({len(contacts)} contacts voulus) ; parois minces : boîte {len(bilan['parois_boite'])}, "
      f"collerettes {len(bilan['parois_collerettes'])}, caisson {len(bilan['parois_caisson'])}", flush=True)
with open(os.path.join(ICI, "chiffrage_gabarit.md"), "w", encoding="utf-8") as f:
    f.write("# Chiffrage du panneau gabarit (généré par essai_panneau_gabarit.py)\n\n" + TAB + "\n")
