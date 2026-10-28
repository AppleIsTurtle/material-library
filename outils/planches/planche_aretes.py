r"""Planche d'arêtes (chunk-02) : la même pièce — plaque 40 × 26 × 3 dressée, fenêtre, trou rond, encoche ouverte sur le bord —
avec des arêtes de 0 / 0,2 / 0,4 / 0,6 mm, obtenues
  - par la GÉOMÉTRIE : plaque(arr = r) et coupe(congé = r) ;
  - par le RENDU : géométrie vive + nœud Bevel de r (bevel_rendu) ;
vue de trois quarts et gros plan du coin de la fenêtre. Peinture satinée grise sans grain (base de la peinture FS 36118 de la
réplique), pour que seuls les reflets des arêtes changent.
    blender -b G:\Blender\MFS\plans_fixes\site\hero.blend --python outils\planches\planche_aretes.py -- [quick]
puis : python outils\planches\assembler.py <sortie>\grille.json <sortie>\planche_aretes.png"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import studio as ST                                   # noqa: E402
import bpy                                            # noqa: E402
from material_library import aretes as AR               # noqa: E402

RAYONS = (0.0, 0.2, 0.4, 0.6)
W, H, E = 40.0, 26.0, 3.0                              # plaque : largeur (x), hauteur (z), épaisseur (y, face avant en y = 0)
FENETRE = (16.0, 9.0, 1.2, -4.0, 16.0)                 # w, h, rayon des coins, centre x, centre z
TROU = (2.5, 11.0, 7.0)                                # rayon, centre x, centre z
ENCOCHE = (2.2, 3.2, -W / 2 + 3.2, 7.0)                # rayon, distance au bord gauche, centre x, centre z

sc, col, SORTIE = ST.preparer("aretes", res=(1200, 900))
NC = int(next((a[3:] for a in ST.ARGV if a.startswith("nc=")), "6"))      # segments des congés


def srgb(h):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


def matiere(nom, rayon_bevel):
    m = bpy.data.materials.new(nom); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = srgb("#3b3f45"); b.inputs["Roughness"].default_value = 0.40
    b.inputs["Sheen Weight"].default_value = 0.08; b.inputs["Sheen Roughness"].default_value = 0.6
    return AR.bevel_rendu(m, rayon_bevel) if rayon_bevel > 0 else m


def piece(nom, r_geo, m):
    """Plaque dressée sur le bureau (bas en z = 0), découpes à congé r_geo sur la face avant."""
    cz = H / 2
    bm = AR.plaque(W, H, 2.0, 0.0, E, (r_geo, r_geo), cz=cz)
    me = bpy.data.meshes.new(nom); bm.to_mesh(me); bm.free(); me.materials.append(m)
    o = bpy.data.objects.new(nom, me); col.objects.link(o)
    fw, fh, fr, fx, fz = FENETRE; R, tx, tz = TROU; Re, de, ex, ez = ENCOCHE
    AR.retrancher(o, [AR.coupe(AR.contour_rrect(fw, fh, fr), -1.0, E + 1.0, conge=r_geo, n_conge=NC, cx=fx, cz=fz),
                      AR.coupe(AR.contour_cercle(R), -1.0, E + 1.0, conge=r_geo, n_conge=NC, cx=tx, cz=tz),
                      AR.coupe(AR.encoche_u(Re, de, sens=-1.0, rf=1.0), -1.0, E + 1.0, conge=r_geo, n_conge=NC, cx=ex, cz=ez)])
    o.rotation_euler.z = math.radians(-22)
    return o


pieces = {}
for r in RAYONS:
    pieces[("geo", r)] = piece(f"ARETE_geo_{r}", r, matiere(f"ARETE_geo_{r}", 0.0))
    pieces[("rendu", r)] = piece(f"ARETE_rendu_{r}", 0.0, matiere(f"ARETE_rendu_{r}", r))

# contrôle par mesure : arêtes de plus de 45° sur la face avant et le contour (le dos des découpes reste vif : non vu)
bpy.context.view_layer.update()
for (mode, r), o in pieces.items():
    if mode != "geo": continue
    av = [(p, a) for p, a in AR.aretes_vives(o, 45.0) if (o.matrix_world.inverted() @ p).y < E / 2]
    print(f"CONTROLE arêtes vives (> 45°) face avant, géométrie r {r} : {len(av)}", flush=True)
    if r > 0:
        for p, a in av[:12]:
            q = o.matrix_world.inverted() @ p; print(f"   x {q.x:6.2f} y {q.y:5.2f} z {q.z:6.2f} : {a:5.1f}°", flush=True)

CAMS = {"34": ST.camera(col, "CAM_34", (-62, -118, 52), (1.0, 0.0, 12.0), 85, 8.0),
        "gros_plan": ST.camera(col, "CAM_gros_plan", (-38, -60, 34), (-10.0, 0.0, 13.0), 135, 11.0)}

tous = list(pieces.values())
lignes = []
for mode, titre in (("geo", "Géométrie : plaque() et coupe(congé = r)"), ("rendu", "Rendu : arêtes vives + nœud Bevel r")):
    for vue in ("34", "gros_plan"):
        imgs = []
        for r in RAYONS:
            ST.montrer([pieces[(mode, r)]], tous)
            imgs.append(ST.rendre(sc, CAMS[vue], os.path.join(SORTIE, f"{mode}_{vue}_r{r}.png")))
        lignes.append(dict(titre=f"{titre} — {'trois quarts' if vue == '34' else 'gros plan'}", images=imgs))

g = dict(titre="Arêtes — même pièce, rayons 0 / 0,2 / 0,4 / 0,6 mm (studio du site)",
         colonnes=[f"r = {str(r).replace('.', ',')} mm" for r in RAYONS], lignes=lignes,
         pied="Peinture satinée grise sans grain (base #3b3f45). Géométrie : congés sur la face avant seulement. "
              "Rendu : nœud Bevel, Cycles seulement (STL inchangées).")
with open(os.path.join(SORTIE, "grille_quick.json" if ST.QUICK else "grille.json"), "w", encoding="utf-8") as f:
    json.dump(g, f, ensure_ascii=False, indent=1)
print("FINI", SORTIE, flush=True)
