# material_library.conception.supports — supports de bureau clipsés (pose inclinée), repris tels quels de MFS
# (boitier/scripts/supports.py, 2026-10-27 ; la maquette du F-COM2 l'utilise encore jusqu'à la migration, chunk-09) ; en plus, à
# la fin : profil du clipsage en queue d'aronde (repris de maquette_grand_format.py) et construire(), qui pose les deux supports
# et leurs patins sous un caisson quelconque. Méthode : methode/conception_boitier.md, étape 6.
# Historique MFS : supports de bureau « armature » du boîtier v3 PCB (chunk-00g) — géométrie 2D (vue de dessus) partagée par
# build_boitier.py (pièces à imprimer) et maquette_ailerons.py (exploration).
# Épaisseur : SUP_T de build_boitier.py (3,5). Contour = enveloppe convexe de 2 coins avant (R_CORNER) et d'une pointe ronde (TIP_R) ; bandes de largeur W le long des
# 3 côtés droits, raccordées entre elles et aux nœuds (avant plein qui porte le tenon et le patin avant, fond du jour
# arrière autour du patin arrière) par un minimum lissé (smooth-min, rayon K), puis recoupées par l'enveloppe → raccords
# fluides à l'intérieur, contour net. Contour extrait par marching squares, puis maillé à pas régulier (maillage_regulier).
# Coordonnées locales : x depuis le flanc du boîtier vers l'intérieur, y vers l'arrière (0 = face avant de la façade).
import math
import numpy as np

DEFAUTS = dict(
    BASE=33.0, D=42.0,            # largeur de la base, profondeur (depuis la face avant de la façade)
    Y_FRONT=3.2,                  # début du support : juste derrière la façade (dos de façade à y = 3)
    W=2.6, K=3.0,                 # largeur des bandes ; rayon de raccord
    HUB_Y1=18.5, HUB_X1=21.0, HUB_R=2.0,   # avant plein jusqu'à y (sous le tenon) et x (au-delà : 2e jour) ; coin arrondi
    TIRANT=True,                  # bande (largeur W) du coin de l'avant plein à la bande diagonale : sépare les 2 jours (Lou)
    TIP_R=6.0, TIP_CLR=5.5,       # pointe arrière (patin Ø8,3 → 1,85 de paroi) ; matière pleine autour du patin arrière
    R_CORNER=1.6,                 # coins avant du contour
    PAD_FRONT=(6.0, 8.5),         # patin avant, 1,85 du bord (le patin arrière est au centre de la pointe)
    GRID=0.12,                    # pas du champ (mm)
    PAS=0.4,                      # pas du maillage (mm) : longueur d'arête visée partout (topologie régulière)
    # --- boîtier incliné (chunk-00i) : le contour ci-dessus est l'EMPREINTE SUR LE BUREAU (vue de dessus) ; le dessus du
    #     support = plan du fond du caisson, incliné de TILT (angle ajouté par build_boitier.py) → cale, plus épaisse devant ;
    #     il rejoint le dessus plat de l'empreinte arrière (épaisseur z1 - z0) par un raccord lisse (max lissé, largeur
    #     BLEND). Y_KINK : y (repère du caisson) où le plan du caisson atteint cette épaisseur — derrière le caisson (18) ;
    #     BLEND assez petit pour que le raccord commence derrière le tenon (qui finit à 17,5 + 0,25 de contention)
    Y_KINK=20.0, BLEND=0.6,
)

def _seg(X, Y, a, b, r):
    ax, ay = a; bx, by = b; px, py = X - ax, Y - ay; ex, ey = bx - ax, by - ay
    h = np.clip((px * ex + py * ey) / (ex * ex + ey * ey), 0, 1)
    return np.hypot(px - ex * h, py - ey * h) - r

def _smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)

def _poly(X, Y, poly):
    d = np.full(X.shape, np.inf); inside = np.zeros(X.shape, bool); n = len(poly)
    for k in range(n):
        (ax, ay), (bx, by) = poly[k], poly[(k + 1) % n]
        d = np.minimum(d, _seg(X, Y, (ax, ay), (bx, by), 0.0))
        cond = (ay > Y) != (by > Y)
        xint = ax + (Y - ay) * (bx - ax) / np.where(by - ay == 0, 1e-12, by - ay)
        inside ^= cond & (X < xint)
    return np.where(inside, -d, d)

def _hull(circles, seg=48):
    pts = sorted({(round(cx + r * math.cos(2 * math.pi * k / seg), 6), round(cy + r * math.sin(2 * math.pi * k / seg), 6))
                  for cx, cy, r in circles for k in range(seg)})
    def half(P):
        h = []
        for p in P:
            while len(h) >= 2 and (h[-1][0] - h[-2][0]) * (p[1] - h[-2][1]) - (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0]) <= 0:
                h.pop()
            h.append(p)
        return h
    lo, up = half(pts), half(pts[::-1])
    return lo[:-1] + up[:-1]

def champ(A):
    """Champ de distance signé (négatif = matière) sur une grille ; renvoie xs, ys, F, centre de la pointe."""
    g = A["GRID"]; xs = np.arange(-2.0, A["BASE"] + 2.0, g); ys = np.arange(-2.0, A["D"] + 2.0, g)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    rc, R, w2, y0 = A["R_CORNER"], A["TIP_R"], A["W"] / 2, A["Y_FRONT"]
    tip = (R, A["D"] - R)
    hull = _hull([(rc, y0 + rc, rc), (A["BASE"] - rc, y0 + rc, rc), (tip[0], tip[1], R)])
    hullf = _poly(X, Y, hull)
    f = np.full(X.shape, 1e3); n = len(hull)
    for k in range(n):                                     # bandes le long des côtés droits de l'enveloppe
        (px, py), (qx, qy) = hull[k], hull[(k + 1) % n]
        L = math.hypot(qx - px, qy - py)
        if L < 3.0: continue
        ex, ey = (qx - px) / L, (qy - py) / L; nx, ny = -ey * w2, ex * w2   # normale intérieure (sens trigo)
        f = _smin(f, _seg(X, Y, (px + nx, py + ny), (qx + nx, qy + ny), w2), A["K"])
    # avant plein = traverse entre les 2 jours ; coin (HUB_X1, HUB_Y1) arrondi de HUB_R (pas d'angle vif, même en plan)
    if A["HUB_X1"]:
        rr = A["HUB_R"]; qx, qy = X - A["HUB_X1"] + rr, Y - A["HUB_Y1"] + rr
        coin = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - rr
    else:
        coin = Y - A["HUB_Y1"]
    front = np.maximum(hullf, coin)
    f = _smin(f, front, A["K"])
    if A["TIRANT"] and A["HUB_X1"]:   # tirant : du centre du coin arrondi, perpendiculaire à la bande diagonale
        diag = [(hull[k], hull[(k + 1) % n]) for k in range(n)]
        diag = max((c for c in diag if min(abs(c[1][0] - c[0][0]), abs(c[1][1] - c[0][1])) > 3.0),
                   key=lambda c: math.hypot(c[1][0] - c[0][0], c[1][1] - c[0][1]))
        (px, py), (qx, qy) = diag; L = math.hypot(qx - px, qy - py); ex, ey = (qx - px) / L, (qy - py) / L
        hx, hy = A["HUB_X1"] - A["HUB_R"], A["HUB_Y1"] - A["HUB_R"]
        t = (hx - px) * ex + (hy - py) * ey
        fx, fy = px + ex * t - ey * w2, py + ey * t + ex * w2        # pied sur l'axe de la bande (normale intérieure)
        f = _smin(f, _seg(X, Y, (hx, hy), (fx, fy), w2), A["K"])
    ux, uy = A["BASE"] / 2 - tip[0], A["HUB_Y1"] - tip[1]; L = math.hypot(ux, uy); ux, uy = ux / L, uy / L
    f = _smin(f, np.maximum(hullf, (X - tip[0]) * ux + (Y - tip[1]) * uy - A["TIP_CLR"]), A["K"])   # fond du jour arrière
    return xs, ys, np.maximum(f, hullf), tip

def contour(xs, ys, f):
    """Marching squares : points (x, y) sur les arêtes de la grille (partagés entre cellules) et segments du contour f = 0."""
    ins = f < 0
    c = ins[:-1, :-1].astype(int) + 2 * ins[1:, :-1] + 4 * ins[1:, 1:] + 8 * ins[:-1, 1:]
    T = {1: [(3, 0)], 2: [(0, 1)], 3: [(3, 1)], 4: [(1, 2)], 5: [(3, 0), (1, 2)], 6: [(0, 2)], 7: [(3, 2)],
         8: [(2, 3)], 9: [(0, 2)], 10: [(0, 1), (2, 3)], 11: [(1, 2)], 12: [(1, 3)], 13: [(0, 1)], 14: [(3, 0)]}
    pts, idx, segs = [], {}, []
    def vert(key):
        if key not in idx:
            kind, i, j = key
            (i0, j0), (i1, j1) = ((i, j), (i + 1, j)) if kind == 'h' else ((i, j), (i, j + 1))
            f0, f1 = f[i0, j0], f[i1, j1]; t = f0 / (f0 - f1)
            idx[key] = len(pts); pts.append((xs[i0] + (xs[i1] - xs[i0]) * t, ys[j0] + (ys[j1] - ys[j0]) * t))
        return idx[key]
    for i, j in zip(*np.nonzero((c > 0) & (c < 15))):
        e = [('h', i, j), ('v', i + 1, j), ('h', i, j + 1), ('v', i, j)]
        for u, v in T[int(c[i, j])]: segs.append((vert(e[u]), vert(e[v])))
    return pts, segs

def _etapes(f, n=6, print_side=False):
    """Profil d'arrondi (décalage vers l'intérieur, hauteur) de rayon f ; print_side : départ à 45° (face sur le plateau)."""
    pts, a0 = [], 0.0
    if print_side:
        pts.append((f * (2 - math.sqrt(2)), 0.0)); a0 = 45.0
    for k in range(n + 1):
        th = math.radians(a0 + (90 - a0) * k / n)
        pts.append((f * (1 - math.sin(th)), f * (1 - math.cos(th))))
    return pts

def _normales(xs, ys, f):
    """Normale extérieure unitaire du champ (gradient interpolé) en un point (x, y)."""
    g = xs[1] - xs[0]; gx, gy = np.gradient(f, g, g)
    def normale(x, y):
        i = min(max((x - xs[0]) / g, 0), len(xs) - 2); j = min(max((y - ys[0]) / g, 0), len(ys) - 2)
        i0, j0 = int(i), int(j); u, v = i - i0, j - j0
        def bil(A): return (A[i0, j0] * (1 - u) * (1 - v) + A[i0 + 1, j0] * u * (1 - v) + A[i0, j0 + 1] * (1 - u) * v
                            + A[i0 + 1, j0 + 1] * u * v)
        nx, ny = bil(gx), bil(gy); L = math.hypot(nx, ny) or 1.0
        return nx / L, ny / L                       # vers l'extérieur (le champ croît vers l'extérieur)
    return normale

def _boucles(pts, segs):
    """Segments du marching squares → boucles fermées (points confondus soudés : nœud de grille partagé par 2 arêtes)."""
    key, P, remap = {}, [], []
    for (x, y) in pts:
        k = (round(x, 4), round(y, 4))
        if k not in key: key[k] = len(P); P.append((x, y))
        remap.append(key[k])
    adj = {}
    for a, b in {tuple(sorted((remap[a], remap[b]))) for a, b in segs if remap[a] != remap[b]}:
        adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    assert all(len(v) == 2 for v in adj.values()), "contour non manifold"
    vus, boucles = set(), []
    for s in adj:
        if s in vus: continue
        loop, prev, cur = [P[s]], s, adj[s][0]; vus.add(s)
        while cur != s:
            loop.append(P[cur]); vus.add(cur)
            a, b = adj[cur]; prev, cur = cur, (b if a == prev else a)
        boucles.append(loop)
    return boucles

def _reechantillonne(loop, h):
    """Boucle fermée → points également espacés (≈ h) le long de l'abscisse curviligne."""
    P = np.array(loop + loop[:1]); s = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    n = max(8, int(round(s[-1] / h))); t = np.arange(n) * s[-1] / n
    return list(zip(np.interp(t, s, P[:, 0]), np.interp(t, s, P[:, 1])))

def _pas(L, h, g=0.0):
    """Abscisses de 0 à L (incluses) au pas ≈ h ; g > 0 : g et L - g en plus (arêtes de contention) si la place le permet."""
    if g and L >= 2 * g + 0.05:
        m = max(1, int(round((L - 2 * g) / h)))
        return [0.0] + [g + (L - 2 * g) * i / m for i in range(m + 1)] + [L]
    c = max(1, int(round(L / h)))
    return [L * i / c for i in range(c + 1)]

def _subdivise(poly, h, g=0.0):
    """Polygone fermé → chaque côté coupé en segments ≈ h (sommets gardés, contention à g des sommets) ; renvoie aussi
    l'indice du 1er point de chaque côté."""
    out, debuts, n = [], [], len(poly)
    for k in range(n):
        (ax, ay), (bx, by) = poly[k], poly[(k + 1) % n]
        L = math.hypot(bx - ax, by - ay); debuts.append(len(out))
        out += [(ax + (bx - ax) * s / L, ay + (by - ay) * s / L) for s in _pas(L, h, g)[:-1]]
    return out, debuts

def _decale(P, g):
    """Boucle fermée décalée de g vers l'intérieur (sens quelconque) : onglet aux sommets, décalage perpendiculaire pour
    les points pris sur un côté ; points confondus (contention à g d'un angle droit) rendus identiques."""
    n = len(P); A = sum(P[i][0] * P[(i + 1) % n][1] - P[(i + 1) % n][0] * P[i][1] for i in range(n))
    sg = 1 if A > 0 else -1; out = []
    def nrm(a, b):
        L = math.hypot(b[0] - a[0], b[1] - a[1]); return (-(b[1] - a[1]) / L * sg, (b[0] - a[0]) / L * sg)
    for i in range(n):
        n1, n2 = nrm(P[i - 1], P[i]), nrm(P[i], P[(i + 1) % n])
        mx, my = n1[0] + n2[0], n1[1] + n2[1]; Lm = math.hypot(mx, my); mx, my = mx / Lm, my / Lm
        k = g / max(mx * n1[0] + my * n1[1], 1e-3)
        out.append((P[i][0] + mx * k, P[i][1] + my * k))
    for i in range(n):
        if math.dist(out[i], out[i - 1]) < 1e-6: out[i] = out[i - 1]
    return out

def _uniques(P):
    """Boucle sans points consécutifs confondus."""
    return [p for i, p in enumerate(P) if p != P[i - 1]]

def _dedans(Q, boucles):
    """Points Q (n, 2) à l'intérieur de la région délimitée par les boucles (règle pair-impair : trous compris)."""
    A = np.concatenate([np.array(L, float) for L in boucles])
    B = np.concatenate([np.roll(np.array(L, float), -1, 0) for L in boucles])
    ax, ay, bx, by = A[:, 0], A[:, 1], B[:, 0], B[:, 1]; out = np.zeros(len(Q), bool)
    for k in range(0, len(Q), 2000):
        x, y = Q[k:k + 2000, :1], Q[k:k + 2000, 1:]
        xi = ax + (y - ay) * (bx - ax) / np.where(by == ay, 1e-12, by - ay)
        out[k:k + 2000] = ((((ay > y) != (by > y)) & (x < xi)).sum(1) % 2) == 1
    return out

def _couvercle(boucles, h, relax=3):
    """Face plane à triangles réguliers (≈ équilatéraux, côté h) : points des boucles gardés tels quels (arêtes
    contraintes), intérieur semé en réseau hexagonal, Delaunay contraint, puis quelques passes de relaxation (chaque point
    intérieur vers le centre de ses voisins). Renvoie les points 2D et les triangles (indices)."""
    from mathutils import Vector
    from mathutils.geometry import delaunay_2d_cdt
    C = np.concatenate([np.array(L, float) for L in boucles]); nc = len(C)
    (x0, y0), (x1, y1) = C.min(0), C.max(0); dy = h * math.sqrt(3) / 2
    Q = np.array([(x0 + (i + 0.5 * (j % 2)) * h, y0 + j * dy)
                  for j in range(int((y1 - y0) / dy) + 2) for i in range(int((x1 - x0) / h) + 2)])
    Q = Q[_dedans(Q, boucles)]
    keep = np.ones(len(Q), bool)
    for k in range(0, len(Q), 2000):
        q = Q[k:k + 2000]
        keep[k:k + 2000] = np.hypot(q[:, None, 0] - C[None, :, 0], q[:, None, 1] - C[None, :, 1]).min(1) > 0.7 * h
    Q = Q[keep]
    E, o = [], 0
    for L in boucles:
        n = len(L); E += [(o + k, o + (k + 1) % n) for k in range(n)]; o += n
    for it in range(relax + 1):
        V = np.concatenate([C, Q]) if len(Q) else C
        _, _, fo, orig, _, _ = delaunay_2d_cdt([Vector(p) for p in V], E, [], 0, 1e-7)
        idx = [ov[0] for ov in orig]
        T = np.array([[idx[i] for i in f] for f in fo if len(f) == 3])
        e1, e2 = V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]   # sans les lamelles plates de l'enveloppe convexe
        T = T[(np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]) > 1e-3 * h * h) & _dedans(V[T].mean(1), boucles)]
        if it == relax or not len(Q): return V, T
        S = np.zeros_like(V); cnt = np.zeros(len(V))
        for a, b in ((0, 1), (1, 2), (2, 0)):        # somme des voisins (arête intérieure vue 2 fois : même poids partout)
            np.add.at(S, T[:, a], V[T[:, b]]); np.add.at(cnt, T[:, a], 1)
            np.add.at(S, T[:, b], V[T[:, a]]); np.add.at(cnt, T[:, b], 1)
        Q = 0.5 * Q + 0.5 * S[nc:] / np.maximum(cnt[nc:, None], 1)

def repere_bureau(z0, z1, incl=None):
    """Repère « bureau » S (fond du support plat à zs = 0, empreinte = contour) ↔ repère du caisson C (dessus du support =
    plan z = z1 du caisson). C → S : rotation de TILT autour de x, pivot en y = Y_KINK sur le plan du dessus ; y de S choisi
    pour que le devant du support (Y_FRONT) ne bouge pas. Renvoie c2s, s2c (x, y, z) → (x, y, z), Z1 (hauteur du dessus en
    S selon y : plan du caisson raccordé au plat arrière de hauteur z1 - z0), Tt = z1 - z0, zc = z1."""
    incl = incl or {}
    th = math.radians(incl.get("TILT", 0.0)); cs, sn = math.cos(th), math.sin(th)
    yk, kb, yf = incl.get("Y_KINK", 0.0), incl.get("BLEND", 0.6), incl.get("Y_FRONT", 0.0)
    Tt, zc = z1 - z0, z1
    Y0 = yf + (yk - yf) * cs                        # y (S) du point du plan de dessus de y (C) = Y_KINK
    def c2s(x, y, z):
        dy, dz = y - yk, z - zc
        return (x, Y0 + dy * cs + dz * sn, Tt - dy * sn + dz * cs)
    def s2c(x, y, z):
        u, v = y - Y0, z - Tt
        return (x, yk + u * cs - v * sn, zc + u * sn + v * cs)
    def Z1(y):                                      # dessus (repère S) : plan du caisson, raccord lisse (max polynomial) au plat
        if sn < 1e-9: return Tt
        a = Tt + (Y0 - y) * math.tan(th); hh = max(kb - abs(a - Tt), 0.0) / kb
        return max(a, Tt) + hh * hh * kb / 4
    return c2s, s2c, Z1, Tt, zc

def maillage_regulier(bm, xs, ys, f, pts, segs, z0, z1, r, xy, h, tenon=None, poches=(), c=0.05, ca=0.25, incl=None):
    """Support complet en un seul maillage régulier (arêtes ≈ h partout, sans booléen qui recouperait la topologie) :
    - contour rééchantillonné à pas h ; flancs = anneaux du contour décalés vers l'intérieur le long de la normale du champ
      (valable : rayons de la forme ≥ R_CORNER > r), arêtes haut et bas arrondies de r (bas imprimable : départ à 45°),
      anneaux espacés d'≈ h sur les arrondis comme sur la partie droite ;
    - dessus et dessous en triangles ≈ équilatéraux (_couvercle) ;
    - tenon = (profil (x, z) fermé dont le 1er côté est la base posée sur le dessus à z = z1, y0, y1) ;
    - poches (cx, cy, rayon, profondeur) ouvertes sous le support ;
    - arêtes de contention (ombrage lisse sans traînée sur les faces planes) : boucle à c du départ à 45° du dessous (des
      deux côtés) et du bord du dessus ; à ca (= adoucissement + c) de chaque arête adoucie du tenon et des poches.
    Points partagés soudés par coordonnées → pièce étanche. xy : repère local → monde (miroir pour le support droit).
    Boîtier incliné (chunk-00i) : tout est construit dans le repère « bureau » S (fond plat à zs = 0, flancs verticaux, poches
    d'aplomb, empreinte = contour), sauf le tenon (profil et plage de y donnés dans le repère du caisson, plan du dessus z1) ;
    le dessus suit le plan du caisson, incliné de incl["TILT"], puis se raccorde au dessus plat arrière (épaisseur z1 - z0) ;
    à la fin, rotation S → repère du caisson (autour de x). incl = dict(TILT °, Y_FRONT, Y_KINK, BLEND) ; None ou TILT 0 : plat."""
    import bmesh
    from mathutils import Vector
    c2s, s2c, Z1, Tt, zc = repere_bureau(z0, z1, incl)
    z0, z1 = 0.0, Tt                                # tout le reste dans le repère S
    normale = _normales(xs, ys, f)
    contours = [_reechantillonne(L, h) for L in _boucles(pts, segs)]
    N = [[normale(x, y) for x, y in L] for L in contours]
    nb, nt = max(1, round(math.pi / 4 * r / h)), max(1, round(math.pi / 2 * r / h))
    # flanc droit : pas ≈ h sur le dessus plat ; sous un boîtier incliné le flanc est plus haut devant (jusqu'à Z1 max) :
    # même nombre d'anneaux partout, pas ≈ 1,4 h au plus haut (≈ 0,15 au plus bas)
    hmax = max(Z1(y) for L in contours for _, y in L)
    nw = max(1, round((z1 - z0 - 2 * r) / h), round((hmax - z0 - 2 * r) / (1.4 * h)))
    bas = _etapes(r, nb, True); (d0, t0), (d1, t1) = bas[0], bas[1]; L01 = math.hypot(d1 - d0, t1 - t0)
    bas.insert(1, (d0 + (d1 - d0) * c / L01, t0 + (t1 - t0) * c / L01))     # contention sur le chanfrein à 45°
    # anneaux (décalage d, genre, valeur) : 'b' = z0 + t ; 'm' = flanc droit, k-ième des nw pas ; 't' = Z1(y) - t (hauteur
    # du dessus au point de l'anneau : le dessus n'est pas plat sous un boîtier incliné)
    anneaux = ([(d, 'b', t) for d, t in bas] + [(0.0, 'm', k) for k in range(1, nw)]
               + [(d, 't', t) for d, t in reversed(_etapes(r, nt))])
    def hauteur(g, v, y):
        return z0 + v if g == 'b' else z0 + r + (Z1(y) - z0 - 2 * r) * v / nw if g == 'm' else Z1(y) - v
    VV = {}
    def V(x, y, z):
        k = (round(x, 5), round(y, 5), round(z, 5))
        if k not in VV: VV[k] = bm.verts.new((*xy(x, y), z))
        return VV[k]
    def face(vs):                                    # sommets confondus retirés, triangles plats sautés (coins des contentions)
        u = []
        for v in vs:
            if v not in u: u.append(v)
        if len(u) == 3 and (u[1].co - u[0].co).cross(u[2].co - u[0].co).length < 1e-9: return
        if len(u) >= 3: bm.faces.new(u)
    def bande(A_, B_):                               # quads entre 2 boucles 3D de même nombre de points
        n = len(A_)
        for k in range(n): face((V(*A_[k]), V(*A_[(k + 1) % n]), V(*B_[(k + 1) % n]), V(*B_[k])))
    def plan(boucles, to3d):
        P2, T = _couvercle([_uniques(L) for L in boucles], h)
        for t in T: face([V(*to3d(*P2[i])) for i in t])
    def anneau(d):
        return [[(x - nx * d, y - ny * d) for (x, y), (nx, ny) in zip(L, NL)] for L, NL in zip(contours, N)]
    def a3(L, z):                                    # z : nombre ou fonction de y
        return [(x, y, z(y) if callable(z) else z) for x, y in L]
    for L, NL in zip(contours, N):                   # flancs arrondis
        R = [[(x - nx * d, y - ny * d, hauteur(g, v, y - ny * d if g == 't' else y)) for (x, y), (nx, ny) in zip(L, NL)]
             for d, g, v in anneaux]
        for a, b in zip(R, R[1:]): bande(a, b)
    bord = set(VV.values())                          # sommets des flancs (déjà arrondis)
    # dessous : contention à c du départ à 45°, poches des patins (paroi, fond, contentions à ca des arêtes adoucies)
    for A_, B_ in zip(anneau(d0), anneau(d0 + c)): bande(a3(A_, z0), a3(B_, z0))
    trous = []
    for cx, cy, rp, prof in poches:
        n = max(8, round(2 * math.pi * rp / h))
        def cercle(R_): return [(cx + R_ * math.cos(2 * math.pi * k / n), cy + R_ * math.sin(2 * math.pi * k / n)) for k in range(n)]
        zs = [z0 + t for t in _pas(prof, h, ca)]
        for za, zb in zip(zs, zs[1:]): bande(a3(cercle(rp), za), a3(cercle(rp), zb))
        bande(a3(cercle(rp), zs[-1]), a3(cercle(rp - ca), zs[-1])); plan([cercle(rp - ca)], lambda u, v: (u, v, zs[-1]))
        bande(a3(cercle(rp), z0), a3(cercle(rp + ca), z0)); trous.append(cercle(rp + ca))
    plan(anneau(d0 + c) + trous, lambda u, v: (u, v, z0))
    # dessus : contention à c du bord (départ de l'arrondi)
    rt = anneaux[-1][0]
    for A_, B_ in zip(anneau(rt), anneau(rt + c)): bande(a3(A_, Z1), a3(B_, Z1))
    dessus = anneau(rt + c); reduits = {}
    if tenon:
        prof, ty0, ty1 = tenon                       # profil (x, z) et plage de y : repère du caisson (plan du dessus z = zc)
        Vc = lambda x, y, z: V(*c2s(x, y, z))
        Pp, deb = _subdivise(prof, h, ca); nbase = deb[1]
        ty = [ty0 + t for t in _pas(ty1 - ty0, h, ca)]
        chaine = Pp[nbase:] + Pp[:1]                 # du coin de base droit au coin de base gauche, par le haut
        for ya, yb in zip(ty, ty[1:]):
            for (ua, va), (ub, vb) in zip(chaine, chaine[1:]):
                face((Vc(ua, ya, va), Vc(ub, ya, vb), Vc(ub, yb, vb), Vc(ua, yb, va)))
        Pi = _decale(Pp, ca)                         # bouts du tenon : contention à ca du bord
        for yy in (ty0, ty1):
            bande([c2s(u, yy, v) for u, v in Pp], [c2s(u, yy, v) for u, v in Pi])
            plan([Pi], lambda u, v, yy=yy: c2s(u, yy, v))
        base = Pp[:nbase + 1]; xa, xb = base[0][0], base[-1][0]
        tys = [c2s(0.0, y, zc)[1] for y in ty]       # le pied du tenon, dans le plan du dessus (repère S)
        y0t, y1t = tys[0], tys[-1]
        rect = ([(u, y0t) for u, _ in base] + [(xb, y) for y in tys[1:-1]]
                + [(u, y1t) for u, _ in reversed(base)] + [(xa, y) for y in reversed(tys[1:-1])])
        # contention autour du pied du tenon, à ca de chaque côté — sauf là où il n'y a pas la place avant le bord du dessus
        # (bout arrière : 0,2 avant l'arrondi du jour) ; là, l'adoucissement est réduit à la place disponible (poids < 1)
        Bd = np.concatenate([np.array(L) for L in dessus])
        def place(p, q):
            S_ = np.array(p) + (np.array(q) - np.array(p)) * np.linspace(0, 1, 20)[:, None]
            return np.hypot(S_[:, None, 0] - Bd[None, :, 0], S_[:, None, 1] - Bd[None, :, 1]).min()
        cotes = {"G": ((xa, y0t), (xa, y1t)), "D": ((xb, y0t), (xb, y1t)), "Av": ((xa, y0t), (xb, y0t)), "Ar": ((xa, y1t), (xb, y1t))}
        gap = {k: place(*v) for k, v in cotes.items()}
        o_ = {k: ca if g_ > ca + 0.5 * h else 0.0 for k, g_ in gap.items()}
        oG, oD, oAv, oAr = o_["G"], o_["D"], o_["Av"], o_["Ar"]
        rext = [(u - oG if abs(u - xa) < 1e-9 else u + oD if abs(u - xb) < 1e-9 else u,
                 v - oAv if abs(v - y0t) < 1e-9 else v + oAr if abs(v - y1t) < 1e-9 else v) for u, v in rect]
        bande(a3(rect, Z1), a3(rext, Z1))
        for i in range(len(rect)):                   # arêtes du pied sans place : poids réduit
            (pu, pv), (qu, qv) = rect[i], rect[(i + 1) % len(rect)]
            k = ("G" if abs(pu - xa) + abs(qu - xa) < 1e-9 else "D" if abs(pu - xb) + abs(qu - xb) < 1e-9 else
                 "Av" if abs(pv - y0t) + abs(qv - y0t) < 1e-9 else "Ar" if abs(pv - y1t) + abs(qv - y1t) < 1e-9 else None)
            if k and not o_[k]:
                reduits[frozenset((V(pu, pv, Z1(pv)), V(qu, qv, Z1(qv))))] = min(1.0, max(0.1, (gap[k] - c) / (ca - c)))
        if reduits:                                  # même largeur sur tous ces côtés (sinon arête vive au coin commun)
            wmin = min(reduits.values()); reduits = {k: wmin for k in reduits}
        n = len(rect); bord_t = []                   # bord du dessus : repasse par le coin quand un côté n'a pas de contention
        for i in range(n):
            dec, dec_av, dec_ap = rext[i] != rect[i], rext[i - 1] != rect[i - 1], rext[(i + 1) % n] != rect[(i + 1) % n]
            if dec and not dec_av: bord_t.append(rect[i])
            bord_t.append(rext[i])
            if dec and not dec_ap: bord_t.append(rect[i])
        dessus.append(bord_t)
    plan(dessus, lambda u, v: (u, v, Z1(v)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # poids de bevel = arêtes à adoucir (modificateur « adoucissement » limité par poids) : arêtes vives (> 40°) du tenon
    # et des poches ; pas celles des flancs (départ à 45° du dessous : l'ancien contour dense bloquait déjà le bevel là,
    # le garder intact garde la surface au plateau)
    bw = bm.edges.layers.float.get("bevel_weight_edge") or bm.edges.layers.float.new("bevel_weight_edge")
    for e in bm.edges:
        if not (e.verts[0] in bord and e.verts[1] in bord) and e.calc_face_angle(0.0) > math.radians(40):
            e[bw] = reduits.get(frozenset(e.verts), 1.0)
    for v in bm.verts: v.co = Vector(s2c(*v.co))     # repère S → repère du caisson
    return bm

def geometrie(overrides=None):
    """Contour du support (repère local) + positions des patins."""
    A = dict(DEFAUTS); A.update(overrides or {})
    xs, ys, F, tip = champ(A)
    pts, segs = contour(xs, ys, F)
    return A, pts, segs, (A["PAD_FRONT"], tip), (xs, ys, F)


# ============================================================ ajouts material-library (2026-10-27)
# Supports du F-COM2 et du transpondeur (communs aux deux) : cotes du F-COM1 × 1,6, dessus incliné de 15° (MFS,
# maquette_grand_format.py P["SUP"]) ; pour un autre caisson on garde ces cotes tant que sa largeur est voisine (≈ 145).
SUPPORT_PANNEAU = dict(BASE=52.8, D=66.0, W=4.2, K=4.8, HUB_Y1=29.6, HUB_X1=33.6, HUB_R=3.2, TIP_R=9.6, TIP_CLR=8.8,
                       R_CORNER=2.5, PAD_FRONT=(9.6, 13.6), GRID=0.15, PAS=0.5, BLEND=1.0)
POSE = dict(INCL=15.0, SUP_T=4.5, SUP_EDGE=1.0, PAD_D=8.0, PAD_H=2.8, PAD_SINK=1.0, PAD_CLR=0.2)
# clipsage du F-COM1 (validé en commande test JLC3DP) : rainure femelle en queue d'aronde dans le fond du caisson, ouverte au dos,
# à X du flanc ; tenon sur le dessus du support ; jeux CLR_X / CLR_Z, nervures d'écrasement ECR sur les pans verticaux (dessin de
# fabrication) ; renfort intérieur RIB_HW × RIB_TOP au-dessus de la rainure ; chanfrein de la bouche et entrée évasée au dos
# (Lou, 2026-10-26 : pas d'arête vive au clipsage)
CLIPSAGE = dict(X=23.2, MOUTH=4.9, DEPTH=3.0, RELIEF=0.6, LIP=1.0, CLR_X=0.3, CLR_Z=0.25, RIB_HW=7.5, RIB_TOP=6.0, ECR=0.15,
                CH_BOUCHE=0.5, CH_ENTREE=0.6)


def queue_aronde(xc, z0, a, d, r, lip):
    """Profil (x, z) de queue d'aronde à 45°, goulot 2a en z0, hauteur d : plat vertical « lip » au goulot et pan vertical r en
    haut ; aile de chaque côté : d - lip - r."""
    e = d - lip - r
    return [(xc - a, z0), (xc + a, z0), (xc + a, z0 + lip), (xc + a + e, z0 + d - r), (xc + a + e, z0 + d),
            (xc - a - e, z0 + d), (xc - a - e, z0 + d - r), (xc - a, z0 + lip)]


def profil_rainure(xc, z_fond, off=0.0, cl=CLIPSAGE):
    """Profil (x, z) de la rainure creusée dans le fond du caisson (fond extérieur à z_fond), élargi de `off` (entrée évasée),
    chanfrein CH_BOUCHE à 45° sur les lèvres ; même nombre de points quel que soit off (pour un loft)."""
    z0, a, d, r, lip = z_fond - 0.05, cl["MOUTH"] + off, cl["DEPTH"] + 0.05 + off, cl["RELIEF"], cl["LIP"] + 0.05
    e = cl["DEPTH"] - cl["LIP"] - cl["RELIEF"]; c = cl["CH_BOUCHE"] + 0.05
    return [(xc - a - c, z0), (xc + a + c, z0), (xc + a, z0 + c), (xc + a, z0 + lip), (xc + a + e, z0 + d - r), (xc + a + e, z0 + d),
            (xc - a - e, z0 + d), (xc - a - e, z0 + d - r), (xc - a, z0 + lip), (xc - a, z0 + c)]


def _patin(bm, rp, h):
    """Patin 3M (dôme) d'axe z, dôme vers le bas, base en z = 0."""
    profil = [(0.0, rp), (h * 0.45, rp), (h * 0.8, rp - 0.9), (h * 0.95, rp - min(2.3, rp * 0.45))]
    n = 64; anneaux = [[bm.verts.new((r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), -t)) for i in range(n)]
                       for t, r in profil]
    for a, b in zip(anneaux, anneaux[1:]):
        for i in range(n): bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    bm.faces.new(list(reversed(anneaux[0])))
    pv = bm.verts.new((0.0, 0.0, -h))
    for i in range(n): bm.faces.new((anneaux[-1][(i + 1) % n], anneaux[-1][i], pv))
    import bmesh
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


def construire(coll, parent, prefixe, largeur, z_fond, y_dos_facade, y_dos_caisson, y_butee, matiere, matiere_patin,
               dims=None, pose=None, cl=CLIPSAGE):
    """Les deux supports clipsés et leurs patins sous un caisson de `largeur` (x centré), fond extérieur à z = z_fond, façade
    de dos à y_dos_facade, dos du caisson à y_dos_caisson ; tenon de y_butee + 0,3 (butée de la rainure) jusque sous l'avant
    plein. Objets <prefixe>SUPPORT_G / _D et <prefixe>PATIN_SUP_<i>_<j> ; renvoie (supports, patins, pose) : pose =
    dict(rotation, location) à donner à la racine du boîtier pour le poser incliné sur ses supports (patins sur z = 0).
    Repère : x à droite, y vers l'arrière, z en haut, mm (celui des maquettes)."""
    import bpy, bmesh
    from mathutils import Matrix, Vector
    dims = dict(SUPPORT_PANNEAU, **(dims or {})); pose = dict(POSE, **(pose or {}))
    A, pts, segs, pads, (xs, ys, F) = geometrie(dict(dims, Y_FRONT=y_dos_facade + 0.2, Y_KINK=y_dos_caisson + 1.5))
    z1 = z_fond - 0.02; z0 = z1 - pose["SUP_T"]
    incl = dict(TILT=pose["INCL"], Y_FRONT=A["Y_FRONT"], Y_KINK=A["Y_KINK"], BLEND=A["BLEND"])
    c2s, s2c, *_ = repere_bureau(z0, z1, incl)
    o = Vector(s2c(0, 0, 0)); m_s2c = Matrix((Vector(s2c(1, 0, 0)) - o, Vector(s2c(0, 1, 0)) - o,
                                              Vector(s2c(0, 0, 1)) - o)).transposed().to_4x4(); m_s2c.translation = o
    tenon = (queue_aronde(cl["X"], z1, cl["MOUTH"] - cl["CLR_X"], cl["DEPTH"] - cl["CLR_Z"], cl["RELIEF"], cl["LIP"]),
             y_butee + 0.3, A["HUB_Y1"] - 0.5)
    supports, patins = [], []
    def objet(nom, bm, mats, lisse):
        me = bpy.data.meshes.new(nom); bm.to_mesh(me); bm.free()
        for m in mats: me.materials.append(m)
        me.shade_smooth(); me.set_sharp_from_angle(angle=math.radians(lisse))
        ob = bpy.data.objects.new(nom, me); coll.objects.link(ob); ob.parent = parent
        return ob
    for sx in (-1, 1):
        xy = (lambda x, y: (-largeur / 2 + x, y)) if sx < 0 else (lambda x, y: (largeur / 2 - x, y))
        poches = [(px, py, pose["PAD_D"] / 2 + pose["PAD_CLR"], pose["PAD_SINK"]) for px, py in pads]
        sup = objet(f"{prefixe}SUPPORT_{'G' if sx < 0 else 'D'}",
                    maillage_regulier(bmesh.new(), xs, ys, F, pts, segs, z0, z1, pose["SUP_EDGE"], xy, A["PAS"], tenon, poches,
                                      incl=incl), [matiere], 40)
        bv = sup.modifiers.new("adoucissement", "BEVEL"); bv.limit_method = "WEIGHT"; bv.width = 0.4; bv.segments = 3
        bm = bmesh.new(); bm.from_mesh(sup.data)        # sommets confondus du maillage (arêtes ouvertes au tenon)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-3); bmesh.ops.dissolve_degenerate(bm, dist=1e-4, edges=bm.edges)
        bm.to_mesh(sup.data); bm.free()
        supports.append(sup)
        for j, (px, py) in enumerate(pads):
            cx, cy = xy(px, py)
            bm = bmesh.new(); _patin(bm, pose["PAD_D"] / 2, pose["PAD_H"])
            bmesh.ops.translate(bm, verts=bm.verts, vec=(cx, cy, pose["PAD_SINK"]))      # repère bureau S
            pad = objet(f"{prefixe}PATIN_SUP_{len(supports)}_{j}", bm, [matiere_patin], 35)
            pad.data.transform(m_s2c)                                                  # S → caisson
            patins.append(pad)
    t = c2s(0.0, 0.0, 0.0)
    pose_racine = dict(rotation=(-math.radians(pose["INCL"]), 0.0, 0.0), location=(0.0, t[1], t[2] + pose["PAD_H"] - pose["PAD_SINK"]))
    return supports, patins, pose_racine
