r"""Planche de visserie (chunk-05) : chaque norme en M3 / M4, inox A2 et acier oxydé noir, couchée sur le bureau du studio du site,
gros plan de trois quarts ; puis écrous + rondelles, inserts laiton, et les deux fixations de façade (attache M4 DIN 84 en
collerette dans une encoche en U, petite vis M3 ISO 7046 à fleur) sur une plaque peinte.
    blender -b G:\Blender\MFS\plans_fixes\site\hero.blend --python outils\planches\planche_visserie.py -- [quick]
puis : python outils\planches\assembler.py <sortie>\grille.json <sortie>\planche_visserie.png"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import studio as ST                                   # noqa: E402
import bpy                                            # noqa: E402
from mathutils import Matrix, Vector                  # noqa: E402
from material_library import aretes as AR               # noqa: E402
from material_library.visserie import fixations as FX, normes as N, pieces as PC, shading as SH   # noqa: E402

sc, col, SORTIE = ST.preparer("visserie", res=(1200, 900))
COLONNES = [(3, "inox"), (3, "oxyde"), (4, "inox"), (4, "oxyde")]
VIS = [("DIN 84", 8, "DIN 84 — cylindrique fendue"), ("ISO 7045", 8, "ISO 7045 — bombée cruciforme"),
       ("ISO 7046", 10, "ISO 7046 / DIN 965 — fraisée 90° cruciforme"), ("ISO 4762", 8, "ISO 4762 — six pans creux")]
NOM_MAT = {"inox": "inox A2", "oxyde": "acier oxydé noir"}


def poser(objs, M):
    """Applique la transformation M (monde) à des objets créés à l'origine."""
    for o in objs: o.matrix_world = M @ o.matrix_world
    return objs


def couchee(objs, r_tete, d, longueur, k, azimut=18.0):
    """Vis couchée sur le bureau (z = 0) : axe dans le plan horizontal tourné de `azimut` (tête vers -y, vue de trois quarts par
    les caméras de cadrer()), appuyée sur le bord de la tête et la crête du filet (axe incliné)."""
    a = math.atan2(r_tete - d / 2, longueur + k / 2)
    M = Matrix.Translation((0, 0, r_tete)) @ Matrix.Rotation(math.radians(azimut), 4, "Z") @ Matrix.Rotation(-a, 4, "X")
    return poser(objs, M)


def cadrer(nom, objs, lens=100.0, marge=1.35, direction=(-0.55, -0.72, 0.42), fstop=16.0):
    """Caméra de gros plan sur la boîte englobante des objets."""
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    c = (lo + hi) / 2; diag = (hi - lo).length
    dist = diag * marge / (36.0 / lens)
    return ST.camera(col, nom, c + Vector(direction).normalized() * dist, c, lens, fstop)


cellules = []                                          # (ligne, colonne, objets, caméra, note)
for i, (nm, l, titre) in enumerate(VIS):
    for j, (d, mat) in enumerate(COLONNES):
        c = N.cotes(nm, d)
        objs = PC.vis(f"M{d} x {l} {nm} {mat}", a=25.0, col=col, prefixe=f"PL_VIS_{i}_{j}")
        k = 0.0 if c["forme"] == "fraisee_cruciforme" else c["k"]
        couchee(objs, c["dk"] / 2, d, l, k)
        note = f"M{d} × {l}, tête Ø {c['dk']:g} × {c['k']:g}".replace(".", ",")
        cellules.append((i, j, objs, cadrer(f"CAM_{i}_{j}", objs), note))

# écrou ISO 4032 sur rondelle DIN 125, à plat
i = len(VIS)
for j, (d, mat) in enumerate(COLONNES):
    h = N.DIN_125[d]["h"]
    objs = PC.rondelle(f"M{d} DIN 125 {mat}", col=col, prefixe=f"PL_RONDELLE_{j}")
    objs += PC.ecrou(f"M{d} ISO 4032 {mat}", y_av=h, col=col, prefixe=f"PL_ECROU_{j}")
    poser(objs, Matrix.Rotation(math.radians(90), 4, "X") @ Matrix.Rotation(math.radians(12 * j), 4, "Y"))
    c = N.ISO_4032[d]
    cellules.append((i, j, objs, cadrer(f"CAM_E_{j}", objs, direction=(-0.5, -0.7, 0.75)),
                     f"écrou M{d} sur plats {c['s']:g} × {c['m']:g} ; rondelle Ø {N.DIN_125[d]['d2']:g}".replace(".", ",")))

# gros plans : inserts laiton M3 / M4, attache en collerette, vis à fleur
i += 1
ins = []
for k_, d in enumerate((3, 4)):
    L = N.INSERT_LAITON[d]["l"]
    o = PC.insert(f"M{d} INSERT laiton", x=7.0 * k_, y_face=L, col=col, prefixe=f"PL_INSERT_{d}")
    ins += poser(o, Matrix.Rotation(math.radians(90), 4, "X"))
cellules.append((i, 0, ins, cadrer("CAM_INSERTS", ins, direction=(-0.5, -0.7, 0.8)), "inserts laiton ruthex M3 × 5,7, M4 × 8,1"))

W, H, TL = 30.0, 22.0, 3.0                              # plaque peinte dressée, face avant en y = 0, bas en z = 0
peinture = bpy.data.materials.new("PL_peinture_satinee"); peinture.use_nodes = True
b = peinture.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = SH.srgb("#3b3f45"); b.inputs["Roughness"].default_value = 0.4
AR.bevel_rendu(peinture, 0.4)
pla = bpy.data.materials.new("PL_PLA_noir"); pla.use_nodes = True
b = pla.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = SH.srgb("#18181a"); b.inputs["Roughness"].default_value = 0.55
AR.bevel_rendu(pla, 0.3)
XA, ZA, XF, ZF = W / 2 - 4.6, H / 2, -5.0, H / 2 - 3.0        # attache près du bord droit (encoche en U), vis à fleur à gauche
bm = AR.plaque(W, H, 2.0, 0.0, TL, (0.4, 0.4), cz=H / 2)
me = bpy.data.meshes.new("PL_PLAQUE"); bm.to_mesh(me); bm.free(); me.materials.append(peinture)
plaque = bpy.data.objects.new("PL_PLAQUE", me); col.objects.link(plaque)
AR.retrancher(plaque, [FX.trou_attache(XA, ZA, -1.0, TL + 0.5, bord=W / 2), FX.fraisage(XF, ZF, 0.0)])
coll = PC.objet("PL_COLLERETTE", FX.collerette(XA, ZA, TL, TL), pla, col, lisse=40)
fac = [plaque, coll] + PC.vis("M4 x 8 DIN 84 inox", XA, ZA, TL - FX.ATTACHE["coll_fond"], a=28.0, col=col, prefixe="PL_ATTACHE")
fac += PC.vis("M3 x 10 ISO 7046 oxyde", XF, ZF, 0.0, a=45.0, col=col, prefixe="PL_FLEUR")
poser(fac, Matrix.Rotation(math.radians(-18), 4, "Z"))
cam_fac = ST.camera(col, "CAM_FACADE", (-38, -70, 34), (1.0, 0.0, 11.0), 85, 11.0)
cellules.append((i, 1, fac, cam_fac, "attache M4 en collerette, M3 à fleur"))
bpy.context.view_layer.update()


def gros_plan(nom, x, z, direction, dist):
    cible = plaque.matrix_world @ Vector((x, 0.0, z))
    return ST.camera(col, nom, cible + Vector(direction).normalized() * dist, cible, 135, 16.0)


cellules.append((i, 2, fac, gros_plan("CAM_GP_ATTACHE", XA, ZA, (-0.45, -1.0, 0.55), 42.0),
                 "attache : congé 0,6, entrée du U R 1"))
cellules.append((i, 3, fac, gros_plan("CAM_GP_FLEUR", XF, ZF, (-0.4, -1.0, 0.45), 32.0),
                 "M3 oxydée à fleur, fraisage R 0,25"))

# contrôle par mesure : arêtes vives (> 60°) des têtes après biseau
for o in col.objects:
    if o.type == "MESH" and o.name.startswith(("PL_VIS_", "PL_ATTACHE", "PL_FLEUR")) and not o.name.endswith(("_filet", "_ame")):
        print(f"CONTROLE {o.name} : {len(AR.aretes_vives(o, 60.0))} arêtes > 60°", flush=True)

tous = [o for o in col.objects if o.type == "MESH"]
lignes = [dict(titre=t, images=[None] * 4, notes=[None] * 4) for _, _, t in VIS]
lignes += [dict(titre="Écrou ISO 4032 sur rondelle DIN 125", images=[None] * 4, notes=[None] * 4),
           dict(titre="Inserts et fixations de façade", images=[None] * 4, notes=[None] * 4)]
for i, j, objs, cam, note in cellules:
    ST.montrer(objs, tous)
    lignes[i]["images"][j] = ST.rendre(sc, cam, os.path.join(SORTIE, f"l{i}_c{j}.png"))
    lignes[i]["notes"][j] = note

g = dict(titre="Visserie du commerce — M3 / M4, inox A2 et acier oxydé noir (studio du site)",
         colonnes=[f"M{d} {NOM_MAT[m]}" for d, m in COLONNES], lignes=lignes,
         pied="Géométrie : material_library.visserie (normes.py, fixations.py, filets.py) ; matières : shading.py (Bevel R 0,2, "
              "imperfections sur UV en mm). Dernière ligne : inserts, plaque de façade, gros plans.")
with open(os.path.join(SORTIE, "grille_quick.json" if ST.QUICK else "grille.json"), "w", encoding="utf-8") as f:
    json.dump(g, f, ensure_ascii=False, indent=1)
print("FINI", SORTIE, flush=True)
