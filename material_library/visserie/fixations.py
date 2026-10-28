r"""Têtes de vis du commerce et fixations des façades — règle : methode/fixations_facade.md. Repris de MFS
(boitier/scripts/fixations.py, standard du 2026-10-27) et rendu paramétrable par la norme (cotes : normes.py).
Vis du commerce seulement (Lou, 2026-10-27 : « des vis accessibles à un prix correct, des vis standards ») :
- ATTACHE (façade → caisson) : vis à tête cylindrique fendue DIN 84 / ISO 1207, inox A2 (M4 × 8 : tête Ø 7 × 2,6, la plus proche
  d'une Dzus), au fond d'une COLLERETTE (coupelle en PLA noir imprimée chez l'imprimeur FDM, Ø 9,5 en M4 comme l'œillet des vraies Dzus),
  posée sur l'embase dans un trou de la plaque un peu plus large qu'elle (anneau d'ombre), ouvert en U sur le bord s'il en est près ;
- VIS À FLEUR (petites vis qui traversent la façade) : fraisée 90° cruciforme ISO 7046 / DIN 965 (M3 : Ø 5,5), acier oxydé noir, à
  fleur de la face avant, dans un fraisage à arête arrondie.
Plus les têtes bombées ISO 7045 et à six pans creux ISO 4762 (tete()). Géométrie seule (bmesh), sans matière ni objet : pieces.py
ou chaque maquette l'habille (objet, booléen, biseau). Repère des maquettes : axe des vis parallèle à y, -y vers l'utilisateur ;
t = saillie vers l'utilisateur depuis un plan d'appui y0 (y = y0 - t). Cotes par défaut (ATTACHE, VIS_FLEUR) = celles du F-COM2.
"""
import math

import bmesh

from . import normes as N


def attache_cotes(d=4, norme="DIN 84", l=8.0):
    """Cotes d'une attache en collerette pour une vis Md × l à tête cylindrique fendue (défaut : M4 × 8 du F-COM2)."""
    c = N.cotes(norme, d); r = c["dk"] / 2
    return dict(tete_r=r, tete_h=c["k"], fente=(c["dk"] + 1.0, c["n"], c["t"]),   # fente traversante : n largeur, t profondeur
                tete_ra=round(0.3 * c["dk"] / 7.0, 3),          # arrondi du bord du dessus de la tête (0,3 en M4)
                coll_re=r + 0.25 + 1.0, coll_ri=r + 0.25, coll_fond=0.8,   # collerette : alésage 0,25 autour de la tête, paroi 1,0
                coll_ra=0.4,                                    # (buse 0,4 de l'imprimeur FDM), fond 0,8 ; arrondi du bord du sommet
                jeu_trou=0.4, r_passage=N.passage(d),           # jeu du trou de la plaque autour de la collerette, passage
                vis_l=l, vis_d=d, vis_pas=c["pas"])


def fleur_cotes(d=3, norme="ISO 7046"):
    """Cotes d'une vis fraisée à fleur (défaut : M3 ISO 7046 du F-COM2)."""
    c = N.cotes(norme, d)
    return dict(tete_r=c["dk"] / 2, tete_k=c["k"], jeu=0.1, arrondi=0.25,   # tête ; jeu et arrondi du fraisage
                croix=N.croix_rendu(norme, d), r_passage=N.passage(d),     # empreinte : demi-longueur, demi-largeur, profondeur
                vis_d=d, vis_pas=c["pas"])


ATTACHE = attache_cotes()        # M4 × 8 DIN 84 : tête Ø 7 × 2,6, fente 1,2 × 1,1, collerette Ø 9,5 (F-COM2)
VIS_FLEUR = fleur_cotes()        # M3 ISO 7046 : Ø 5,5 × 1,65, PH1, passage Ø 3,4 (F-COM2)


def revolution(profil, x, z, y0, n=96, ferme=False):
    """Solide de révolution d'axe y passant par (x, z) ; profil = [(t, r)] parcouru d'un bout à l'autre, r = 0 aux bouts = pôle ;
    ferme = profil en boucle (pièce annulaire : le dernier anneau rejoint le premier)."""
    bm = bmesh.new(); anneaux = []
    for t, r in profil:
        anneaux.append([bm.verts.new((x + r * math.cos(2 * math.pi * i / n), y0 - t, z + r * math.sin(2 * math.pi * i / n)))
                        for i in range(n)] if r > 1e-6 else [bm.verts.new((x, y0 - t, z))])
    for a, b in zip(anneaux, anneaux[1:] + (anneaux[:1] if ferme else [])):
        for i in range(n):
            j = (i + 1) % n
            if len(a) == 1: bm.faces.new((a[0], b[j], b[i]))
            elif len(b) == 1: bm.faces.new((a[i], a[j], b[0]))
            else: bm.faces.new((a[i], a[j], b[j], b[i]))
    for ring in ((anneaux[0], anneaux[-1]) if not ferme else ()):
        if len(ring) > 1: bm.faces.new(ring)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def prisme(contour, x, z, y0, y1):
    """Prisme d'axe y : contour [(u, v)] autour de (x, z), de y0 à y1."""
    bm = bmesh.new()
    av = [bm.verts.new((x + u, y0, z + v)) for u, v in contour]; ar = [bm.verts.new((x + u, y1, z + v)) for u, v in contour]
    bm.faces.new(av); bm.faces.new(ar)
    for i in range(len(contour)):
        j = (i + 1) % len(contour); bm.faces.new((av[i], av[j], ar[j], ar[i]))
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def stade(L, e, r, n=8):
    """Contour d'une fente à bouts arrondis : longueur L, largeur 2e, coins de rayon r."""
    pts = []
    for cx, cz, a0 in ((L / 2 - r, e - r, 0), (-L / 2 + r, e - r, 90), (-L / 2 + r, -e + r, 180), (L / 2 - r, -e + r, 270)):
        pts += [(cx + r * math.cos(math.radians(a0 + 90 * i / n)), cz + r * math.sin(math.radians(a0 + 90 * i / n))) for i in range(n + 1)]
    return pts


def croix(L, e, a):
    """Contour d'une empreinte cruciforme (bras de demi-longueur L, demi-largeur e) tournée de a degrés."""
    pts = [(L, -e), (L, e), (e, e), (e, L), (-e, L), (-e, e), (-L, e), (-L, -e), (-e, -e), (-e, -L), (e, -L), (e, -e)]
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return [(u * c - v * s, u * s + v * c) for u, v in pts]


def hexagone(s, a=0.0):
    """Contour d'un six pans de `s` sur plats, tourné de a degrés."""
    R = s / math.sqrt(3)
    return [(R * math.cos(math.radians(a + 30 + 60 * i)), R * math.sin(math.radians(a + 30 + 60 * i))) for i in range(6)]


def empreinte_croix(x, z, y_dessus, croix_, a):
    """Outil cruciforme à retrancher d'une tête dont le dessus est en y_dessus (vers -y) : bras droits sur 0,41 de la profondeur
    puis pointe effilée (comme un embout PH)."""
    L, e, p = croix_
    anneaux = [(y_dessus - 1.0, croix(L, e, a)), (y_dessus + 0.45 * p / 1.1, croix(L, e, a)),
               (y_dessus + p, croix(0.4 * L / 1.35, 0.12 * L / 1.35, a))]
    em = bmesh.new(); vs = [[em.verts.new((x + u, y, z + v)) for u, v in c] for y, c in anneaux]
    for a_, b_ in zip(vs, vs[1:]):
        for i in range(12): em.faces.new((a_[i], a_[(i + 1) % 12], b_[(i + 1) % 12], b_[i]))
    em.faces.new(vs[0]); em.faces.new(vs[-1][::-1])
    bmesh.ops.triangulate(em, faces=[f for f in em.faces if len(f.verts) > 4])
    bmesh.ops.recalc_face_normals(em, faces=em.faces)
    return em


def _quart(t0, r0, ra, k=6):
    """Arrondi de rayon ra du coin du dessus d'une tête (de la paroi à t0 - ra au dessus en t0)."""
    return [(t0 - ra + ra * math.sin(math.pi / 2 * i / k), r0 - ra + ra * math.cos(math.pi / 2 * i / k)) for i in range(k + 1)]


# ------------------------------------------------------------------ attache (vis DIN 84 dans sa collerette)
def collerette(x, z, y_appui, h, A=ATTACHE):
    """Coupelle posée sur le plan y_appui (embase), haute de h vers l'utilisateur (sommet à fleur de la façade), bord extérieur
    arrondi, arête de l'alésage chanfreinée, fond de coll_fond percé du passage (la tête de la vis y appuie)."""
    re, ri, f, ra, rp = A["coll_re"], A["coll_ri"], A["coll_fond"], A["coll_ra"], A["r_passage"]
    prof = [(0.0, rp), (0.0, re)] + _quart(h, re, ra)
    prof += [(h, ri + 0.25), (h - 0.25, ri), (f + 0.2, ri), (f, ri - 0.2), (f, rp + 0.2), (f - 0.2, rp)]
    return revolution(prof, x, z, y_appui, ferme=True)


def tete_attache(x, z, y_appui, A=ATTACHE, a=0.0):
    """Tête cylindrique fendue DIN 84 posée en y_appui, bord du dessus arrondi, dessous légèrement cassé :
    (maillage, [fente traversante à retrancher, tournée de a degrés])."""
    r, h, ra = A["tete_r"], A["tete_h"], A["tete_ra"]
    prof = [(0.0, 0.0), (0.0, r - 0.1), (0.1, r)] + _quart(h, r, ra) + [(h, 0.0)]
    bm = revolution(prof, x, z, y_appui)
    L, n, t = A["fente"]
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    fente = prisme([(u * c - v * s, u * s + v * c) for u, v in stade(L, n / 2, 0.15)], x, z, y_appui - h - 1.0, y_appui - h + t)
    return bm, [fente]


def trou_attache(x, z, y0, y1, bord=None, n=48, arrondi=0.6, y_face=0.0, A=ATTACHE):
    """Trou de la plaque autour de la collerette (rayon coll_re + jeu_trou), outil de y0 (devant) à y1 (derrière) ; bord =
    abscisse du bord latéral de la plaque : s'il reste moins de 2 mm de matière, le trou s'ouvre sur ce bord (encoche en U,
    entrée R 1, comme le transpondeur). Le bord avant du trou (face y_face) est arrondi d'un congé de `arrondi` (Lou, 2026-10-27 :
    « le bord qui nous fait face » était vif). Contours et congé : aretes.encoche_u / contour_cercle / coupe."""
    from .. import aretes as AR
    R = A["coll_re"] + A["jeu_trou"]; rf = 1.0
    ouvert = bord is not None and abs(bord - x) - R < 2.0
    contour = (AR.encoche_u(R, abs(bord - x), math.copysign(1.0, bord - x), rf=rf, n=n) if ouvert
               else AR.contour_cercle(R, n=n))
    return AR.coupe(contour, y0, y1, conge=min(arrondi, rf - 0.05), y_face=y_face, cx=x, cz=z)


# ------------------------------------------------------------------ vis à fleur (fraisée, cruciforme)
def vis_fleur(x, z, y_face, a, V=VIS_FLEUR):
    """Tête fraisée 90° à fleur de y_face (face avant de la plaque), empreinte cruciforme tournée de a degrés :
    (maillage, [empreinte à retrancher])."""
    r, k, rs = V["tete_r"], V["tete_k"], V["vis_d"] / 2
    # dessus plat à fleur, bord arrondi de 0,2 (quart de cercle ; Lou : arêtes trop vives), liseré cylindrique jusqu'à 0,3, cône 90°,
    # puis l'amorce de la tige
    ra = 0.2
    # dessus = une seule face plane (un éventail de triangles depuis le centre marquait des traînées en étoile à l'ombrage)
    prof = [(0.0, r - ra)] + [(-ra + ra * math.cos(math.pi / 2 * i / 6), r - ra + ra * math.sin(math.pi / 2 * i / 6))
                              for i in range(1, 7)]
    prof += [(-0.3, r), (-0.3 - (r - rs), rs), (-k, rs), (-k, 0.0)]
    bm = revolution(prof, x, z, y_face)
    return bm, [empreinte_croix(x, z, y_face, V["croix"], a)]


def fraisage(x, z, y_face, V=VIS_FLEUR):
    """Fraisage 90° de la plaque pour une vis à fleur (jeu V['jeu']), arête du bord arrondie (quart de cercle), prolongé par le
    passage : outil à retrancher."""
    R = V["tete_r"] + V["jeu"]; ra = V["arrondi"]; rp = V["r_passage"]
    prof = [(1.0, 0.0), (1.0, R + ra + 1.0), (0.0, R + ra + 1.0)]
    prof += [(-ra + ra * math.cos(math.pi / 2 * i / 6), R + ra - ra * math.sin(math.pi / 2 * i / 6)) for i in range(7)]   # congé
    prof += [(-ra - (R - rp), rp), (-ra - (R - rp) - 3.0, rp), (-ra - (R - rp) - 3.0, 0.0)]   # cône 90° depuis le congé, passage
    return revolution(prof, x, z, y_face)


# ------------------------------------------------------------------ autres têtes du commerce
def tete_bombee(x, z, y_appui, d=3, a=0.0, norme="ISO 7045"):
    """Tête bombée cruciforme ISO 7045 posée en y_appui : flanc droit puis dôme de rayon rf jusqu'à k, dessous cassé de 0,1 :
    (maillage, [empreinte])."""
    c = N.cotes(norme, d); r, k, rf = c["dk"] / 2, c["k"], c["rf"]
    a0 = math.asin(r / rf)                                       # le dôme rejoint le flanc à k - rf (1 - cos a0)
    prof = [(0.0, 0.0), (0.0, r - 0.1), (0.1, r)]
    prof += [(k - rf + rf * math.cos(a0 * (1 - i / 10)), rf * math.sin(a0 * (1 - i / 10))) for i in range(10)] + [(k, 0.0)]
    bm = revolution(prof, x, z, y_appui)
    return bm, [empreinte_croix(x, z, y_appui - k, N.croix_rendu(norme, d), a)]


def tete_btr(x, z, y_appui, d=3, a=0.0, norme="ISO 4762"):
    """Tête cylindrique à six pans creux ISO 4762 posée en y_appui : bord du dessus arrondi (0,08 dk), dessous cassé ;
    (maillage, [six pans creux, fond conique à 118°])."""
    c = N.cotes(norme, d); r, k, s, t = c["dk"] / 2, c["k"], c["s"], c["t"]
    ch = round(0.08 * c["dk"], 2)
    prof = [(0.0, 0.0), (0.0, r - 0.1), (0.1, r), (k - ch, r)] + _quart(k, r, ch, 4)[1:] + [(k, 0.0)]
    bm = revolution(prof, x, z, y_appui)
    hx = hexagone(s, a); yd = y_appui - k
    outil = bmesh.new()
    haut = [outil.verts.new((x + u, yd - 1.0, z + v)) for u, v in hx]
    bas = [outil.verts.new((x + u, yd + t, z + v)) for u, v in hx]
    pointe = outil.verts.new((x, yd + t + (s / math.sqrt(3)) / math.tan(math.radians(59)), z))
    outil.faces.new(haut)
    for i in range(6):
        j = (i + 1) % 6; outil.faces.new((haut[i], haut[j], bas[j], bas[i])); outil.faces.new((bas[i], pointe, bas[j]))
    bmesh.ops.recalc_face_normals(outil, faces=outil.faces)
    return bm, [outil]


def tete(norme, d, x, z, y_appui, a=0.0):
    """Tête d'une vis du commerce par sa norme : (maillage, [outils à retrancher]).
    y_appui = plan sous la tête (cylindrique, bombée, BTR) ou, pour une fraisée, plan du dessus (à fleur) : la tige commence à
    y_appui pour les premières, à y_appui + k pour la fraisée (son cône est dans la tête)."""
    forme = N.cotes(norme, d)["forme"]
    if forme == "cylindrique_fendue":
        bm, o = tete_attache(x, z, y_appui, attache_cotes(d, norme), a)
    elif forme == "bombee_cruciforme":
        bm, o = tete_bombee(x, z, y_appui, d, a, norme)
    elif forme == "fraisee_cruciforme":
        bm, o = vis_fleur(x, z, y_appui, a, fleur_cotes(d, norme))
    elif forme == "btr":
        bm, o = tete_btr(x, z, y_appui, d, a, norme)
    else:
        raise ValueError(f"{norme} n'est pas une vis ({forme})")
    return bm, o
