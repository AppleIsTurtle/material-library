r"""Contrôles automatiques d'une maquette de boîtier (dans Blender) : trous bouchés, collisions, parois trop minces.
Repris des contrôles de la maquette du F-COM2 (MFS, boitier/scripts/maquette_grand_format.py : controle_trous,
controle_collisions, écrits pour les noms GF_*) et rendus génériques : on donne des noms ou des préfixes de noms d'objets.
Méthode : methode/conception_boitier.md, étape 7. Chaque contrôle affiche son bilan (ligne « CONTROLE … ») et le renvoie.

    import material_library.conception.controles as CT
    CT.trous([(0, 33.3), (-52.5, 9)], ["GF_PLAQUE", "GF_EMBASE", "GF_BOITE_LUMIERE", "GF_PCB"])
    CT.collisions(["GF_CAISSON", "GF_PLAQUE"], prefixes=["GF_INSERT_", "GF_CADRE_"],
                  voulus=[("GF_CAISSON", "GF_INSERT_"), ("GF_CADRE_", "GF_VERRE_")])
    CT.parois(["GF_BOITE_LUMIERE"], minimum=1.2)
Repère des maquettes : x à droite, y en profondeur (vers l'arrière), z en haut, mm.
"""
import math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def _noms(noms=(), prefixes=(), exclure_suffixes=("_fond",), collection=None):
    """Noms donnés + objets maillages dont le nom commence par un des préfixes (sans ceux qui finissent par un suffixe exclu)."""
    objets = collection.all_objects if collection else bpy.data.objects
    out = list(noms)
    for o in objets:
        if (o.type == "MESH" and prefixes and o.name.startswith(tuple(prefixes)) and o.name not in out
                and not o.name.endswith(tuple(exclure_suffixes))):
            out.append(o.name)
    return out


def _triangles(me):
    """Triangles du maillage calculés par Blender : les faces concaves laissées par les booléens (couronne d'une collerette en
    une seule face) triangulées en éventail par BVHTree.FromPolygons couvraient le trou → fausses collisions (essai du
    2026-10-27)."""
    me.calc_loop_triangles()
    return [tuple(t.vertices) for t in me.loop_triangles]


def trous(axes, pieces, y_depart=-20.0, longueur=60.0, sauf=(), direction=(0.0, 1.0, 0.0)):
    """Un rayon le long de y (par défaut) à travers chaque axe (x, z) — vis traversantes, axe d'encodeur… — et chaque pièce :
    aucune pièce ne doit l'arrêter. sauf = couples (pièce, (x, z)) à ne pas tester (ex. l'encodeur soudé sur la carte).
    Renvoie la liste des trous bouchés (pièce, x, z, y du choc)."""
    dg = bpy.context.evaluated_depsgraph_get(); bouches = []; n = 0
    for nom in pieces:
        o = bpy.data.objects[nom]; ev = o.evaluated_get(dg); inv = o.matrix_world.inverted()
        for x, z in axes:
            if (nom, (x, z)) in sauf: continue
            n += 1
            orig = inv @ Vector((x, y_depart, z)); dirl = (inv.to_3x3() @ Vector(direction)).normalized()
            hit, loc, *_ = ev.ray_cast(orig, dirl, distance=longueur)
            if hit:
                loc = o.matrix_world @ loc; bouches.append((nom, x, z, round(loc.y, 2)))
                print(f"TROU BOUCHE {nom} ({x:.1f} ; {z:.1f}) à y = {loc.y:.2f}", flush=True)
    print(f"CONTROLE TROUS : {len(bouches)} bouché(s) sur {n}", flush=True)
    return bouches


def collisions(noms=(), prefixes=(), voulus=(), meme_piece=lambda a, b: False, retrait=0.03, collection=None,
               exclure_suffixes=("_fond",)):
    """Pièces qui se pénètrent : surfaces rentrées de `retrait` le long des normales (un simple contact ne compte pas), puis
    recouvrement des arbres BVH, en coordonnées du monde. voulus = couples de préfixes (a, b) dont le recouvrement est voulu
    (insert emmanché, vis dans son insert, vitre serrée par des nervures, pièce multi-matière…) ; meme_piece(a, b) → True pour
    deux objets d'une même pièce (ex. un morceau de lest et son adhésif). Renvoie (collisions, contacts voulus)."""
    dg = bpy.context.evaluated_depsgraph_get()
    liste = _noms(noms, prefixes, exclure_suffixes, collection)

    def arbre(n):
        o = bpy.data.objects[n]; me = o.evaluated_get(dg).to_mesh(); mw = o.matrix_world; m3 = mw.to_3x3()
        vs = [mw @ (v.co - v.normal * retrait) for v in me.vertices]; ps = _triangles(me)
        t = BVHTree.FromPolygons(vs, ps); o.evaluated_get(dg).to_mesh_clear()
        return t
    arbres = {n: arbre(n) for n in liste}

    def voulu(a, b):
        return any((a.startswith(x) and b.startswith(y)) or (a.startswith(y) and b.startswith(x)) for x, y in voulus)
    paires = [(a, b) for i, a in enumerate(liste) for b in liste[i + 1:]
              if not meme_piece(a, b) and arbres[a].overlap(arbres[b])]
    att = [p for p in paires if voulu(*p)]; bad = [p for p in paires if not voulu(*p)]
    for a, b in bad: print(f"COLLISION {a} / {b}", flush=True)
    print(f"CONTROLE COLLISIONS : {len(bad)} collision(s) à corriger, {len(att)} contact(s) voulu(s), {len(liste)} pièces", flush=True)
    return bad, att


def parois(noms, minimum, prefixes=(), pas=1, angle_max=30.0, collection=None):
    """Épaisseur de matière sous chaque triangle (un sur `pas`) : rayon lancé de son centre vers l'intérieur, le long de
    -normale, jusqu'à la face opposée ; signale les parois plus minces que `minimum` (ex. 1,2 en buse 0,4 ; 1,0 pour une
    collerette ; 2,0 autour d'un insert). Seules comptent les faces opposées presque parallèles (écart ≤ angle_max) : les
    arrondis et chanfreins ne donnent pas de fausse alerte. Renvoie [(pièce, épaisseur, point)] (une ligne par zone de 2 mm)."""
    dg = bpy.context.evaluated_depsgraph_get(); minces = []
    cmax = math.cos(math.radians(180.0 - angle_max))
    for nom in _noms(noms, prefixes, (), collection):
        o = bpy.data.objects[nom]; me = o.evaluated_get(dg).to_mesh(); mw = o.matrix_world
        vs = [v.co.copy() for v in me.vertices]; ps = _triangles(me)
        t = BVHTree.FromPolygons(vs, ps); vus = []
        for i in range(0, len(me.loop_triangles), pas):    # triangles : le centre d'une face concave peut tomber hors d'elle
            c, nrm = me.loop_triangles[i].center, me.loop_triangles[i].normal
            loc, n2, _, d = t.ray_cast(c - nrm * 1e-4, -nrm, minimum * 4)
            if loc is None or d >= minimum - 1e-3 or n2.dot(nrm) > cmax: continue
            w = mw @ c
            if any((w - q).length < 2.0 for q in vus): continue
            vus.append(w); minces.append((nom, round(d, 2), tuple(round(x, 1) for x in w)))
            print(f"PAROI MINCE {nom} : {d:.2f} < {minimum} près de ({w.x:.1f} ; {w.y:.1f} ; {w.z:.1f})", flush=True)
        o.evaluated_get(dg).to_mesh_clear()
    print(f"CONTROLE PAROIS : {len(minces)} zone(s) sous {minimum}", flush=True)
    return minces


def volume_cm3(nom):
    """Volume d'une pièce fermée (cm³, maillage évalué, échelle du monde comprise) : pour le chiffrage (chiffrage.sla_jlc…)."""
    import bmesh
    o = bpy.data.objects[nom]; bm = bmesh.new()
    bm.from_object(o, bpy.context.evaluated_depsgraph_get()); bm.transform(o.matrix_world)
    v = abs(bm.calc_volume()) / 1000.0; bm.free()
    return v
