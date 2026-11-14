r"""Planche du chunk-08 de fdm-trajets : la face d'une pièce FDM sortie d'un plateau lisse, couche par couche (référence :
<DONNEES>\fdm\references\6.webp). Une plaque d'essai en PLA noir (60 × 36 × 3, deux trous) passe par material_library.rendu ;
chaque ligne de la planche n'allume qu'une couche du look (nœuds `couche_<nom>`), la dernière les allume toutes ; deux vues :
« reflet » (face inclinée, une boîte à lumière dans l'axe miroir de la caméra, comme le plafonnier de la photo) et « gros plan »
dans ce même reflet.
    blender -b <rendu.STUDIO> --python outils\planches\planche_plateau_lisse.py -- [quick]
puis : python outils\planches\assembler.py <sortie>\grille.json <sortie>\planche_plateau_lisse.png
(lancer via le garde-fou mémoire ; MATERIAL_LIBRARY_PYTHON = Python avec numpy et shapely)"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import material_library as SP                                          # noqa: E402
from material_library import aretes as AR, rendu as RD                 # noqa: E402

QUICK = "quick" in sys.argv
SORTIE = os.path.join(SP.DONNEES, "planches", "plateau_lisse"); os.makedirs(SORTIE, exist_ok=True)
sc = RD.studio(32 if QUICK else 96, (900, 700))

# plaque d'essai : face avant (y = 0) posée sur le plateau, 60 × 36 × 3, coins R 2, un trou Ø 6 et un trou Ø 3,4
W, H, E = 60.0, 36.0, 3.0
bm = AR.plaque(W, H, 2.0, 0.0, E, (0.4, 0.4), cz=H / 2)
me = bpy.data.meshes.new("PL_PLAQUE"); bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new("PL_PLAQUE", me); sc.collection.objects.link(ob)
AR.retrancher(ob, [AR.coupe(AR.contour_cercle(3.0, 64), -1.0, E + 1.0, chanf=0.4, cx=14.0, cz=12.0),
                   AR.coupe(AR.contour_cercle(1.7, 48), -1.0, E + 1.0, chanf=0.3, cx=-16.0, cz=24.0)])
pivot = bpy.data.objects.new("PL_PIVOT", None); sc.collection.objects.link(pivot); ob.parent = pivot
RD.piece_fdm(ob, "pla_noir", plateau="-Y", res=1024, res_premier_lit=2048,
             dossier=os.path.join(SP.DONNEES, "fdm", "planche_plateau_lisse"))
objets = [o for o in sc.collection.objects if o.name.startswith("PL_PLAQUE")]

COUCHES = ["ondulation", "plaques", "lignes", "sillons", "poussiere"]
TITRES = {"base": "Base : matière seule (PLA noir, micro-rugosité du plateau lisse)", "ondulation": "1 · planéité (ondulation)",
          "plaques": "2 · brillance par zones", "lignes": "3 · brillance par ligne et par bande",
          "sillons": "3-4 · relief des cordons (sillons)", "poussiere": "10 · poussière fine", "toutes": "Toutes les couches"}


def allumer(actives):
    for o in objets:
        for s_ in o.material_slots:
            if not s_.material: continue
            for n in s_.material.node_tree.nodes:
                if n.name.startswith("couche_"):
                    n.outputs[0].default_value = 1.0 if n.name[len("couche_"):] in actives else 0.0


# ces couches se lisent dans un REFLET (photo : le plafonnier) : une boîte à lumière placée dans l'axe miroir de la caméra par
# rapport à la face, comme le zébra du banc de la R-Box ; la face est inclinée de INCL, le point visé est sur une zone sans trou
INCL = -55.0
R = Matrix.Rotation(math.radians(INCL), 4, "X")
CIBLE = R @ Vector((-6.0, 0.0, 12.0)); NORMALE = (R.to_3x3() @ Vector((0.0, -1.0, 0.0))).normalized()
lum = bpy.data.lights.new("PL_REFLET", "AREA"); lum.shape = "RECTANGLE"; lum.size, lum.size_y = 140.0, 90.0; lum.energy = 60000.0
lampe = bpy.data.objects.new("PL_REFLET", lum); sc.collection.objects.link(lampe)
cam = RD.camera("PL_CAM", (0, -150, 100), (0, 0, H / 2), 60)
def vue(distance, focale):
    """Caméra à `distance` de CIBLE, de trois quarts, et lampe dans son axe miroir (le reflet tombe sur CIBLE)."""
    d = Vector((0.18, -0.55, 0.82)).normalized()
    loc = CIBLE + d * distance; r = 2 * d.dot(NORMALE) * NORMALE - d
    lampe.location = CIBLE + r * 260.0; lampe.rotation_euler = (-r).to_track_quat("-Z", "Y").to_euler()
    return tuple(loc), tuple(CIBLE), focale
VUES = [("reflet", *vue(170.0, 50)), ("gros_plan", *vue(45.0, 100))]
lignes = []
for cle in ["base"] + COUCHES + ["toutes"]:
    allumer(COUCHES if cle == "toutes" else ([] if cle == "base" else [cle]))
    images = []
    for nom, loc, cible, focale in VUES:
        pivot.rotation_euler = (math.radians(INCL), 0.0, 0.0); bpy.context.view_layer.update()
        vue(170.0 if nom == "reflet" else 45.0, focale)                       # replace la lampe pour cette vue
        cam.data.lens = focale; RD.viser(cam, loc, cible, 11.0)
        images.append(RD.rendre(os.path.join(SORTIE, f"{cle}_{nom}{'_quick' if QUICK else ''}.png")))
    lignes.append(dict(titre=TITRES[cle], images=images, notes=[None, None]))
g = dict(titre="Face sortie d'un plateau lisse — couches du look (référence : fdm/references/6.webp)",
         colonnes=["reflet d'une boîte à lumière (comme la photo)", "gros plan dans le reflet"], lignes=lignes,
         pied="material_library.rendu.piece_fdm ; nœuds couche_* de procedes.plateau_texture / trajets et imperfections (poussière).")
with open(os.path.join(SORTIE, "grille_quick.json" if QUICK else "grille.json"), "w", encoding="utf-8") as f:
    json.dump(g, f, ensure_ascii=False, indent=1)
print("FINI", SORTIE, flush=True)
