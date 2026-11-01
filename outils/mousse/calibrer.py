r"""Mesure la hauteur de `mousse.hauteur` sur une coupe plane (Geometry Nodes, grille de points) et cherche les gains K qui
retrouvent les mesures de la vraie géométrie.
    blender -b --factory-startup --python outils\mousse\calibrer.py"""
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from material_library.matieres import mousse as M  # noqa: E402

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene


def mesurer(face, k, cote=6.0, n=600):
    ng = bpy.data.node_groups.new("mesure", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    A = M.Arbre(ng, geo=True)
    go = A.n("NodeGroupOutput")
    gr = A.n("GeometryNodeMeshGrid"); gr.inputs["Size X"].default_value = cote; gr.inputs["Size Y"].default_value = cote
    gr.inputs["Vertices X"].default_value = n; gr.inputs["Vertices Y"].default_value = n
    pos = A.n("GeometryNodeInputPosition").outputs[0]
    if face == "dessus":
        p, inter, d = pos, (0.0, 0.0, -1.0), 1.0
    else:                                  # flanc : plan y = 0, coordonnées (x, 0, z)
        s = A.n("ShaderNodeSeparateXYZ"); A.L.new(pos, s.inputs[0])
        c = A.n("ShaderNodeCombineXYZ"); A.L.new(s.outputs["X"], c.inputs["X"]); A.L.new(s.outputs["Y"], c.inputs["Z"])
        p, inter, d = c.outputs[0], (0.0, 1.0, 0.0), 0.0
    h = M.hauteur(A, p, inter, d, kf=k, kd=k)
    st = A.n("GeometryNodeStoreNamedAttribute"); st.data_type = "FLOAT"; st.domain = "POINT"; st.inputs["Name"].default_value = "h"
    A.L.new(gr.outputs[0], st.inputs["Geometry"]); A.L.new(h, st.inputs["Value"]); A.L.new(st.outputs[0], go.inputs[0])
    ob = bpy.data.objects.new("m", bpy.data.meshes.new("m")); sc.collection.objects.link(ob)
    ob.modifiers.new("g", "NODES").node_group = ng
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    a = ev.data.attributes["h"]; v = np.zeros(len(a.data), dtype=np.float32); a.data.foreach_get("value", v)
    bpy.data.objects.remove(ob); bpy.data.node_groups.remove(ng)
    z = -v * 1000                           # µm, positif en creux
    return dict(sa=float(np.mean(np.abs(z - z.mean()))), p50=float(np.percentile(z, 50)), p95=float(np.percentile(z, 95)),
                plat=float(np.mean(z < 15) * 100)), z


def ecart(st, c):
    # le zéro n'est pas le même que sur la géométrie (le plan de coupe y recule par arrachement) : on compare la forme de la répartition,
    # et la part de surface sans creux (à faire baisser : « trop de surface pleine »)
    return abs(st["sa"] - c["sa"]) / c["sa"] + abs((st["p95"] - st["p50"]) - (c["p95"] - c["p50"])) / (c["p95"] - c["p50"]) + st["plat"] / 100


GRILLES = {"flanc": [dict(df=d, wf=w, tf=t) for d in (0.008, 0.012) for w in (0.02, 0.035, 0.05) for t in (0.25, 0.4, 0.6, 0.9)],
           "dessus": [dict(dd=d, wd=w, ld=l, lc=c) for d in (0.015, 0.025) for w in (0.03, 0.05) for l in (0.12, 0.2) for c in (0.5, 0.7)]}
for face in ("dessus", "flanc"):
    c = M.CIBLES[face]
    meilleur = None
    for g in GRILLES[face]:
        M.P.update(g)
        st, _ = mesurer(face, 1.0, n=300)
        k = c["sa"] / st["sa"]
        st2, _ = mesurer(face, k, n=300)
        e = ecart(st2, c)
        if meilleur is None or e < meilleur[0]:
            meilleur = (e, dict(g), k, st2)
    print(f"CALIB {face} : ecart {meilleur[0]:.2f} reglages {meilleur[1]} k={meilleur[2]:.3f} mesure {meilleur[3]} cible {c}")
    M.P.update(meilleur[1])
print("FINI")
