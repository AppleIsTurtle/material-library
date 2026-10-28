r"""Filets, tiges, écrous, rondelles et inserts (géométrie bmesh, sans matière ni objet ; pieces.py les habille). Repris de MFS :
boitier/scripts/visserie_photoreal.py (2026-10-16, Lou : « les vis n'ont pas de filetage, l'écrou et la rondelle sont pleins ») et
tige() / ecrou() / tube_y() de boitier/scripts/maquette_grand_format.py. Filetage ISO réel (profil à 60°, hélice à droite).
Repère : axe parallèle à y passant par (cx, cz), coordonnées en mm."""
import math

import bmesh
from mathutils import Vector

from . import normes as N


def anneau_y(bm, cx, cz, y, rayon, seg=64):
    return [bm.verts.new((cx + rayon * math.cos(2 * math.pi * k / seg), y, cz + rayon * math.sin(2 * math.pi * k / seg))) for k in range(seg)]


def coudre(bm, a, b):
    n = len(a)
    for k in range(n): bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))


def tour(bm, cx, cz, profil, seg=64):
    """Pièce de révolution d'axe y : profil [(y, rayon)…] ; rayon 0 au bout = fermé par un éventail."""
    anneaux = []
    for y, rr in profil:
        anneaux.append([bm.verts.new((cx, y, cz))] if rr < 1e-6 else anneau_y(bm, cx, cz, y, rr, seg))
    for a, b in zip(anneaux, anneaux[1:]):
        if len(a) == 1 and len(b) > 1:
            for k in range(len(b)): bm.faces.new((a[0], b[(k + 1) % len(b)], b[k]))
        elif len(b) == 1 and len(a) > 1:
            for k in range(len(a)): bm.faces.new((a[k], a[(k + 1) % len(a)], b[0]))
        else: coudre(bm, a, b)
    return anneaux


def orienter(bm, cx, cz, vers_axe=False):
    """Normales radiales (vers l'extérieur, ou vers l'axe d'un taraudage) pour une surface ouverte d'axe y."""
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median(); radial = Vector((c.x - cx, 0.0, c.z - cz))
        if radial.length < 1e-9: continue
        if (f.normal.dot(radial) < 0) != vers_axe: f.normal_flip()


def filet(bm, cx, cz, y0, y1, d, pas, interne=False, seg=40, sortie=0.0):
    """Hélice ISO à 60° d'axe y entre y0 et y1 (dans un sens ou l'autre), diamètre nominal d, hélice à droite.
    Profil sur un pas : fond 1/4, flanc, sommet 1/8, flanc. Extérieur : sommet à d/2, fond à d/2 − 0,6134 p ;
    intérieur (taraudage) : sommet à d/2 − 0,5413 p (côté axe), fond à d/2 + 0,02. sortie = nombre de pas sur lesquels le filet
    extérieur s'efface vers le fond aux deux bouts (filet qui « sort » sur le chanfrein de la pointe et sous la tête, comme une vis
    roulée ; 0 = filet coupé net, celui des maquettes de MFS). Renvoie (rayon du sommet, rayon du fond)."""
    sens = 1.0 if y1 > y0 else -1.0
    if interne: R, r = d / 2 + 0.02, d / 2 - 0.5413 * pas; prof = [(0.0, R), (0.25, R), (0.5625, r), (0.6875, r), (1.0, R)]
    else: R, r = d / 2, d / 2 - 0.6134 * pas; prof = [(0.0, r), (0.25, r), (0.5625, R), (0.6875, R), (1.0, r)]
    tours = max(1.0, abs(y1 - y0) / pas - 1.0); n = int(round(tours * seg))
    vs = [bm.verts.new((cx + rad, y0 + sens * a * pas, cz)) for a, rad in prof]
    es = [bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
    bmesh.ops.spin(bm, geom=vs + es, cent=(cx, y0, cz), axis=(0.0, sens, 0.0), dvec=(0.0, sens * pas / seg, 0.0),
                   angle=2 * math.pi * n / seg, steps=n, use_merge=False)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    if sortie > 0 and not interne:
        ts = [v.co.y * sens for v in bm.verts]; t0, t1 = min(ts), max(ts)
        for v, t in zip(bm.verts, ts):
            f = min(1.0, max(0.0, min(t - t0, t1 - t) / (sortie * pas))); f = f * f * (3 - 2 * f)
            u = Vector((v.co.x - cx, 0.0, v.co.z - cz)); rad = u.length
            if rad > r: u *= (r + (rad - r) * f) / rad; v.co.x, v.co.z = cx + u.x, cz + u.z
    orienter(bm, cx, cz, vers_axe=interne)
    return R, r


def tige(cx, cz, y0, longueur, d, pas=None, sortie=0.0):
    """Tige filetée ISO d'axe y depuis y0 (dessous de la tête) vers +y : (filet réel, âme : collet lisse 0,4, noyau, pointe
    chanfreinée) — tige() de la maquette du F-COM2 ; sortie : voir filet()."""
    pas = pas or N.PAS[d]; y1 = y0 + longueur
    bm_f = bmesh.new(); R_, r_ = filet(bm_f, cx, cz, y0 + 0.4, y1 - 0.3, d, pas, sortie=sortie)
    bm_a = bmesh.new()
    tour(bm_a, cx, cz, [(y0 - 0.05, d / 2 - 0.05), (y0 + 0.4, d / 2 - 0.05), (y0 + 0.42, r_ + 0.005), (y1 - 0.3, r_ + 0.005),
                        (y1, r_ - 0.25), (y1, 0.0)], seg=48)
    bmesh.ops.recalc_face_normals(bm_a, faces=bm_a.faces)
    return bm_f, bm_a


def ecrou(cx, cz, y_av, y_ar, d=3, pas=None, ouverture=None):
    """Écrou hexagonal (ISO 4032 ; défaut : cotes de la table pour Md) entre y_av et y_ar : faces chanfreinées à 30° (cercle
    d'appui = 0,95 sur plats), alésage taraudé réel : (corps, taraudage)."""
    pas = pas or N.PAS[d]; ouverture = ouverture or N.ISO_4032[d]["s"]
    bm = bmesh.new(); seg = 48

    def hexa(k):                                             # rayon de l'hexagone dans la direction k (sommets à 30°)
        a = 2 * math.pi * k / seg; da = ((a - math.pi / 6) % (math.pi / 3)) - math.pi / 6
        return (ouverture / 2) / math.cos(da), a
    rc = 0.95 * ouverture / 2                                # cercle d'appui ; chanfrein = cône à 30° jusqu'aux sommets
    sgn = 1.0 if y_ar > y_av else -1.0

    def couronnes(y_face, sens):
        face, bord = [], []
        for k in range(seg):
            rr, a = hexa(k); h = max(0.0, rr - rc) * math.tan(math.radians(30))
            face.append(bm.verts.new((cx + min(rr, rc) * math.cos(a), y_face, cz + min(rr, rc) * math.sin(a))))
            bord.append(bm.verts.new((cx + rr * math.cos(a), y_face + sens * h, cz + rr * math.sin(a))))
        return face, bord
    a0, a1 = couronnes(y_av, sgn); a3, a2 = couronnes(y_ar, -sgn)
    coudre(bm, a0, a1); coudre(bm, a1, a2); coudre(bm, a2, a3)
    ri = d / 2 + 0.02; i0 = anneau_y(bm, cx, cz, y_av, ri, seg); i3 = anneau_y(bm, cx, cz, y_ar, ri, seg)
    coudre(bm, i0, a0); coudre(bm, a3, i3); coudre(bm, i3, i0)       # faces d'appui et alésage
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm2 = bmesh.new(); filet(bm2, cx, cz, y_av + 0.1 * sgn, y_ar - 0.1 * sgn + pas * sgn, d, pas, interne=True)
    return bm, bm2


def rondelle(cx, cz, y_av, y_ar=None, d=3, d_ext=None, d_int=None, casse=0.08):
    """Rondelle plate percée DIN 125 (défaut : cotes de la table ; y_ar = y_av + h), arêtes légèrement cassées (0,08)."""
    c = N.DIN_125[d]; d_ext = d_ext or c["d2"]; d_int = d_int or c["d1"]
    y_ar = y_av + c["h"] if y_ar is None else y_ar
    bm = bmesh.new(); seg = 72; k = casse; s = 1.0 if y_ar > y_av else -1.0
    re, ri = d_ext / 2, d_int / 2
    prof = [(y_av, ri + k), (y_av, re - k), (y_av + k * s, re), (y_ar - k * s, re), (y_ar, re - k), (y_ar, ri + k),
            (y_ar - k * s, ri), (y_av + k * s, ri)]
    anneaux = [anneau_y(bm, cx, cz, y, rr, seg) for y, rr in prof]
    for a, b in zip(anneaux, anneaux[1:] + anneaux[:1]): coudre(bm, a, b)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def insert(cx, cz, y_fond, y_face, r_in, r_out, n_moletage=24, n=96):
    """Insert fileté à chaud (laiton) : tube d'axe y, face visible en y_face (tournée vers +y), extérieur moleté (n_moletage
    stries), arête de la face extérieure adoucie de 0,15 ; alésage figuré par un fond (filetage dans l'ombre) : (insert, fond)
    — tube_y() de la maquette du F-COM2. Cotes d'un insert du commerce : insert_cotes()."""
    bm = bmesh.new()

    def anneau(r_f, y):
        return [bm.verts.new((cx + r_f(2 * math.pi * i / n) * math.cos(2 * math.pi * i / n), y,
                              cz + r_f(2 * math.pi * i / n) * math.sin(2 * math.pi * i / n))) for i in range(n)]
    mol = (lambda th: r_out - 0.18 * (0.5 + 0.5 * math.cos(n_moletage * th)) ** 2) if n_moletage else (lambda th: r_out)
    ext = [anneau(mol, y_fond), anneau(mol, y_face - 0.15), anneau(lambda th: r_out - 0.15, y_face)]
    inn = [anneau(lambda th: r_in + 0.1, y_face), anneau(lambda th: r_in, y_face - 0.1), anneau(lambda th: r_in, y_fond)]
    rings = ext + inn
    for a, c in zip(rings, rings[1:]):
        for i in range(n): bm.faces.new((a[i], a[(i + 1) % n], c[(i + 1) % n], c[i]))
    for i in range(n): bm.faces.new((rings[-1][i], rings[-1][(i + 1) % n], rings[0][(i + 1) % n], rings[0][i]))   # fond
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    fond = bmesh.new()
    f = fond.faces.new([fond.verts.new((cx + r_in * math.cos(2 * math.pi * i / 32), y_face - 2.0, cz + r_in * math.sin(2 * math.pi * i / 32)))
                        for i in range(32)])
    if f.normal.y < 0: f.normal_flip()
    return bm, fond


def insert_cotes(d):
    """(r_in, r_out, longueur, rayon du logement à prévoir) d'un insert laiton du commerce Md (normes.INSERT_LAITON)."""
    c = N.INSERT_LAITON[d]
    return d / 2, c["d1"] / 2, c["l"], c["trou"] / 2
