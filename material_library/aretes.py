r"""Arêtes : aucune arête vive (règle de Lou, 2026-09-29) — outils communs ; la règle écrite : methode/aretes.md.
Deux moyens, qui se complètent :
- la GÉOMÉTRIE, pour ce qui se voit en silhouette ou se fabrique (rayon d'outil, congé d'impression) : plaque() (rectangle
  arrondi épais à arêtes arrondies), coupe() (outil de découpe à congé ou chanfrein sur la face visible), adoucir() (biseau
  appliqué, normales durcies et pondérées) ;
- le RENDU (Cycles seulement ; volume et STL inchangés) : bevel_rendu() / aretes_douces() (nœud Bevel sous le relief).
Après un booléen : retrancher() lisse par angle (lisser()). Contrôle par mesure : aretes_vives().
Unités : mm. Repère des maquettes : plaque dans le plan xz, épaisseur le long de y, -y vers l'utilisateur, face avant en y_face.
Repris de MFS le 2026-10-27 (maquette_grand_format.py : rrect, loft, profil_arrondi, plaque_xz, coupe_xz, adoucir, bevel_rendu,
booleen ; photoreal.py : aretes_douces ; fixations.py : congé de trou_attache)."""
import math

import bmesh
import bpy
from mathutils import Vector

# rayons par défaut du nœud Bevel (mm), réglés sur les rendus du F-COM1 / F-COM2 (Lou, 2026-10-25 → 27)
RAYONS = dict(acrylique=0.4,    # plaque peinte « jour / nuit » : découpes et contour (« angles droits trop sharps »)
              pla=0.3,          # pièces FDM de l'imprimeur FDM
              resine=0.25,      # SLA JLC, résine 9600 (aretes_douces du F-COM1)
              nylon=0.25,       # MJF PA12
              molette=0.6,      # molette (« bords trop vifs à 0,25 »)
              vis=0.2,          # têtes de vis (frappe à froid)
              pcb=0.15)         # cartes électroniques
ANGLE_LISSE = 35.0              # degrés : au-delà, l'arête reste marquée au lissage (set_sharp_from_angle)


# ------------------------------------------------------------------ contours et lofts
def rrect(w, h, r, n=8):
    """Rectangle arrondi centré (sens trigonométrique), n segments par coin : même nombre de points quel que soit r."""
    r = max(r, 1e-3); pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n); pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def loft(bm, anneaux, fermer_debut=True, fermer_fin=True):
    """Anneaux = listes de Vector de même longueur ; relie les anneaux par des quads, bouche les extrémités (n-gones)."""
    vs = [[bm.verts.new(p) for p in a] for a in anneaux]
    n = len(vs[0])
    for a, b in zip(vs, vs[1:]):
        for i in range(n):
            bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    if fermer_debut: bm.faces.new(list(reversed(vs[0])))
    if fermer_fin: bm.faces.new(vs[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return vs


def profil_arrondi(e0, e1, rayon, n=4):
    """Profil (y, retrait) d'une plaque d'épaisseur [e0, e1] le long de y, arêtes avant / arrière arrondies (rayon = (av, ar))."""
    r0, r1 = rayon; pts = []
    for i in range(n + 1):           # arrondi avant : de la face avant (retrait r0) au flanc (retrait 0)
        a = math.radians(90 * i / n); pts.append((e0 + r0 * (1 - math.cos(a)), r0 * (1 - math.sin(a))))
    for i in range(n + 1):           # arrondi arrière : du flanc à la face arrière
        a = math.radians(90 * i / n); pts.append((e1 - r1 + r1 * math.sin(a), r1 * (1 - math.cos(a))))
    return pts


def plaque(w, h, r, y0, y1, arr, cx=0.0, cz=0.0, n=8):
    """Plaque rectangle arrondi (coins de rayon r) dans le plan xz, épaisse de y0 à y1, arêtes avant / arrière arrondies
    (arr = (av, ar), 0 = vive) : bmesh. (plaque_xz de la maquette du F-COM2.)"""
    bm = bmesh.new(); anneaux = []
    prof = profil_arrondi(y0, y1, arr)
    prof = [p for i, p in enumerate(prof) if i == 0 or p != prof[i - 1]]      # arête vive (rayon 0) : pas d'anneaux confondus
    for y, retrait in prof:
        anneaux.append([Vector((cx + x, y, cz + z)) for x, z in rrect(w - 2 * retrait, h - 2 * retrait, max(r - retrait, 0.05), n)])
    loft(bm, anneaux)
    return bm


# ------------------------------------------------------------------ découpes à congé
def contour_rrect(w, h, r, n=8):
    """Contour de découpe rectangle arrondi : e → points décalés de e vers l'extérieur."""
    return lambda e: rrect(w + 2 * e, h + 2 * e, r + e, n)


def contour_cercle(R, n=48):
    """Contour de découpe circulaire de rayon R : e → points décalés de e."""
    return lambda e: [((R + e) * math.cos(2 * math.pi * i / n), (R + e) * math.sin(2 * math.pi * i / n)) for i in range(n)]


def encoche_u(R, d, sens=1.0, rf=1.0, n=48):
    """Trou de rayon R ouvert sur un bord à la distance d du centre (encoche en U, sens = +1 bord vers +u, -1 vers -u), entrée
    arrondie de rayon rf : e → points. Un congé ou un chanfrein de e ≥ rf croiserait le contour (bug du 2026-10-27) : refusé."""
    loin = d + 3.0

    def contour(e):
        if e > rf - 0.05:
            raise ValueError(f"encoche_u : décalage {e:.2f} ≥ rayon d'entrée {rf:.2f} - 0,05 (contour croisé) : augmenter rf")
        r_, f_ = R + e, rf - e                      # dessiné pour un bord à droite (u > 0) puis retourné
        bas = [(d - f_ + f_ * math.sin(math.pi / 2 * i / 8), -r_ - f_ + f_ * math.cos(math.pi / 2 * i / 8)) for i in range(9)]
        pts = [(-r_ * math.sin(math.pi * i / n), r_ * math.cos(math.pi * i / n)) for i in range(n + 1)]
        pts += bas + [(loin, -r_ - f_), (loin, r_ + f_)] + [(u, -v) for u, v in bas[::-1]]
        pts = [(sens * u, v) for u, v in pts]
        return pts[::-1] if sens < 0 else pts
    return contour


def coupe(contour, y0, y1, conge=0.0, chanf=0.0, y_face=0.0, cx=0.0, cz=0.0, n_conge=6):
    """Outil de découpe le long de y (de y0, devant la face, à y1, derrière la pièce) autour de (cx, cz), à retrancher :
    bord de la face y_face arrondi d'un congé de `conge` (quart de cercle tangent à la face et à la paroi, comme
    fixations.trou_attache, `n_conge` segments), ou cassé d'un chanfrein à 45° de `chanf` (coupe_xz de la maquette) ; les deux à 0 : découpe droite.
    contour : contour_rrect(), contour_cercle(), encoche_u() ou toute fonction e → [(u, v)] à nombre de points constant."""
    if conge > 0:
        prof = [(y0, conge)] + [(y_face + conge - conge * math.cos(math.pi / 2 * k / n_conge),
                                 conge - conge * math.sin(math.pi / 2 * k / n_conge)) for k in range(n_conge + 1)] + [(y1, 0.0)]
    elif chanf > 0:
        prof = [(y0, chanf + y_face - y0), (y_face + chanf, 0.0), (y1, 0.0)]
    else:
        prof = [(y0, 0.0), (y1, 0.0)]
    bm = bmesh.new()
    vs = loft(bm, [[Vector((cx + u, y, cz + v)) for u, v in contour(e)] for y, e in prof])
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])   # fonds concaves (encoches) : triangulés
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


# ------------------------------------------------------------------ biseau appliqué, lissage, booléens
def lisser(ob, angle=ANGLE_LISSE, ponderer=False):
    """Lissage par angle (arêtes de plus de `angle` degrés marquées) ; ponderer : normales pondérées par l'aire des faces,
    appliquées (contre les traînées des longs triangles laissés par les booléens)."""
    ob.data.shade_smooth(); ob.data.set_sharp_from_angle(angle=math.radians(angle))
    if ponderer:
        ob.modifiers.new("normales", "WEIGHTED_NORMAL").keep_sharp = True
        _appliquer_modificateurs(ob)
    return ob


def adoucir(ob, largeur, segments=3, angle=40.0, lisse=ANGLE_LISSE):
    """Pas d'arête vive : biseau appliqué de `largeur` mm sur les arêtes de plus de `angle` degrés (`segments` segments), normales
    durcies et pondérées (biseau des pièces du transpondeur et du F-COM2)."""
    ob.data.shade_smooth(); ob.data.set_sharp_from_angle(angle=math.radians(lisse))
    b = ob.modifiers.new("biseau", "BEVEL"); b.width = largeur; b.segments = segments; b.limit_method = "ANGLE"
    b.angle_limit = math.radians(angle); b.harden_normals = True
    ob.modifiers.new("normales", "WEIGHTED_NORMAL").keep_sharp = True
    _appliquer_modificateurs(ob)
    return ob


def retrancher(cible, outils, op="DIFFERENCE", solveur="MANIFOLD", angle=ANGLE_LISSE, ponderer=True):
    """Booléen appliqué : outils = maillages bmesh (coupe(), …) retranchés de (ou unis à) `cible`, puis lissage par angle et
    normales pondérées (sans elles, les longs triangles du booléen tirent l'ombrage de la face plane le long d'un congé : ligne
    sombre vue sur la planche d'arêtes du 2026-10-27 ; booleen de la maquette = ponderer=False). Outils temporaires supprimés."""
    col = cible.users_collection[0]; tmp = []
    for i, bm_o in enumerate(outils):
        me = bpy.data.meshes.new(f"_outil_{cible.name}_{i}"); bm_o.to_mesh(me); bm_o.free()
        o = bpy.data.objects.new(me.name, me); col.objects.link(o); o.hide_render = True; o.hide_viewport = True; tmp.append(o)
        mod = cible.modifiers.new(f"b{i}", "BOOLEAN"); mod.operation = op; mod.object = o
        mod.solver = solveur if bpy.app.version >= (4, 5) or solveur != "MANIFOLD" else "EXACT"   # Manifold : Blender 4.5+
    _appliquer_modificateurs(cible)
    for o in tmp:
        me = o.data; bpy.data.objects.remove(o); bpy.data.meshes.remove(me)
    return lisser(cible, angle, ponderer)


def _appliquer_modificateurs(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    for m_ in list(ob.modifiers): ob.modifiers.remove(m_)
    ancien = ob.data; ob.data = me; bpy.data.meshes.remove(ancien)


def aretes_vives(ob, angle=45.0):
    """Contrôle par mesure (règle de Lou : « le vérifier par mesure, pas seulement à l'œil ») : arêtes du maillage évalué dont
    l'angle dièdre dépasse `angle` degrés → liste de (milieu de l'arête en coordonnées monde, angle en degrés)."""
    dg = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new(); bm.from_object(ob, dg); bm.transform(ob.matrix_world)
    vives = []
    for e in bm.edges:
        if len(e.link_faces) == 2:
            a = math.degrees(e.calc_face_angle())
            if a > angle: vives.append(((e.verts[0].co + e.verts[1].co) / 2, a))
    bm.free()
    return vives


# ------------------------------------------------------------------ arêtes adoucies au rendu (nœud Bevel)
def bevel_rendu(m, rayon=None):
    """Pas d'arête vive au rendu (Lou, 2026-10-27) : nœud Bevel « aretes_douces » de `rayon` mm (défaut : propriété « arrondi » de la
    matière, sinon 0,25) au pied de la chaîne de relief de chaque Principled BSDF (sous le dernier nœud Bump, sinon sur l'entrée
    Normal du BSDF) ; il arrondit visuellement toutes les arêtes de la pièce. Relançable : met le rayon à jour."""
    rayon = m.get("arrondi", 0.25) if rayon is None else rayon
    nt = m.node_tree
    for b in [n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"]:
        entree = b.inputs["Normal"]
        while entree.is_linked and entree.links[0].from_node.type == "BUMP":
            entree = entree.links[0].from_node.inputs["Normal"]
        if not entree.is_linked:
            bev = nt.nodes.get("aretes_douces")
            if bev is None:
                bev = nt.nodes.new("ShaderNodeBevel"); bev.name = "aretes_douces"; bev.samples = 8
            nt.links.new(bev.outputs["Normal"], entree)
        elif entree.links[0].from_node.type == "BEVEL":         # déjà adoucie (ici ou par la matière elle-même)
            bev = entree.links[0].from_node
        else:
            print(f"ATTENTION bevel_rendu {m.name} : chaîne de normale inconnue ({entree.links[0].from_node.type}), arête non adoucie")
            continue
        bev.inputs["Radius"].default_value = rayon
    return m


def aretes_douces(materiaux, rayon=0.25, sauf=()):
    """bevel_rendu() sur chaque matière (propriété « arrondi » prioritaire) sauf celles nommées dans `sauf` (inscriptions à fleur,
    écrans plans : l'arrondi y dessinerait un liseré sombre) et les matières liées (non modifiables). (aretes_douces de photoreal.)"""
    for m in materiaux:
        if m and m.name not in sauf and m.library is None and m.use_nodes:
            bevel_rendu(m, m.get("arrondi", rayon))
