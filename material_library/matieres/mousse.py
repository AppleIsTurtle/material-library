r"""Mousse PE à cellules fermées, procédurale et sans répétition : matière (Cycles, vrai déplacement) et forme (Geometry Nodes).
    from material_library.matieres import catalogue as CAT, mousse as MO
    m = CAT.construire("mousse_pe_ld33")
    MO.poser(ob, m)                       # forme (arête franche, faces jamais planes, attributs) + subdivision adaptative
Méthode, sources et mesures : methode/mousses.md. Référence en vraie géométrie et calibrage : outils/mousse/.

La matière est un empilement de bulles (Voronoï 3D déformé, sphère de rayon tiré au hasard, film plan entre voisines). En un point de
la coupe, la profondeur visible est celle qu'atteint un rayon lancé vers l'intérieur : sortie de la sphère (√ du discriminant) ou
rencontre du film avec la bulle voisine, au premier des deux. Le fond des alvéoles est donc celui de la bulle coupée, pas un motif.
La même fonction `hauteur` sert au shader (Cycles, vrai déplacement) et aux Geometry Nodes (mesures de calibrage).

Deux faces : dessus tranché à la scie à ruban (`dessus` = 1 : creux limités, rebords épais et arrondis, niveaux variables) et flanc au
jet d'eau (`dessus` = 0 : parois fines et effrangées, cellules profondes, stries, arrachements).
Gains K réglés par outils/mousse/calibrer.py pour retrouver les mesures de la géométrie (rayons sur le bloc de 16 mm).
Sans la forme (matière glissée seule sur un objet) : normale de l'objet, tout en flanc, et il faut un maillage dense pour le relief."""
import bmesh
import bpy

from . import noeuds as N
from .couleurs import srgb

OCC_PROF, OCC_FORCE = 0.22, 0.72   # occlusion des creux : profondeur (mm) et force
CELL = 0.4                # Plastazote LD33 : cellules d'environ 0,4 mm
RBULLE = (0.64, 0.80)     # rayon des bulles, en taille de cellule
KF, KD = 1.013, 1.122     # gains de profondeur flanc / dessus (outils/mousse/calibrer.py, 2026-11-01)
# réglages de la répartition des creux, cherchés par outils/mousse/calibrer.py
P = dict(df=0.008, dd=0.015, wf=0.02, wd=0.03, tf=0.6, ld=0.12, lc=0.5)
CIBLES = {"dessus": dict(sa=51, p50=54, p95=168), "flanc": dict(sa=97, p50=167, p95=349)}   # µm, mesurés sur la géométrie


class Arbre:
    """Câblage commun aux arbres de shader et de géométrie."""
    def __init__(self, nt, geo=False):
        self.nt, self.N, self.L, self.geo = nt, nt.nodes, nt.links, geo

    def n(self, typ, **kw):
        nd = self.N.new(typ)
        for k, v in kw.items():
            setattr(nd, k, v)
        return nd

    def val(self, sock, v):
        if isinstance(v, (int, float, tuple)):
            sock.default_value = v
        else:
            self.L.new(v, sock)

    def m(self, op, a, b=None, c=None):
        nd = self.n("ShaderNodeMath", operation=op)
        for i, v in enumerate((a, b, c)):
            if v is not None:
                self.val(nd.inputs[i], v)
        return nd.outputs[0]

    def v(self, op, a, b=None, ech=None):
        nd = self.n("ShaderNodeVectorMath", operation=op)
        self.val(nd.inputs[0], a)
        if b is not None:
            self.val(nd.inputs[1], b)
        if ech is not None:
            self.val(nd.inputs["Scale"], ech)
        return nd.outputs["Value"] if op in ("DOT_PRODUCT", "LENGTH", "DISTANCE") else nd.outputs["Vector"]

    def bruit(self, vec, echelle, detail=1.0, rugo=0.5):
        t = self.n("ShaderNodeTexNoise")
        t.inputs["Scale"].default_value = echelle; t.inputs["Detail"].default_value = detail; t.inputs["Roughness"].default_value = rugo
        self.L.new(vec, t.inputs["Vector"])
        return t

    def centre(self, fac, amp):
        return self.m("MULTIPLY", self.m("SUBTRACT", fac, 0.5), 2 * amp)

    def lisse(self, v, a, b):
        nd = self.n("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP", clamp=True)
        self.val(nd.inputs["Value"], v)
        nd.inputs["From Min"].default_value, nd.inputs["From Max"].default_value = a, b
        return nd.outputs["Result"]

    def melange(self, d, a, b):                     # a si d = 0, b si d = 1
        return self.m("ADD", self.m("MULTIPLY", a, self.m("SUBTRACT", 1.0, d)), self.m("MULTIPLY", b, d))

    def voronoi(self, q, feature):
        t = self.n("ShaderNodeTexVoronoi"); t.voronoi_dimensions = "3D"; t.feature = feature
        t.inputs["Scale"].default_value = 1 / CELL; t.inputs["Randomness"].default_value = 0.85
        self.L.new(q, t.inputs["Vector"])
        return t

    def couleur(self, sock):
        c = self.n("FunctionNodeSeparateColor" if self.geo else "ShaderNodeSeparateColor")
        self.L.new(sock, c.inputs[0])
        return c


def hauteur(A, pos, vers_interieur, dessus, kf=None, kd=None, bord=1.0):
    """Hauteur en mm (négative dans la matière) au point `pos` d'une coupe de normale intérieure `vers_interieur`."""
    kf = KF if kf is None else kf; kd = KD if kd is None else kd
    C = CELL
    # mêmes déformations que la géométrie : tailles variables, parois courbes
    w1 = A.v("SUBTRACT", A.bruit(pos, 1 / (2.5 * C), 1.0).outputs["Color"], (0.5, 0.5, 0.5))
    w2 = A.v("SUBTRACT", A.bruit(pos, 1 / (0.9 * C), 0.0).outputs["Color"], (0.5, 0.5, 0.5))
    q = A.v("ADD", A.v("ADD", pos, A.v("SCALE", w1, ech=0.35 * C)), A.v("SCALE", w2, ech=0.3 * C))
    v1, v2 = A.voronoi(q, "F1"), A.voronoi(q, "F2")
    c1, c2 = v1.outputs["Position"], v2.outputs["Position"]
    coul = A.couleur(v1.outputs["Color"])
    r_i = A.m("MULTIPLY", A.m("MULTIPLY_ADD", coul.outputs["Red"], RBULLE[1] - RBULLE[0], RBULLE[0]), C)
    # rayon → sphère
    vc = A.v("SUBTRACT", c1, q)
    b = A.v("DOT_PRODUCT", vc, vers_interieur)
    l2 = A.v("DOT_PRODUCT", vc, vc); l_ = A.m("SQRT", l2)
    t_sph = A.m("ADD", b, A.m("SQRT", A.m("MAXIMUM", A.m("ADD", A.m("SUBTRACT", A.m("MULTIPLY", b, b), l2), A.m("MULTIPLY", r_i, r_i)), 0.0)))
    # paroi avec la voisine (plan bissecteur de c1 et c2) : elle ne sert qu'au rebord. Le fond reste celui de la sphère, continu dans
    # toute la cellule (un fond calculé sur le film saute quand la voisine la plus proche change : éclats polygonaux)
    nv = A.n("ShaderNodeVectorMath", operation="NORMALIZE"); A.L.new(A.v("SUBTRACT", c2, c1), nv.inputs[0]); nf = nv.outputs["Vector"]
    milieu = A.v("SCALE", A.v("ADD", c1, c2), ech=0.5)
    d_film = A.v("DOT_PRODUCT", A.v("SUBTRACT", milieu, q), nf)        # distance à la paroi, positive dans la cellule
    t0 = t_sph
    # rebords : minces et effrangés au jet d'eau, épais et arrondis sous la lame
    eff = A.m("MULTIPLY", A.centre(A.bruit(pos, 1 / (0.09 * C), 1.0).outputs["Fac"], 0.014), A.m("SUBTRACT", 1.0, dessus))
    demi = A.melange(dessus, P["df"], P["dd"])
    w = A.melange(dessus, P["wf"], P["wd"])
    r_film = A.n("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP", clamp=True)
    A.L.new(A.m("SUBTRACT", A.m("ADD", d_film, eff), demi), r_film.inputs["Value"]); r_film.inputs["From Min"].default_value = 0.0
    A.val(r_film.inputs["From Max"], w)
    r_sph = A.n("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP", clamp=True)
    A.L.new(A.m("ADD", A.m("SUBTRACT", r_i, l_), eff), r_sph.inputs["Value"]); r_sph.inputs["From Min"].default_value = 0.0
    A.val(r_sph.inputs["From Max"], w)
    ouvert = A.m("MULTIPLY", r_film.outputs["Result"], r_sph.outputs["Result"])
    # dessus : creux limités en cuvette propre à chaque cellule
    cuv = A.m("MAXIMUM", A.m("SUBTRACT", 1.0, v1.outputs["Distance"]), 0.0)
    limite = A.m("MULTIPLY", A.m("ADD", P["ld"], A.m("MULTIPLY", cuv, A.m("MULTIPLY", coul.outputs["Green"], P["lc"]))), C)
    # flanc : profondeur comprimée sans plafond (t_f (1 - e^(-t/t_f))) : le fond garde sa courbe, jamais de palier plat
    comp = A.m("MULTIPLY", P["tf"], A.m("SUBTRACT", 1.0, A.m("EXPONENT", A.m("DIVIDE", t0, -P["tf"]))))
    t = A.melange(dessus, comp, A.m("SMOOTH_MIN", t0, limite, 0.03))
    bos = A.centre(A.bruit(pos, 1 / (0.3 * C), 2.0, 0.5).outputs["Fac"], 0.07 * C)   # fonds bosselés
    creux = A.m("MULTIPLY", A.m("MAXIMUM", A.m("ADD", t, bos), 0.0), ouvert)
    creux = A.m("MULTIPLY", A.m("MULTIPLY", creux, A.melange(dessus, kf, kd)), bord)      # bord < 1 : moins creux près des arêtes
    # niveau de la coupe : rebords à des hauteurs variables sous la lame ; stries et arrachements au jet d'eau
    niveaux = A.m("MULTIPLY", A.centre(A.bruit(pos, 1 / (0.9 * C), 2.0, 0.55).outputs["Fac"], 0.04), dessus)
    et = A.n("ShaderNodeVectorMath", operation="MULTIPLY"); A.val(et.inputs[0], pos); et.inputs[1].default_value = (1 / (0.12 * C), 1 / (0.12 * C), 1 / (3.0 * C))
    stries = A.centre(A.bruit(et.outputs[0], 1.0, 2.0).outputs["Fac"], 0.012)
    arr = A.m("MULTIPLY", A.m("MAXIMUM", A.m("SUBTRACT", A.bruit(pos, 1 / (1.2 * C), 2.0).outputs["Fac"], 0.5), 0.0), 2 * 0.25 * C)
    jet = A.m("MULTIPLY", A.m("SUBTRACT", stries, arr), A.m("SUBTRACT", 1.0, dessus))
    A.creux = creux                                                     # pour l'occlusion de la matière
    plan = A.m("SUBTRACT", 1.0, ouvert)                                 # le plan de coupe bouge, pas le fond des bulles
    return A.m("SUBTRACT", A.m("MULTIPLY", A.m("ADD", niveaux, jet), plan), creux)


def matiere_mousse(f):
    """Fabrique de la fiche du catalogue (champs base, rugosite = flanc, rugosite_dessus)."""
    m, nt, b = N.neuf(f["matiere"])
    (m if hasattr(m, "displacement_method") else m.cycles).displacement_method = "DISPLACEMENT"    # Blender 4.4 : réglage Cycles
    A = Arbre(nt); sortie = next(x for x in A.N if x.bl_idname == "ShaderNodeOutputMaterial")
    tc = A.n("ShaderNodeTexCoord")
    ad = A.n("ShaderNodeAttribute"); ad.attribute_name = "dessus"
    an = A.n("ShaderNodeAttribute"); an.attribute_name = "normale_base"
    # sans la forme, l'attribut vaut zéro : normale de l'objet, pas d'affaissement de bord
    forme = A.m("GREATER_THAN", A.v("LENGTH", an.outputs["Vector"]), 0.01)
    geo = A.n("ShaderNodeNewGeometry")
    vt = A.n("ShaderNodeVectorTransform", vector_type="NORMAL", convert_from="WORLD", convert_to="OBJECT"); A.L.new(geo.outputs["Normal"], vt.inputs[0])
    norm = A.n("ShaderNodeVectorMath", operation="NORMALIZE")
    A.L.new(A.v("ADD", A.v("SCALE", an.outputs["Vector"], ech=forme), A.v("SCALE", vt.outputs[0], ech=A.m("SUBTRACT", 1.0, forme))), norm.inputs[0])
    inter = A.v("SCALE", norm.outputs["Vector"], ech=-1.0)
    ab = A.n("ShaderNodeAttribute"); ab.attribute_name = "dist_arete"
    bord = A.m("MAXIMUM", A.m("ADD", 0.3, A.m("MULTIPLY", A.lisse(ab.outputs["Fac"], 0.0, 0.7), 0.7)), A.m("SUBTRACT", 1.0, forme))
    h = hauteur(A, tc.outputs["Object"], inter, ad.outputs["Fac"], bord=bord)
    # occlusion des creux : le fond d'une alvéole de quelques pixels ne reçoit pas sa vraie ombre au découpage du déplacement ;
    # sans elle les cellules se lisent en relief (galets). Ce n'est pas une variation de teinte de la matière (règle de Lou) mais la
    # lumière qui manque au fond : proportionnelle à la profondeur, 1 sur les rebords.
    occ = A.m("SUBTRACT", 1.0, A.m("MULTIPLY", A.lisse(A.creux, 0.0, OCC_PROF), OCC_FORCE))
    tb = A.n("ShaderNodeVectorMath", operation="SCALE"); tb.inputs[0].default_value = srgb(f["base"])[:3]; A.L.new(occ, tb.inputs["Scale"])
    A.L.new(tb.outputs["Vector"], b.inputs["Base Color"])
    spc = A.m("MULTIPLY", occ, 0.45); A.L.new(spc, b.inputs["Specular IOR Level"])
    dep = A.n("ShaderNodeDisplacement"); A.L.new(h, dep.inputs["Height"])
    dep.inputs["Midlevel"].default_value = 0.0; dep.inputs["Scale"].default_value = 1.0
    A.L.new(dep.outputs[0], sortie.inputs["Displacement"])
    A.L.new(A.melange(ad.outputs["Fac"], f["rugosite"], f["rugosite_dessus"]), b.inputs["Roughness"])
    m.diffuse_color = srgb(f["base"])
    return m


def arbre_forme(nom="SP_mousse_forme", voxel=0.25, materiau=None, densite_chocs=0.002):
    """Geometry Nodes : maillage dense (SDF), arête franche, faces jamais planes (gonflement, bosselage, chocs, affaissement au bord de
    coupe), attributs `dessus` et `normale_base` pris AVANT déformation."""
    ng = bpy.data.node_groups.new(nom, "GeometryNodeTree"); ng.is_modifier = True
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    A = Arbre(ng, geo=True)
    gi, go = A.n("NodeGroupInput"), A.n("NodeGroupOutput")
    m2s = A.n("GeometryNodeMeshToSDFGrid"); A.L.new(gi.outputs[0], m2s.inputs["Mesh"])
    m2s.inputs["Voxel Size"].default_value = voxel; m2s.inputs["Band Width"].default_value = 3
    g2m = A.n("GeometryNodeGridToMesh"); A.L.new(m2s.outputs[0], g2m.inputs["Grid"]); g2m.inputs["Threshold"].default_value = 0.0
    pos, nor = A.n("GeometryNodeInputPosition").outputs[0], A.n("GeometryNodeInputNormal").outputs[0]
    lent = A.centre(A.bruit(pos, 1 / 22.0, 1.5).outputs["Fac"], 0.12)
    moyen = A.centre(A.bruit(pos, 1 / 4.0, 3.0, 0.55).outputs["Fac"], 0.035)
    pts = A.n("GeometryNodeDistributePointsOnFaces"); A.L.new(g2m.outputs[0], pts.inputs["Mesh"])
    pts.inputs["Density"].default_value = densite_chocs; pts.inputs["Seed"].default_value = 3
    prox = A.n("GeometryNodeProximity"); prox.target_element = "POINTS"; A.L.new(pts.outputs["Points"], prox.inputs[0])
    t_ = A.m("POWER", A.m("MAXIMUM", A.m("SUBTRACT", 1.0, A.m("DIVIDE", prox.outputs["Distance"], 1.0)), 0.0), 2.0)
    chocs = A.m("MULTIPLY", t_, A.m("MULTIPLY", A.bruit(pos, 1 / 9.0).outputs["Fac"], -0.16))
    # affaissement le long des arêtes vives de la pièce (compression avant coupe)
    vive = A.m("GREATER_THAN", A.n("GeometryNodeInputMeshEdgeAngle").outputs["Unsigned Angle"], 1.0)
    ar = A.n("GeometryNodeSeparateGeometry"); ar.domain = "EDGE"
    A.L.new(gi.outputs[0], ar.inputs["Geometry"]); A.L.new(vive, ar.inputs["Selection"])
    pa = A.n("GeometryNodeProximity"); pa.target_element = "EDGES"; A.L.new(ar.outputs["Selection"], pa.inputs[0])
    aff = A.m("MULTIPLY", A.m("EXPONENT", A.m("DIVIDE", pa.outputs["Distance"], -0.6)), A.m("MULTIPLY", A.bruit(pos, 1 / 3.0).outputs["Fac"], -0.14))
    total = A.m("ADD", A.m("ADD", lent, moyen), A.m("ADD", chocs, aff))
    sn = A.n("ShaderNodeSeparateXYZ"); A.L.new(nor, sn.inputs[0])
    sd = A.n("GeometryNodeStoreNamedAttribute"); sd.data_type = "FLOAT"; sd.domain = "POINT"; sd.inputs["Name"].default_value = "dessus"
    A.L.new(g2m.outputs[0], sd.inputs["Geometry"]); A.L.new(A.lisse(A.m("ABSOLUTE", sn.outputs["Z"]), 0.75, 0.95), sd.inputs["Value"])
    sv = A.n("GeometryNodeStoreNamedAttribute"); sv.data_type = "FLOAT_VECTOR"; sv.domain = "POINT"; sv.inputs["Name"].default_value = "normale_base"
    A.L.new(sd.outputs[0], sv.inputs["Geometry"]); A.L.new(nor, sv.inputs["Value"])
    sa = A.n("GeometryNodeStoreNamedAttribute"); sa.data_type = "FLOAT"; sa.domain = "POINT"; sa.inputs["Name"].default_value = "dist_arete"
    A.L.new(sv.outputs[0], sa.inputs["Geometry"]); A.L.new(pa.outputs["Distance"], sa.inputs["Value"])
    sp = A.n("GeometryNodeSetPosition"); A.L.new(sa.outputs[0], sp.inputs["Geometry"])
    A.L.new(A.v("SCALE", nor, ech=total), sp.inputs["Offset"])
    lis = A.n("GeometryNodeSetShadeSmooth"); A.L.new(sp.outputs[0], lis.inputs[0])
    sm = A.n("GeometryNodeSetMaterial"); A.L.new(lis.outputs[0], sm.inputs[0])
    if materiau is not None:
        sm.inputs["Material"].default_value = materiau
    A.L.new(sm.outputs[0], go.inputs[0])
    return ng


def poser(ob, materiau, voxel=0.4):
    """Pose la matière et la forme sur `ob` (maillage fermé, 1 unité = 1 mm), puis la subdivision adaptative du vrai déplacement.
    `voxel` : pas de la forme ; 0,4 pour un objet de 20 cm, 0,1 pour un gros plan."""
    ob.data.materials.clear(); ob.data.materials.append(materiau)
    ob.modifiers.new("forme", "NODES").node_group = arbre_forme(f"SP_mousse_forme_{voxel:g}mm", voxel, materiau)
    s = ob.modifiers.new("subdivision", "SUBSURF"); s.subdivision_type = "SIMPLE"
    if hasattr(s, "use_adaptive_subdivision"):
        s.use_adaptive_subdivision = True
    else:                                     # Blender 4.4 : réglage Cycles de l'objet, jeu de fonctions expérimental
        bpy.context.scene.cycles.feature_set = "EXPERIMENTAL"; ob.cycles.use_adaptive_subdivision = True
    return ob


def bloc(nom, materiau, cotes=(16.0, 12.0, 6.0), voxel=0.1, col=None):
    """Petit bloc coupé (aperçus, essais) : dessus tranché, flancs au jet d'eau."""
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=cotes, verts=bm.verts)
    me = bpy.data.meshes.new(nom); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(nom, me); (col or bpy.context.scene.collection).objects.link(ob)
    return poser(ob, materiau, voxel)
