r"""Simulation du tranchage FDM d'une pièce (Snapmaker U1 de l'imprimeur FDM, PLA), calée sur OrcaSlicer 2.4.2 (feature fdm-trajets,
chunk-02 ; règles mesurées : methode/fdm_trajets.md). Python système : numpy, shapely — pas besoin d'Orca pour les rendus.
    python tranchage.py <sortie .npz> <buse 0.4|0.2> <pièce.stl> [<pièce.stl> …] [--plateau -Z] [--set clé=valeur …]
    from material_library.impression import tranchage as T ; t = T.trancher(triangles, T.reglages(0.4, parois=1))
Les STL d'une pièce sont tranchées d'un bloc (une matière). plateau = face de la pièce posée sur le plateau, dans le repère du
STL (« -Z » : déjà orientée, « -Y » : face avant d'une maquette…). Sortie : les trajets au format de outils/fdm/gcode.py (un
segment par ligne : couche, z, hauteur, largeur, type, x0, y0, x1, y1, dans le repère d'impression : z vers le haut, plateau à
z = 0) + `rotation` et `origine` (point p du STL → rotation @ p − origine), `tops` / `hauteurs` des couches et les réglages.
Ce qui est simulé (visible sur une pièce) : parois extérieure et intérieures autour du bord et de chaque trou, dessus de toute
couche non couverte par la suivante (une seule paroi, lignes monotones), face sur le plateau (première couche), plein interne
(lignes, pour la comparaison), ponts sous les zones sans appui, couture (alignée, arrière, aléatoire). Pas simulé : la largeur
variable d'Arachne (cordons d'une largeur fixe par type), les petits espaces, le remplissage clairsemé (invisible)."""
import json, math, os, struct, sys

import numpy as np
from shapely import affinity
from shapely.geometry import LineString, MultiLineString, Polygon, MultiPolygon, GeometryCollection
from shapely.ops import polygonize, unary_union

K = 1 - math.pi / 4                                    # écrasement du cordon : pas = largeur − hauteur × K (Slic3r)
TYPES = ["Outer wall", "Inner wall", "Overhang wall", "Top surface", "Bottom surface", "Internal solid infill", "Sparse infill",
         "Bridge", "Internal Bridge", "Gap infill", "Skirt", "Brim", "Support", "Custom", "Ironing"]    # = outils/fdm/gcode.py
# défauts du profil Snapmaker U1 d'OrcaSlicer 2.4.2 (« 0.20 Standard » buse 0,4 ; « 0.10 Standard » buse 0,2), relevés le 2026-10-27
DEFAUTS = {
    0.4: dict(couche=0.2, premiere=0.25, l_ext=0.42, l_int=0.45, l_dessus=0.42, l_plein=0.42, l_premiere=0.50, parois=2),
    0.2: dict(couche=0.1, premiere=0.10, l_ext=0.22, l_int=0.22, l_dessus=0.22, l_plein=0.22, l_premiere=0.25, parois=4)}
COMMUNS = dict(motif_dessus="monotone", angle=45.0, couture="alignee", une_paroi_dessus=True, recouvrement_plein=0.15,
               recouvrement_dessous=0.25, bout_dessus=0.77, pied_elephant=0.15, angle_pont=0.0, densite=0.15,
               aire_min_clairseme=15.0)
# coques pleines (couches, dessus compris) : profil U1 ; dessus = max(couches, épaisseur / couche) — 0,2 : max(7, 0,8 / 0,1) = 8
for b, (dessus, dessous) in ((0.4, (5, 3)), (0.2, (8, 5))):
    DEFAUTS[b].update(coque_dessus=dessus, coque_dessous=dessous)


def reglages(buse=0.4, **r):
    """Réglages complets : défauts de la buse + COMMUNS + r (parois=1, motif_dessus="concentrique", couture="arriere"…)."""
    d = dict(buse=buse, **DEFAUTS[buse], **COMMUNS); d.update(r)
    return d


# ------------------------------------------------------------------ géométrie
def lire_stl(chemin):
    d = open(chemin, "rb").read()
    if d[:5] == b"solid" and b"facet" in d[:300]:
        v = [list(map(float, l.split()[1:4])) for l in d.decode("ascii", "replace").splitlines() if l.strip().startswith("vertex")]
        return np.array(v).reshape(-1, 3, 3)
    n = struct.unpack("<I", d[80:84])[0]
    a = np.frombuffer(d[84:84 + 50 * n], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return a["v"].reshape(-1, 3, 3).astype(np.float64)


def rotation_plateau(plateau="-Z"):
    """Rotation qui amène la face `plateau` (normale ±X/Y/Z du repère du STL) vers le bas (−Z d'impression)."""
    s = -1.0 if plateau.startswith("-") else 1.0; i = "XYZ".index(plateau[-1].upper())
    d = np.zeros(3); d[i] = s                         # normale de la face posée
    v = np.cross(d, [0, 0, -1.0]); c = float(np.dot(d, [0, 0, -1.0]))
    if np.linalg.norm(v) < 1e-9:
        return np.eye(3) if c > 0 else np.diag([1.0, -1.0, -1.0])
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx / (1 + c)


def section(tri, z):
    """Section par le plan z : polygones (contours fermés, intérieur par pair-impair)."""
    d = tri[:, :, 2] - z
    sg = np.sign(d); sg[sg == 0] = 1
    coupe = (sg.min(1) < 0) & (sg.max(1) > 0)
    segs = []
    for t, dd in zip(tri[coupe], d[coupe]):
        pts = []
        for i, j in ((0, 1), (1, 2), (2, 0)):
            if (dd[i] < 0) != (dd[j] < 0):
                k = dd[i] / (dd[i] - dd[j]); p = t[i] + k * (t[j] - t[i]); pts.append((round(p[0], 6), round(p[1], 6)))
        if len(pts) == 2 and pts[0] != pts[1]: segs.append(LineString(pts))
    s = Polygon()
    for p in polygonize(unary_union(segs)): s = s.symmetric_difference(Polygon(p.exterior))
    return s.buffer(0)


def _polys(g):
    if g.is_empty: return []
    if isinstance(g, Polygon): return [g]
    return [p for p in getattr(g, "geoms", []) if isinstance(p, Polygon) and not p.is_empty]


def _anneaux(g):
    return [a for p in _polys(g) for a in [p.exterior] + list(p.interiors)]


# ------------------------------------------------------------------ trajets
class _Sortie:
    def __init__(self): self.l = []

    def chemin(self, xy, k, z, h, w, typ):
        xy = np.asarray(xy, float)
        if len(xy) < 2: return
        ti = TYPES.index(typ)
        for (a, b), (c, d) in zip(xy[:-1], xy[1:]): self.l.append((k, z, h, w, ti, a, b, c, d))


def _couture(anneau, prec, mode, rng):
    """Point de départ d'un contour : alignée = le coin le plus marqué (le plus proche de celui de la couche d'avant si le contour
    existait déjà), arrière = le point le plus en +y, aléatoire = un point au hasard. Rend l'indice du sommet."""
    c = np.array(anneau.coords)[:-1]
    if mode == "aleatoire": return int(rng.integers(len(c)))
    if mode == "arriere": return int(np.argmax(c[:, 1] - 1e-3 * c[:, 0]))
    if prec is not None:
        dist = np.hypot(c[:, 0] - prec[0], c[:, 1] - prec[1])
        if dist.min() < 1.0: return int(np.argmin(dist))
    a = np.roll(c, 1, 0) - c; b = np.roll(c, -1, 0) - c          # angle intérieur à chaque sommet : le plus fermé l'emporte
    cos = (a * b).sum(1) / np.maximum(np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1), 1e-12)
    # à égalité (contour lisse : trou rond, coins arrondis) : un côté en x, comme Orca (relevé sur l'embase : 0° ou 180°)
    xc = (c[:, 0].min() + c[:, 0].max()) / 2; ex = np.abs(c[:, 0] - xc) / max(np.ptp(c[:, 0]), 1e-9)
    return int(np.argmax(np.round(cos, 2) + 1e-3 * ex))


def _boucle(anneau, i0):
    c = np.array(anneau.coords)[:-1]
    c = np.roll(c, -i0, 0)
    return np.vstack([c, c[:1]])


def _lignes(zone, angle, pas, phase=0.0):
    """Lignes parallèles d'angle `angle` (°) au pas `pas` dans `zone`, alignées sur l'origine du repère (comme Orca) :
    liste de tableaux (2, 2), triés dans l'ordre de dépôt (monotone : d'un bord à l'autre)."""
    if zone.is_empty: return []
    r = affinity.rotate(zone, -angle, origin=(0, 0))
    x0, y0, x1, y1 = r.bounds
    rangs = []
    for j in range(int(math.floor((y0 - phase) / pas)), int(math.ceil((y1 - phase) / pas)) + 1):
        y = phase + j * pas
        g = r.intersection(LineString([(x0 - 1, y), (x1 + 1, y)]))
        rangs.append([np.array(s.coords)[[0, -1]] for s in getattr(g, "geoms", [g])
                      if isinstance(s, LineString) and s.length > 1e-3])
    # raccords (comme Orca) : le bout d'une ligne rejoint le bout le plus proche d'une ligne du rang suivant par un court
    # segment le long du bord, si ce raccord reste dans la zone ; sinon la chaîne s'arrête
    dedans = r.buffer(0.3 * pas); chaines, libres = [], [list(rg) for rg in rangs]
    for i in range(len(libres)):
        while libres[i]:
            ch = [libres[i].pop(0)]; pts = [ch[0][0], ch[0][1]]; ii = i
            while ii + 1 < len(libres) and libres[ii + 1]:
                fin = pts[-1]; d = [min(np.hypot(*(s[0] - fin)), np.hypot(*(s[1] - fin))) for s in libres[ii + 1]]
                m = int(np.argmin(d))
                if d[m] > 2.5 * pas: break
                s = libres[ii + 1][m]; s = s if np.hypot(*(s[0] - fin)) <= np.hypot(*(s[1] - fin)) else s[::-1]
                if not dedans.covers(LineString([fin, s[0]])): break
                libres[ii + 1].pop(m); pts += [s[0], s[1]]; ii += 1
            chaines.append(np.array(affinity.rotate(LineString(pts), angle, origin=(0, 0)).coords) if len(pts) > 1 else None)
    return [c for c in chaines if c is not None]


def _concentrique(zone, pas):
    out, z = [], zone
    while not z.is_empty:
        out += [np.array(a.coords) for a in _anneaux(z)]
        z = z.buffer(-pas, join_style="round")
    return out


def trancher(maillages, R, plateau="-Z", graine=1):
    """Trajets simulés d'une pièce avec les réglages R (reglages()). maillages : triangles (n, 3, 3) en mm (repère du STL), ou
    liste de ces tableaux (une par matière : chacun coupé à part puis réunis, une matière commune)."""
    if isinstance(maillages, np.ndarray): maillages = [maillages]
    rot = rotation_plateau(plateau)
    ms = [m @ rot.T for m in maillages]; z0 = min(m[:, :, 2].min() for m in ms); ms = [m - [0, 0, z0] for m in ms]
    H = max(m[:, :, 2].max() for m in ms); h0, h = R["premiere"], R["couche"]
    n = 1 + max(0, int(math.ceil((H - h0) / h - 1e-3)))           # dernière couche au-dessus du sommet (Orca : 8,45 pour 8,40)
    tops = [h0 + i * h for i in range(n)]; hs = [h0] + [h] * (n - 1)
    secs = [unary_union([section(m, min(zt - hh / 2, H - 1e-4)) for m in ms]).buffer(0.005, join_style="mitre")
            .buffer(-0.005, join_style="mitre") for zt, hh in zip(tops, hs)]           # referme les fentes entre matières
    expo_haut = [(secs[k].difference(secs[k + 1]) if k + 1 < n else secs[k]) for k in range(n)]       # vu d'en haut
    expo_bas = [secs[0]] + [secs[k].difference(secs[k - 1]) for k in range(1, n)]                    # vu d'en bas
    rng = np.random.default_rng(graine); S = _Sortie(); prec = []; creux_prec = Polygon()
    for k, (sec, zt, hh) in enumerate(zip(secs, tops, hs)):
        prem = k == 0
        if prem and R["pied_elephant"]: sec = sec.buffer(-R["pied_elephant"], join_style="mitre")
        if sec.is_empty: continue
        w_e = R["l_premiere"] if prem else R["l_ext"]; w_i = R["l_premiere"] if prem else R["l_int"]
        s_e, s_i = w_e - hh * K, w_i - hh * K
        dessus = sec.difference(secs[k + 1]) if k + 1 < n else sec            # zones vues d'en haut
        dessus = dessus.buffer(-0.05).buffer(0.05) if not dessus.is_empty else dessus
        if dessus.area < 0.01: dessus = Polygon()
        dessous = Polygon() if prem else sec.difference(secs[k - 1].buffer(0.05))   # zones sans appui (ponts)
        if not dessous.is_empty and dessous.area < 0.05: dessous = Polygon()
        # parois : axe extérieur à ½ largeur du bord (bord déjà compensé du pied d'éléphant à la 1re couche), puis un pas
        # d'écrasement par paroi intérieure ; sous un dessus, une seule paroi (une_paroi_dessus)
        offs = [w_e / 2] + [w_e / 2 + s_i * i for i in range(1, R["parois"])]
        plein = sec.buffer(-(offs[-1] + s_i / 2), join_style="mitre")         # bord de la zone intérieure (après les parois)
        zone_une = dessus if (R["une_paroi_dessus"] and not prem) else Polygon()
        coutures_k = []
        fins = [p for p in _polys(sec) if p.buffer(-w_e * 0.75).is_empty]          # parties trop fines pour deux tours :
        for p in fins:                                                             # un cordon central (Arachne), largeur adaptée
            r = p.minimum_rotated_rectangle; c = np.array(r.exterior.coords)[:4]
            e1, e2 = c[1] - c[0], c[2] - c[1]; lg, ep = (e1, e2) if np.linalg.norm(e1) >= np.linalg.norm(e2) else (e2, e1)
            m0 = c[0] + ep / 2                                                 # milieu du petit côté de départ
            w = float(np.clip(np.linalg.norm(ep), 0.5 * w_e, 2.0 * w_e)); u = lg / max(np.linalg.norm(lg), 1e-9)
            S.chemin([m0 + u * w / 2, m0 + lg - u * w / 2], k, zt, hh, w, "Outer wall"); coutures_k.append(m0)
        if fins: sec = sec.difference(unary_union(fins).buffer(1e-3))
        for a in _anneaux(sec.buffer(-offs[0], join_style="mitre")):
            j = _couture(a, _proche(prec, a) if R["couture"] == "alignee" else None, R["couture"], rng)
            b = _boucle(a, j); coutures_k.append(b[0]); S.chemin(b, k, zt, hh, w_e, "Outer wall")
        bande = sec.buffer(-(offs[0] + s_e / 2), join_style="mitre")             # dedans de la paroi extérieure
        for p in _polys(bande):                                                  # bande trop étroite pour une paroi entière :
            if p.buffer(-0.5 * s_i).is_empty and p.area > 0.05:                  # un cordon central à sa largeur (Arachne)
                r = p.minimum_rotated_rectangle; c = np.array(r.exterior.coords)[:4]
                e1, e2 = c[1] - c[0], c[2] - c[1]; lg, ep = (e1, e2) if np.linalg.norm(e1) >= np.linalg.norm(e2) else (e2, e1)
                w = float(np.clip(np.linalg.norm(ep) + hh * K, 0.3 * w_i, w_i)); m0 = c[0] + ep / 2; u = lg / max(np.linalg.norm(lg), 1e-9)
                S.chemin([m0 + u * w / 2, m0 + lg - u * w / 2], k, zt, hh, w, "Inner wall")
        for o in offs[1:]:
            g = sec.buffer(-o, join_style="mitre")
            if not zone_une.is_empty:                                          # anneaux coupés là où la couche est un dessus
                g = g.boundary.difference(zone_une.buffer(o))
                for s in getattr(g, "geoms", [g]):
                    if isinstance(s, LineString): S.chemin(np.array(s.coords), k, zt, hh, w_i, "Inner wall")
            else:
                for a in _anneaux(g): S.chemin(np.array(a.coords), k, zt, hh, w_i, "Inner wall")
        if not zone_une.is_empty:                                              # zone intérieure étendue sous le dessus
            plein = plein.union(sec.buffer(-(offs[0] + s_e / 2), join_style="mitre").intersection(zone_une.buffer(offs[-1])))
        prec = coutures_k
        ang = R["angle"] if k % 2 == 0 else (R["angle"] + 90.0) % 180.0          # alterne 45° / 135°
        if prem:                                                                  # face sur le plateau
            w = R["l_premiere"]; s = w - hh * K
            z_ = sec.buffer(-(offs[-1] + s_i / 2 + s / 2 - R["recouvrement_dessous"] * w), join_style="mitre")
            for ln in _lignes(z_, ang, s): S.chemin(ln, k, zt, hh, w, "Bottom surface")
            continue
        w = R["l_dessus"]; s_d = w - hh * K
        if not dessus.is_empty:                                                   # dessus : bouts à bout_dessus × w du bord
            z_ = sec.buffer(-R["bout_dessus"] * w, join_style="mitre").intersection(dessus.buffer(0.5 * w))
            lignes = _concentrique(z_, s_d) if R["motif_dessus"] == "concentrique" else _lignes(z_, ang, s_d)
            for ln in lignes: S.chemin(ln, k, zt, hh, w, "Top surface")
        reste = plein.difference(dessus.buffer(0.5 * w)) if not dessus.is_empty else plein
        if not dessous.is_empty:
            zp = dessous.intersection(sec.buffer(-w_e))
            for ln in _lignes(zp, R["angle_pont"], R["l_plein"] - hh * K): S.chemin(ln, k, zt, hh, R["l_plein"], "Bridge")
            reste = reste.difference(dessous)
        # coques : plein là où un dessus est à moins de coque_dessus couches au-dessus, ou le bas à moins de coque_dessous
        # couches au-dessous ; ailleurs remplissage clairsemé (invisible sur une pièce finie, gardé pour la comparaison)
        coque = unary_union([expo_haut[j] for j in range(k, min(n, k + R["coque_dessus"]))] +
                            [expo_bas[j] for j in range(max(0, k - R["coque_dessous"] + 1), k + 1)])
        petits = [p for p in _polys(reste.difference(coque.buffer(0.01))) if p.area < R["aire_min_clairseme"]]
        if petits: coque = unary_union([coque] + petits)                       # petites zones : plein (minimum_sparse_infill_area)
        w = R["l_plein"]; s_p = w - hh * K
        plein_k = reste.intersection(coque.buffer(0.01)) if not coque.is_empty else Polygon()
        if not plein_k.is_empty and not creux_prec.is_empty:                    # plein posé sur du clairsemé : pont interne
            pi = plein_k.intersection(creux_prec)
            if pi.area > 0.05:
                for ln in _lignes(pi, ang, R["buse"]): S.chemin(ln, k, zt, hh, R["buse"], "Internal Bridge")
                plein_k = plein_k.difference(pi)
        z_ = plein_k.buffer(-(s_p / 2 - R["recouvrement_plein"] * w), join_style="mitre") if not plein_k.is_empty else plein_k
        for ln in _lignes(z_, ang, s_p): S.chemin(ln, k, zt, hh, w, "Internal solid infill")
        creux = reste.difference(coque.buffer(0.01)) if not coque.is_empty else reste
        creux_prec = creux
        if not creux.is_empty and creux.area > 0.05:                            # croisé : deux couches à 45°, deux à 135°
            z_ = creux.buffer(-(s_p / 2 - R["recouvrement_plein"] * w), join_style="mitre")
            a_c = R["angle"] if (k // 2) % 2 == 0 else (R["angle"] + 90.0) % 180.0
            for ln in _lignes(z_, a_c, w / R["densite"]): S.chemin(ln, k, zt, hh, w, "Sparse infill")
    a = np.array(S.l, dtype=np.float64).reshape(-1, 9)
    return dict(couche=a[:, 0].astype(int), z=a[:, 1], hauteur=a[:, 2], largeur=a[:, 3], type=a[:, 4].astype(int),
                x0=a[:, 5], y0=a[:, 6], x1=a[:, 7], y1=a[:, 8], rotation=rot, origine=np.array([0.0, 0.0, z0]),
                tops=np.array(tops), hauteurs=np.array(hs), reglages=json.dumps(R))


def _proche(prec, anneau):
    """Couture de la couche d'avant la plus proche de ce contour (alignement d'une couche à l'autre)."""
    if not prec: return None
    c = np.array(anneau.coords)
    d = [np.hypot(c[:, 0] - p[0], c[:, 1] - p[1]).min() for p in prec]
    i = int(np.argmin(d))
    return prec[i] if d[i] < 1.0 else None


def _valeur(v):
    try: return float(v)
    except ValueError: return {"true": True, "false": False}.get(v.lower(), v)


if __name__ == "__main__":
    a = sys.argv[1:]; reg = {}; plateau = "-Z"
    if "--set" in a:
        i = a.index("--set"); reg = {k: _valeur(v) for k, v in (kv.split("=", 1) for kv in a[i + 1:])}; a = a[:i]
    if "--plateau" in a:
        i = a.index("--plateau"); plateau = a[i + 1]; del a[i:i + 2]
    if "parois" in reg: reg["parois"] = int(reg["parois"])
    t = trancher([lire_stl(p) for p in a[2:]], reglages(float(a[1]), **reg), plateau)
    np.savez_compressed(a[0], **t)
    print(f"{a[0]} : {t['couche'].max() + 1} couches, {len(t['couche'])} segments")
