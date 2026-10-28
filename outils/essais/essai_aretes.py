r"""Essai du chunk-02 : chaque fonction de material_library.aretes marche seule, dans une scène vide.
    blender -b --factory-startup --python outils\essais\essai_aretes.py
Sortie : « OK » par fonction, puis « ESSAI ARETES OK » ; une erreur arrête l'essai (code de sortie 1)."""
import os
import sys
import traceback

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from material_library import aretes as AR       # noqa: E402

col = bpy.context.scene.collection


def objet(nom, bm):
    me = bpy.data.meshes.new(nom); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(nom, me); col.objects.link(o); return o


def etanche(o):
    bm = bmesh.new(); bm.from_mesh(o.data)
    ok = all(e.is_manifold for e in bm.edges); bm.free(); return ok


try:
    p = objet("plaque", AR.plaque(30, 20, 2.0, 0.0, 3.0, (0.4, 0.4), cz=10))
    assert etanche(p), "plaque non étanche"; print("OK plaque")
    p0 = objet("plaque_vive", AR.plaque(30, 20, 2.0, 0.0, 3.0, (0.0, 0.0), cz=10))
    assert etanche(p0), "plaque vive non étanche"; print("OK plaque (arêtes vives)")
    AR.retrancher(p, [AR.coupe(AR.contour_rrect(10, 6, 1.0), -1, 4, conge=0.4, cx=-4, cz=12),
                      AR.coupe(AR.contour_cercle(2.0), -1, 4, chanf=0.3, cx=8, cz=6),
                      AR.coupe(AR.encoche_u(2.0, 3.0, sens=-1, rf=1.0), -1, 4, conge=0.4, cx=-12, cz=5)])
    assert etanche(p), "plaque découpée non étanche"; print("OK coupe + retrancher (congé, chanfrein, encoche)")
    try:
        AR.coupe(AR.encoche_u(2.0, 3.0, rf=0.4), -1, 4, conge=0.6); raise AssertionError("encoche croisée acceptée")
    except ValueError:
        print("OK encoche_u refuse un congé ≥ rayon d'entrée")
    av = [a for q, a in AR.aretes_vives(p, 46.0) if q.y < 1.5]            # 46° : le chanfrein à 45° n'est pas une arête vive
    print(f"OK aretes_vives : {len(av)} arête(s) > 46° sur la face avant (jonction des congés à l'entrée de l'encoche)")
    c = objet("cube", (lambda bm: (bmesh.ops.create_cube(bm, size=10.0), bm)[1])(bmesh.new()))
    assert len(AR.aretes_vives(c, 45.0)) == 12
    AR.adoucir(c, 0.5); assert not AR.aretes_vives(c, 45.0), "cube encore vif"; print("OK adoucir (cube : 12 → 0 arête > 45°)")
    AR.lisser(p0, ponderer=True); print("OK lisser")
    m = bpy.data.materials.new("essai"); m.use_nodes = True
    AR.bevel_rendu(m, 0.3); AR.bevel_rendu(m, 0.4)
    bev = [n for n in m.node_tree.nodes if n.type == "BEVEL"]
    assert len(bev) == 1 and abs(bev[0].inputs["Radius"].default_value - 0.4) < 1e-6; print("OK bevel_rendu (relançable)")
    m2 = bpy.data.materials.new("essai_relief"); m2.use_nodes = True; nt = m2.node_tree
    bp = nt.nodes.new("ShaderNodeBump"); nt.links.new(bp.outputs["Normal"], nt.nodes["Principled BSDF"].inputs["Normal"])
    m2["arrondi"] = 0.6; AR.aretes_douces([m, m2], sauf=("essai",))
    assert abs(bp.inputs["Normal"].links[0].from_node.inputs["Radius"].default_value - 0.6) < 1e-6; print("OK aretes_douces (sous le relief)")
    print("ESSAI ARETES OK")
except Exception:
    traceback.print_exc(); sys.exit(1)
