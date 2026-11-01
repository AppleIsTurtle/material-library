r"""Mousse PE en vraie géométrie (Geometry Nodes, grilles SDF), par étapes de fabrication : la référence des gros plans et du calibrage.
Trop lourde pour un objet entier : la matière de l'objet entier est material_library/matieres/mousse.py, calée sur celle-ci.
Étape 1, la matière : expansion à l'azote sans moule, cellules quasi isotropes ; parois fines (cloisons de Voronoï 3D), un peu
froissées ; jonctions épaissies (bords de Plateau) par un congé SDF ; tailles variables (graines irrégulières + légère déformation).
Étape 2, les découpes. Dessus (z = ZT) : scie à ruban horizontale (lame fine, défile en x), plan net, très légère ondulation de la
lame ; près du plan les parois sont cisaillées et couchées dans le sens de la lame, et un peu écrasées (rebords épaissis, aplatis).
Flanc (y = YF) : jet d'eau vertical (le long de z), stries et ondulation, arrachement de profondeur variable, parois amincies et
effrangées près de la coupe, arête du haut un peu écrasée par le jet.
Étape 3, le collage à chaud de deux plaques.
    blender -b --factory-startup --python outils\mousse\geometrie_reference.py -- [sortie=dossier] [cote=3] [cellule=0.4] [paroi=0.018] [voxel=0.009] [conge=2] [echelle=1]"""
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import material_library as SP  # noqa: E402

args = dict(a.split("=") for a in (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []))
SORTIE = args.get("sortie", os.path.join(SP.DONNEES, "planches", "mousse")); os.makedirs(SORTIE, exist_ok=True)
COTE = float(args.get("cote", 3.0)); HAUT = float(args.get("haut", 1.6)); PROF = float(args.get("prof", 1.6)); CELL = float(args.get("cellule", 0.4)); PAROI = float(args.get("paroi", 0.018))
VOX = float(args.get("voxel", 0.009)); CONGE = int(args.get("conge", 2)); NOM = args.get("nom", "decoupe")
RBULLE = (float(args.get("rmin", 0.64)), float(args.get("rmax", 0.8)))   # base validée par Lou (2026-11-01)
MODE = args.get("cellules", "bulles"); AMP = (float(args.get("amin", 0.6)), float(args.get("amax", 1.0)))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.unit_settings.system = "METRIC"; sc.unit_settings.scale_length = 0.001; sc.unit_settings.length_unit = "MILLIMETERS"

ng = bpy.data.node_groups.new("mousse_matiere", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
N, L = ng.nodes, ng.links


def n(t, **kw):
    nd = N.new(t)
    for k, v in kw.items():
        setattr(nd, k, v)
    return nd


def op(o, a, b=None, c=None):
    m = n("ShaderNodeMath", operation=o)
    for i, v in enumerate((a, b, c)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            m.inputs[i].default_value = v
        else:
            L.new(v, m.inputs[i])
    return m.outputs[0]


def vop(o, a, b):
    m = n("ShaderNodeVectorMath", operation=o)
    for i, v in enumerate((a, b)):
        if isinstance(v, tuple):
            m.inputs[i].default_value = v
        else:
            L.new(v, m.inputs[i])
    return m.outputs[0]


out = n("NodeGroupOutput")
topo = n("GeometryNodeCubeGridTopology")
r = int(round(COTE / VOX))
YF, ZT = 0.12, HAUT - 0.12                                       # plans de coupe (flanc, dessus)
topo.inputs["Bounds Min"].default_value = (0, 0, 0); topo.inputs["Bounds Max"].default_value = (COTE, PROF, HAUT)
topo.inputs["Resolution X"].default_value = r
topo.inputs["Resolution Y"].default_value = int(round(PROF / VOX)); topo.inputs["Resolution Z"].default_value = int(round(HAUT / VOX))
pos = n("GeometryNodeInputPosition").outputs[0]
# légère déformation : tailles et formes de cellules variables, sans orientation privilégiée (expansion isotrope)
wn = n("ShaderNodeTexNoise"); wn.inputs["Scale"].default_value = 1 / (2.5 * CELL); wn.inputs["Detail"].default_value = 1.0
L.new(pos, wn.inputs["Vector"])
warp = N.new("ShaderNodeVectorMath"); warp.operation = "SCALE"
L.new(vop("SUBTRACT", wn.outputs["Color"], (0.5, 0.5, 0.5)), warp.inputs[0]); warp.inputs["Scale"].default_value = 0.35 * CELL
sep0 = n("ShaderNodeSeparateXYZ"); L.new(pos, sep0.inputs[0])
dz = op("SUBTRACT", ZT, sep0.outputs["Z"])                         # profondeur sous le dessus
dy = op("SUBTRACT", sep0.outputs["Y"], YF)                         # profondeur derrière le flanc
# scie à ruban : près du plan, la matière est entraînée dans le sens de la lame (-x), d'autant plus qu'on est près de la surface
cis = op("MULTIPLY", op("EXPONENT", op("MULTIPLY", op("MAXIMUM", dz, 0.0), -1 / (0.18 * CELL))), -0.22 * CELL)
cisv = n("ShaderNodeCombineXYZ"); L.new(cis, cisv.inputs["X"])
wc = n("ShaderNodeTexNoise"); wc.inputs["Scale"].default_value = 1 / (0.9 * CELL); wc.inputs["Detail"].default_value = 0.0; L.new(pos, wc.inputs["Vector"])
warp2 = N.new("ShaderNodeVectorMath"); warp2.operation = "SCALE"
L.new(vop("SUBTRACT", wc.outputs["Color"], (0.5, 0.5, 0.5)), warp2.inputs[0]); warp2.inputs["Scale"].default_value = float(args.get("courbure", 0.3)) * CELL
q = vop("ADD", vop("ADD", vop("ADD", pos, warp.outputs[0]), warp2.outputs[0]), cisv.outputs[0])
vo = n("ShaderNodeTexVoronoi"); vo.voronoi_dimensions = "3D"; vo.feature = "DISTANCE_TO_EDGE"
vo.inputs["Scale"].default_value = 1 / CELL; vo.inputs["Randomness"].default_value = 0.85
L.new(q, vo.inputs["Vector"])
# parois froissées : leur position ondule de quelques microns
fr = n("ShaderNodeTexNoise"); fr.inputs["Scale"].default_value = 1 / (0.35 * CELL); fr.inputs["Detail"].default_value = 2.0
L.new(pos, fr.inputs["Vector"])
froisse = op("MULTIPLY", op("SUBTRACT", fr.outputs["Fac"], 0.5), 2 * 0.006)
# épaisseur des parois : écrasées (épaissies) sous la lame, amincies et effrangées derrière le jet
ecr = op("EXPONENT", op("MULTIPLY", op("MAXIMUM", dz, 0.0), -1 / (0.15 * CELL)))
arr = op("EXPONENT", op("MULTIPLY", op("MAXIMUM", dy, 0.0), -1 / (0.25 * CELL)))
fr2 = n("ShaderNodeTexNoise"); fr2.inputs["Scale"].default_value = 1 / (0.07 * CELL); fr2.inputs["Detail"].default_value = 1.0
L.new(pos, fr2.inputs["Vector"])
effr = op("MULTIPLY", op("SUBTRACT", fr2.outputs["Fac"], 0.5), 2 * 0.5)                         # -0,5 … 0,5
epais = op("MULTIPLY", PAROI / 2, op("ADD", op("ADD", 1.0, op("MULTIPLY", ecr, float(args.get("ecrase", 2.0)))),
            op("MULTIPLY", arr, op("SUBTRACT", op("MULTIPLY", effr, 1.6), 0.55))))
paroi = op("SUBTRACT", op("ADD", op("MULTIPLY", vo.outputs["Distance"], CELL), froisse), epais)   # < 0 dans la paroi
# mousse « humide » : chaque cellule est une bulle (sphère de rayon tiré au hasard) ; là où deux bulles se touchent il reste un
# film plan (la paroi ci-dessus), ailleurs la matière remplit les coins en surfaces courbes : fonds et dômes organiques
vf = n("ShaderNodeTexVoronoi"); vf.voronoi_dimensions = "3D"; vf.feature = "F1"
vf.inputs["Scale"].default_value = 1 / CELL; vf.inputs["Randomness"].default_value = 0.85; L.new(q, vf.inputs["Vector"])
sc_c = n("FunctionNodeSeparateColor"); L.new(vf.outputs["Color"], sc_c.inputs[0])
r_i = op("MULTIPLY_ADD", sc_c.outputs["Red"], RBULLE[1] - RBULLE[0], RBULLE[0])                  # rayon (unités de cellule)
bos = n("ShaderNodeTexNoise"); bos.inputs["Scale"].default_value = 1 / (0.22 * CELL); bos.inputs["Detail"].default_value = 3.0
bos.inputs["Roughness"].default_value = 0.55; L.new(pos, bos.inputs["Vector"])
bosse = op("MULTIPLY", op("SUBTRACT", bos.outputs["Fac"], 0.5), 2 * 0.045 * CELL)                # bulles bosselées
hors_bulle = op("ADD", op("SUBTRACT", op("MULTIPLY", r_i, CELL), op("MULTIPLY", vf.outputs["Distance"], CELL)), bosse)
paroi = op("MINIMUM", paroi, hors_bulle)
if MODE == "alligator":
    # bruit « alligator » (Side Effects, HDK ; port OSL d'I. Mavrov, CC BY-SA 4.0) : pour chaque cellule de Worley un poids
    # a_i · smoothstep(1 - d_i), valeur = poids le plus fort - le second. Approché ici par les deux points les plus proches
    # (Voronoï F1 et F2 et leurs couleurs). Crête (≈ 0) là où deux cellules s'équilibrent = paroi ; les amplitudes au hasard
    # courbent les parois vers la cellule la plus faible et font varier la taille des alvéoles.
    def poids(feature):
        v = n("ShaderNodeTexVoronoi"); v.voronoi_dimensions = "3D"; v.feature = feature
        v.inputs["Scale"].default_value = 1 / CELL; v.inputs["Randomness"].default_value = 1.0; L.new(q, v.inputs["Vector"])
        c = n("FunctionNodeSeparateColor"); L.new(v.outputs["Color"], c.inputs[0])
        amp = op("MULTIPLY_ADD", c.outputs["Red"], AMP[1] - AMP[0], AMP[0])
        mr = n("ShaderNodeMapRange"); mr.interpolation_type = "SMOOTHSTEP"; mr.clamp = True
        L.new(op("SUBTRACT", 1.0, v.outputs["Distance"]), mr.inputs["Value"])
        return op("MULTIPLY", amp, mr.outputs["Result"])
    alli = op("ABSOLUTE", op("SUBTRACT", poids("F1"), poids("F2")))
    # distance approximative à la crête (pente ≈ 1,5 par cellule) ; matière où l'on est près d'une crête
    paroi = op("ADD", op("SUBTRACT", epais, op("MULTIPLY", alli, CELL / 1.5)), op("ADD", froisse, op("MULTIPLY", bosse, -0.6)))
    paroi = op("MULTIPLY", paroi, -1.0)
# plans de coupe : dessus presque parfait (lame) ; flanc strié, ondulé, arraché par endroits
ond = n("ShaderNodeTexNoise"); ond.inputs["Scale"].default_value = 1 / 2.5; ond.inputs["Detail"].default_value = 1.0; L.new(pos, ond.inputs["Vector"])
nv = n("ShaderNodeTexNoise"); nv.inputs["Scale"].default_value = 1 / (0.9 * CELL); nv.inputs["Detail"].default_value = 2.0; nv.inputs["Roughness"].default_value = 0.55; L.new(pos, nv.inputs["Vector"])
niveaux = op("MULTIPLY", op("SUBTRACT", nv.outputs["Fac"], 0.5), 2 * float(args.get("niveaux", 0.04)))      # les rebords ne sont pas tous au même niveau
dessus = op("SUBTRACT", op("SUBTRACT", op("SUBTRACT", sep0.outputs["Z"], ZT), op("MULTIPLY", op("SUBTRACT", ond.outputs["Fac"], 0.5), 0.02)), niveaux)
mps = vop("MULTIPLY", pos, (1 / (0.12 * CELL), 1.0, 1 / (3.0 * CELL)))                       # stries le long du jet (z)
stn = n("ShaderNodeTexNoise"); stn.inputs["Scale"].default_value = 1.0; stn.inputs["Detail"].default_value = 2.0; L.new(mps, stn.inputs["Vector"])
stries = op("MULTIPLY", op("SUBTRACT", stn.outputs["Fac"], 0.5), 2 * 0.012)
arn = n("ShaderNodeTexNoise"); arn.inputs["Scale"].default_value = 1 / (1.2 * CELL); arn.inputs["Detail"].default_value = 2.0; L.new(pos, arn.inputs["Vector"])
arrache = op("MULTIPLY", op("MAXIMUM", op("SUBTRACT", arn.outputs["Fac"], 0.5), 0.0), 2 * 0.25 * CELL)   # creux d'arrachement
# arête du haut écrasée par le jet : le flanc recule un peu près du dessus
ar_e = op("MULTIPLY", op("EXPONENT", op("MULTIPLY", op("MAXIMUM", dz, 0.0), -1 / (0.15 * CELL))), 0.06 * CELL)
flanc = op("SUBTRACT", op("ADD", op("ADD", YF, stries), op("ADD", arrache, ar_e)), sep0.outputs["Y"])     # < 0 derrière le flanc
# étape 3 — collage à chaud de deux plaques (air chaud) : fine couche fondue, dense et bosselée, parois épaissies autour
ZL = ZT - float(args.get("collage", 2.6))
lc = n("ShaderNodeTexNoise"); lc.inputs["Scale"].default_value = 1 / 2.2; lc.inputs["Detail"].default_value = 1.5; L.new(pos, lc.inputs["Vector"])
lc2 = n("ShaderNodeTexNoise"); lc2.inputs["Scale"].default_value = 1 / 0.6; lc2.inputs["Detail"].default_value = 1.0; L.new(pos, lc2.inputs["Vector"])
ondl = op("MULTIPLY", op("SUBTRACT", lc.outputs["Fac"], 0.5), 2 * 0.06)                    # la ligne ondule (±0,06 mm)
dzl = op("ABSOLUTE", op("SUBTRACT", op("SUBTRACT", sep0.outputs["Z"], ZL), ondl))
demi_ep = op("MULTIPLY_ADD", lc2.outputs["Fac"], 0.06, 0.0)                               # épaisseur 0 … 0,06 (manques)
demi_ep = op("MAXIMUM", op("SUBTRACT", demi_ep, 0.012), 0.0)
fond = op("EXPONENT", op("MULTIPLY", op("MULTIPLY", dzl, dzl), -1 / (0.12 * 0.12)))
paroi = op("SUBTRACT", paroi, op("MULTIPLY", fond, 0.04 * CELL))
paroi = op("MINIMUM", paroi, op("ADD", op("SUBTRACT", dzl, demi_ep), op("MULTIPLY", bosse, 0.4)))
if args.get("echelle", "0") == "1":
    # fond de la bande de calcul : matière pleine, le regard ne traverse plus
    E_ = float(args.get("coque", 0.9))
    paroi = op("MINIMUM", paroi, op("SUBTRACT", E_ - 0.12, op("MINIMUM", dz, dy)))
    # dessus tranché : creux peu profonds, en cuvette courbe propre à chaque cellule (jamais de fond plat)
    # profondeur = base + part au hasard × (1 - distance au centre de la bulle) ; le flanc garde ses cellules profondes
    cuv = op("MAXIMUM", op("SUBTRACT", 1.0, vf.outputs["Distance"]), 0.0)
    limite = op("ADD", op("MULTIPLY", op("ADD", 0.16, op("MULTIPLY", cuv, op("MULTIPLY", sc_c.outputs["Green"], float(args.get("creux", 0.7))))), CELL), op("MULTIPLY", bosse, 0.5))
    paroi = op("MINIMUM", paroi, op("MAXIMUM", op("SUBTRACT", limite, dz), op("SUBTRACT", 0.45, dy)))
paroi = op("SMOOTH_MAX", paroi, dessus, float(args.get("arrondi", 0.035)))            # rebords arrondis sous la lame
paroi = op("MAXIMUM", paroi, flanc)
# bords du bloc coupés net (plus de parois tronquées par la grille de calcul)
DG = float(args.get("etendue", 4.0))
bx = op("MAXIMUM", op("SUBTRACT", 0.15, sep0.outputs["X"]), op("SUBTRACT", sep0.outputs["X"], COTE - 0.15))
by = op("SUBTRACT", sep0.outputs["Y"], YF + DG - 0.15)
bz = op("SUBTRACT", ZT - DG + 0.15, sep0.outputs["Z"])
paroi = op("MAXIMUM", paroi, op("MAXIMUM", bx, op("MAXIMUM", by, bz)))
f2g = n("GeometryNodeFieldToGrid"); f2g.grid_items.new("FLOAT", "mousse")
L.new(topo.outputs[0], f2g.inputs["Topology"]); L.new(op("MULTIPLY", paroi, -1.0), f2g.inputs["mousse"])
fondg = n("GeometryNodeSetGridBackground"); L.new(f2g.outputs["mousse"], fondg.inputs["Grid"])
fondg.inputs["Background"].default_value = -1.0                     # hors de la grille = vide : pas de faces de fermeture
g2m = n("GeometryNodeGridToMesh"); L.new(fondg.outputs[0], g2m.inputs["Grid"]); g2m.inputs["Threshold"].default_value = 0.0
geo = g2m.outputs[0]
if CONGE:   # bords de Plateau : congé aux jonctions des parois (maillage → SDF → congé → maillage)
    m2s = n("GeometryNodeMeshToSDFGrid"); L.new(geo, m2s.inputs["Mesh"])
    m2s.inputs["Voxel Size"].default_value = VOX; m2s.inputs["Band Width"].default_value = 3
    fil = n("GeometryNodeSDFGridFillet"); L.new(m2s.outputs[0], fil.inputs["Grid"]); fil.inputs["Iterations"].default_value = CONGE
    g2 = n("GeometryNodeGridToMesh"); L.new(fil.outputs[0], g2.inputs["Grid"]); g2.inputs["Threshold"].default_value = 0.0
    geo = g2.outputs[0]
lisse = n("GeometryNodeSetShadeSmooth"); L.new(geo, lisse.inputs[0])
setmat = n("GeometryNodeSetMaterial"); L.new(lisse.outputs[0], setmat.inputs[0]); L.new(setmat.outputs[0], out.inputs[0])

mat = bpy.data.materials.new("PE_anthracite"); mat.use_nodes = True
b = mat.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.028, 0.030, 0.034, 1); b.inputs["Roughness"].default_value = 0.42
b.inputs["Specular IOR Level"].default_value = 0.45
setmat.inputs["Material"].default_value = mat

ECHELLE = args.get("echelle", "0") == "1"
if not ECHELLE:
    ob = bpy.data.objects.new("cube_mousse", bpy.data.meshes.new("cube_mousse")); sc.collection.objects.link(ob)
    ob.modifiers.new("matiere", "NODES").node_group = ng
    dg = bpy.context.evaluated_depsgraph_get(); ev = ob.evaluated_get(dg)
else:
    # à l'échelle des photos : on ne calcule que deux coques minces le long des faces visibles (la matière y est la même)
    E, D = float(args.get("coque", 0.9)), float(args.get("etendue", 4.0))
    def cal(v):                                            # bornes sur la même grille de voxels : coques superposables sans écart
        return round(v / VOX) * VOX
    coques = {"coque_dessus": ((0, cal(YF - 0.05), cal(ZT - E)), (cal(COTE), cal(YF + D), cal(ZT + 0.05))),
              "coque_flanc": ((0, cal(YF - 0.05), cal(ZT - D)), (cal(COTE), cal(YF + E), cal(ZT - E)))}   # bord à bord (fond « vide » : pas de face de jointure)
    if args.get("domaine", "L") == "L":
        coques = {}
        g = ng.copy(); t = next(nd for nd in g.nodes if nd.bl_idname == "GeometryNodeCubeGridTopology")
        f2 = next(nd for nd in g.nodes if nd.bl_idname == "GeometryNodeFieldToGrid")
        def plan(sx, sy, loc, rot):
            m = g.nodes.new("GeometryNodeMeshGrid"); m.inputs["Size X"].default_value = sx; m.inputs["Size Y"].default_value = sy
            m.inputs["Vertices X"].default_value = 2; m.inputs["Vertices Y"].default_value = 2
            tr = g.nodes.new("GeometryNodeTransform"); g.links.new(m.outputs[0], tr.inputs[0])
            tr.inputs["Translation"].default_value = loc; tr.inputs["Rotation"].default_value = rot
            return tr.outputs[0]
        jo = g.nodes.new("GeometryNodeJoinGeometry")
        g.links.new(plan(COTE + 0.4, D + 0.4, (COTE / 2, YF + D / 2, ZT - E / 2), (0, 0, 0)), jo.inputs[0])
        g.links.new(plan(COTE + 0.4, D + 0.4, (COTE / 2, YF + E / 2, ZT - D / 2), (1.5707963, 0, 0)), jo.inputs[0])
        bande = g.nodes.new("GeometryNodeMeshToSDFGrid"); g.links.new(jo.outputs[0], bande.inputs["Mesh"])
        bande.inputs["Voxel Size"].default_value = VOX; bande.inputs["Band Width"].default_value = int(round(E / 2 / VOX)) + 2
        g.links.new(bande.outputs[0], f2.inputs["Topology"]); g.nodes.remove(t)
        ob = bpy.data.objects.new("coque_L", bpy.data.meshes.new("coque_L")); sc.collection.objects.link(ob)
        ob.modifiers.new("matiere", "NODES").node_group = g
    for nom_c, (bmin, bmax) in coques.items():
        g = ng.copy(); t = next(nd for nd in g.nodes if nd.bl_idname == "GeometryNodeCubeGridTopology")
        t.inputs["Bounds Min"].default_value = bmin; t.inputs["Bounds Max"].default_value = bmax
        for i, a_ in enumerate("XYZ"):
            t.inputs[f"Resolution {a_}"].default_value = max(2, int(round((bmax[i] - bmin[i]) / VOX)))
        ob = bpy.data.objects.new(nom_c, bpy.data.meshes.new(nom_c)); sc.collection.objects.link(ob)
        ob.modifiers.new("matiere", "NODES").node_group = g
    dg = bpy.context.evaluated_depsgraph_get(); ev = ob.evaluated_get(dg)
print("TRIANGLES", len(ev.data.polygons))

if ECHELLE and args.get("mesure", "1") == "1":
    import numpy as np
    from mathutils.bvhtree import BVHTree
    bvh = BVHTree.FromObject(ob.evaluated_get(dg), dg)
    rng = np.random.default_rng(1)
    def mesure(nom_f, gen, direction, reference):
        h, rates = [], 0
        for _ in range(40000):
            o_ = Vector(gen()); hit = bvh.ray_cast(o_, Vector(direction), 3.0)
            if hit[0] is None:
                rates += 1
            else:
                h.append((hit[0] - o_).length - reference)
        h = np.array(h); sa = np.mean(np.abs(h - h.mean()))
        print(f"MESURE {nom_f}: Sa {sa * 1000:.0f} um, profondeur p50 {np.percentile(h, 50) * 1000:.0f} p95 {np.percentile(h, 95) * 1000:.0f} p99 {np.percentile(h, 99) * 1000:.0f} um, rayons sans impact {rates / 400:.2f} %")
    xr = lambda: rng.uniform(1.0, COTE - 1.0)
    mesure("dessus", lambda: (xr(), rng.uniform(YF + 1.0, YF + 3.5), ZT + 0.5), (0, 0, -1), 0.5)
    mesure("flanc", lambda: (xr(), YF - 0.5, rng.uniform(ZT - 3.5, ZT - 0.3)), (0, 1, 0), 0.5)
w = bpy.data.worlds.new("fond"); sc.world = w
w.node_tree.nodes["Background"].inputs[0].default_value = (0.6, 0.62, 0.66, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = float(args.get("monde", 0.35))


def viser(o, loc, cible):
    if o.name not in sc.collection.objects:
        sc.collection.objects.link(o)
    o.location = loc; o.rotation_euler = (Vector(cible) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


c = Vector((COTE / 2,) * 3) if not ECHELLE else Vector((COTE / 2, YF + 1.0, ZT - 1.0))
k = 1.0 if not ECHELLE else 3.0
for nom, d, e in (("cle", (-7 * k, -9 * k, 8 * k), 20 * k * k), ("contre", (9 * k, 4 * k, 4 * k), 8 * k * k), ("rasant", (2 * k, -10 * k, 0.8 * k), 6 * k * k), ("rasant_dessus", (-10 * k, 1.5 * k, 1.5 * k), 8 * k * k)):
    l = bpy.data.lights.new(nom, "AREA"); l.energy = e; l.size = 4 * k
    viser(bpy.data.objects.new(nom, l), tuple(c + Vector(d)), tuple(c))
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.camera = cam; cam.data.clip_start = 0.1
sc.render.engine = "CYCLES"; sc.cycles.samples = int(args.get("samples", 48)); sc.cycles.use_denoising = True
sc.view_settings.view_transform = "AgX"; sc.view_settings.exposure = float(args.get("expo", 0.8))
sc.render.resolution_x, sc.render.resolution_y = 1200, 900
ke = COTE / 8.0                                                   # cadrages réglés pour 8 mm, mis à l'échelle du bloc
cx = COTE / 2
VUES_E = (("serre_arete", 50, (cx + 3, YF - 6.5, ZT + 6.5), (cx, YF + 0.5, ZT - 0.3)),
          ("serre_dessus", 50, (cx, YF + 1.2, ZT + 7.5), (cx, YF + 2.2, ZT)),
          ("serre_flanc", 70, (cx, YF - 8.5, ZT - 1.9), (cx, YF, ZT - 1.9)),
          ("recul_arete", 50, (cx + 5, YF - 13, ZT + 13), (cx, YF + 0.6, ZT - 0.4)))
for vue, lens, loc, cible in VUES_E if ECHELLE else (("arete", 50, (COTE * 1.25, -PROF * 2.2, HAUT * 3.2), (COTE * 0.5, PROF * 0.45, HAUT * 0.6)),
                              ("dessus", 60, (COTE * 0.5, -PROF * 1.0, HAUT * 3.6), (COTE * 0.5, PROF * 0.6, ZT)),
                              ("flanc", 60, (COTE * 0.5, -PROF * 2.6, HAUT * 0.75), (COTE * 0.5, YF, HAUT * 0.5))):
    cam.data.lens = lens; viser(cam, loc, cible)
    sc.render.filepath = os.path.join(SORTIE, f"{NOM}_{vue}.png"); bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(SORTIE, f"{NOM}.blend"))
print("FINI")
