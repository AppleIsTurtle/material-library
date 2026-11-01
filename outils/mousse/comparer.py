r"""Même bloc, mêmes cadrages et mêmes lumières que la vraie géométrie (geometrie_reference.py), mais avec la matière calibrée :
comparaison image par image avant de passer au calage entier.
    blender -b --factory-startup --python outils\mousse\comparer.py -- [sortie=dossier] [samples=48] [dicing=1.5] [vues=serre_arete,...]"""
import os
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import material_library as SP  # noqa: E402
from material_library.matieres import catalogue as CAT, mousse as M  # noqa: E402

args = dict(a.split("=") for a in (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []))
SORTIE = args.get("sortie", os.path.join(SP.DONNEES, "planches", "mousse")); COTE = 16.0; YF = 0.12; ZT = 4.08; D = 4.0
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.unit_settings.system = "METRIC"; sc.unit_settings.scale_length = 0.001; sc.unit_settings.length_unit = "MILLIMETERS"
me = bpy.data.meshes.new("bloc"); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
bmesh.ops.scale(bm, vec=(COTE, D, D), verts=bm.verts); bmesh.ops.translate(bm, vec=(COTE / 2, YF + D / 2, ZT - D / 2), verts=bm.verts)
bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new("bloc", me); sc.collection.objects.link(ob)
M.poser(ob, CAT.construire("mousse_pe_ld33"), float(args.get("voxel", 0.1)))
w = bpy.data.worlds.new("fond"); sc.world = w
w.node_tree.nodes["Background"].inputs[0].default_value = (0.6, 0.62, 0.66, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.6


def viser(o, loc, cible):
    if o.name not in sc.collection.objects:
        sc.collection.objects.link(o)
    o.location = loc; o.rotation_euler = (Vector(cible) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


c = Vector((COTE / 2, YF + 1.0, ZT - 1.0)); k = 3.0
for nom, d, e in (("cle", (-7 * k, -9 * k, 8 * k), 20 * k * k), ("contre", (9 * k, 4 * k, 4 * k), 8 * k * k),
                  ("rasant", (2 * k, -10 * k, 0.8 * k), 6 * k * k), ("rasant_dessus", (-10 * k, 1.5 * k, 1.5 * k), 8 * k * k)):
    l = bpy.data.lights.new(nom, "AREA"); l.energy = e; l.size = 4 * k
    viser(bpy.data.objects.new(nom, l), tuple(c + Vector(d)), tuple(c))
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.camera = cam; cam.data.clip_start = 0.1
sc.render.engine = "CYCLES"; sc.cycles.samples = int(args.get("samples", 48)); sc.cycles.use_denoising = True
sc.cycles.dicing_rate = float(args.get("dicing", 1.5)); sc.cycles.max_subdivisions = 8; sc.cycles.offscreen_dicing_scale = 8
sc.view_settings.view_transform = "AgX"; sc.view_settings.exposure = 1.3
sc.render.resolution_x, sc.render.resolution_y = 1200, 900
cx = COTE / 2
VUES = {"serre_arete": (50, (cx + 3, YF - 6.5, ZT + 6.5), (cx, YF + 0.5, ZT - 0.3)),
        "serre_flanc": (70, (cx, YF - 8.5, ZT - 1.9), (cx, YF, ZT - 1.9)),
        "recul_arete": (50, (cx + 5, YF - 13, ZT + 13), (cx, YF + 0.6, ZT - 0.4))}
os.makedirs(SORTIE, exist_ok=True)
for nom in args.get("vues", "serre_arete,serre_flanc,recul_arete").split(","):
    lens, loc, cible = VUES[nom]; cam.data.lens = lens; viser(cam, loc, cible)
    sc.render.filepath = os.path.join(SORTIE, f"calib_{nom}.png"); bpy.ops.render.render(write_still=True)
print("FINI")
