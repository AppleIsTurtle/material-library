r"""Cartes de rendu des cordons FDM (feature fdm-trajets, chunk-03) : Python système (numpy, scipy, Pillow).
    python cartes.py <cuisson.npz> <trajets.npz> <sortie.npz>
cuisson.npz : P (position) et N (normale) de chaque texel dans le repère de l'objet (cuits par procedes.trajets dans Blender),
masque des texels utiles. trajets.npz : sortie de tranchage.py (repère d'impression + rotation / origine).
Sortie : `hauteur` (mm, ≤ 0 : creux entre cordons, sur les dessus, les dessous et aux coutures) et `fil` (direction du fil, repère
de l'objet, pour l'anisotropie du reflet), de la taille de la cuisson. Les couches des tranches ne sont PAS dans la carte : le
shader les calcule (nettes à toute résolution) ; la carte n'y ajoute que les coutures.
Profil d'un cordon : demi-ellipse (largeur réelle du trajet, hauteur de la couche), cordons voisins qui se recouvrent (le creux
entre deux cordons vient de leur pas d'écrasement) ; relief réduit sur les dessus (la buse lisse le haut du cordon) et sur la
face du plateau (cordon écrasé sur le PEI)."""
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.spatial import cKDTree

TYPES = ["Outer wall", "Inner wall", "Overhang wall", "Top surface", "Bottom surface", "Internal solid infill", "Sparse infill",
         "Bridge", "Internal Bridge", "Gap infill", "Skirt", "Brim", "Support", "Custom", "Ironing"]
RELIEF = dict(dessus=0.16, plateau=0.035, dessous=0.30)   # creux entre cordons, en part de la hauteur de couche
COUTURE = 0.18                                            # bourrelet de couture, en part de la hauteur de couche
NORMALE = 0.70                                            # |n.z| au-delà : face de dessus / dessous ; en deçà : tranche


def _trame(t, sel, cadre, pas):
    """Axes des segments `sel` tracés sur une grille (indice du segment + 1), puis segment le plus proche de chaque case."""
    x0, y0, x1, y1 = cadre
    W, H = int(np.ceil((x1 - x0) / pas)) + 1, int(np.ceil((y1 - y0) / pas)) + 1
    im = Image.new("I", (W, H), 0); d = ImageDraw.Draw(im)
    for i in np.where(sel)[0]:
        d.line([((t["x0"][i] - x0) / pas, (t["y0"][i] - y0) / pas), ((t["x1"][i] - x0) / pas, (t["y1"][i] - y0) / pas)],
               fill=int(i) + 1, width=1)
    lab = np.asarray(im, dtype=np.int64)
    if not lab.any(): return None
    _, (iy, ix) = ndimage.distance_transform_edt(lab == 0, return_indices=True)
    return lab[iy, ix] - 1                                  # (H, W) : indice du segment le plus proche


def _distance_segment(px, py, t, idx):
    """Distance exacte du point (px, py) au segment idx et direction unitaire du segment."""
    ax, ay, bx, by = t["x0"][idx], t["y0"][idx], t["x1"][idx], t["y1"][idx]
    dx, dy = bx - ax, by - ay; L2 = np.maximum(dx * dx + dy * dy, 1e-12)
    u = np.clip(((px - ax) * dx + (py - ay) * dy) / L2, 0, 1)
    d = np.hypot(px - (ax + u * dx), py - (ay + u * dy)); L = np.sqrt(L2)
    return d, dx / L, dy / L


def cartes(P, N, masque, t):
    R = np.asarray(t["rotation"]); org = np.asarray(t["origine"])
    tops, hs = np.asarray(t["tops"]), np.asarray(t["hauteurs"])
    q = P @ R.T - org; nq = N @ R.T
    hauteur = np.zeros(P.shape[:-1], np.float32); fil = np.zeros(P.shape, np.float32)
    rng = np.random.default_rng(5); var = rng.normal(0, 0.06, len(t["x0"]))            # cordons un peu inégaux
    pas_trame = float(np.min(t["largeur"][t["largeur"] > 0])) / 5
    vis = (t["type"] != TYPES.index("Sparse infill")) & (t["type"] != TYPES.index("Internal Bridge"))
    nz = nq[..., 2]
    classes = (("dessus", masque & (nz > NORMALE), tops), ("dessous", masque & (nz < -NORMALE), tops - hs))
    for nom, sel_t, ref in classes:
        k = np.abs(q[..., 2][..., None] - ref[None, None, :]).argmin(-1) if sel_t.any() else None
        for kk in (np.unique(k[sel_t]) if sel_t.any() else []):
            m = sel_t & (k == kk)
            s = vis & (t["couche"] == kk)
            if not s.any(): continue
            px, py = q[..., 0][m], q[..., 1][m]
            cadre = (px.min() - 1, py.min() - 1, px.max() + 1, py.max() + 1)
            idx_g = _trame(t, s, cadre, pas_trame)
            if idx_g is None: continue
            fx, fy = (px - cadre[0]) / pas_trame, (py - cadre[1]) / pas_trame
            best = None                                    # 9 cases voisines : le segment vraiment le plus proche (pas de dents)
            for ox in (-1, 0, 1):
                for oy in (-1, 0, 1):
                    ix = np.clip(np.round(fx).astype(int) + ox, 0, idx_g.shape[1] - 1)
                    iy = np.clip(np.round(fy).astype(int) + oy, 0, idx_g.shape[0] - 1)
                    i_ = idx_g[iy, ix]; r_ = _distance_segment(px, py, t, i_)
                    if best is None: best = (i_, *r_)
                    else:
                        mieux = r_[0] < best[1]
                        best = tuple(np.where(mieux, a, b) for a, b in zip((i_, *r_), best))
            idx, d, ux, uy = best
            x = d / (0.5 * t["largeur"][idx] * (1 + var[idx]))
            prof = np.sqrt(np.clip(1 - x * x, 0, 1))                                 # 1 au milieu du cordon, 0 au bord
            rel = RELIEF["plateau"] if (nom == "dessous" and kk == 0) else RELIEF[nom]
            hauteur[m] = (rel * hs[kk] * (prof - 1)).astype(np.float32)
            v = np.stack([ux, uy, np.zeros_like(ux)], -1) @ R                         # direction du fil → repère de l'objet
            fil[m] = v
    # tranches : direction du fil = horizontale le long du contour ; bourrelet aux coutures (début de chaque paroi extérieure)
    tr = masque & (np.abs(nz) <= NORMALE)
    if tr.any():
        h_ = np.cross(nq[tr], [0.0, 0.0, 1.0]); h_ /= np.maximum(np.linalg.norm(h_, axis=1, keepdims=True), 1e-9)
        fil[tr] = h_ @ R
        ow = TYPES.index("Outer wall")
        saut = np.r_[True, (np.hypot(t["x0"][1:] - t["x1"][:-1], t["y0"][1:] - t["y1"][:-1]) > 0.01) |
                     (t["type"][1:] != t["type"][:-1]) | (t["couche"][1:] != t["couche"][:-1])]
        c = saut & (t["type"] == ow)
        kq = np.clip(np.searchsorted(tops, q[..., 2][tr] - 1e-6), 0, len(tops) - 1)
        ht = np.zeros(tr.sum(), np.float32); pts = np.stack([q[..., 0][tr], q[..., 1][tr]], -1)
        for kk in np.unique(kq):
            cs = c & (t["couche"] == kk)
            if not cs.any(): continue
            arbre = cKDTree(np.stack([t["x0"][cs], t["y0"][cs]], -1)); w = t["largeur"][cs].mean()
            sel = kq == kk; d, _ = arbre.query(pts[sel])
            d = np.maximum(d - 0.5 * w, 0)                                             # le point est sur l'axe, la tranche à ½ largeur
            ht[sel] = COUTURE * hs[kk] * np.exp(-(d / (0.6 * w)) ** 2)
        hauteur[tr] = ht
    return hauteur, fil


if __name__ == "__main__":
    c = np.load(sys.argv[1]); t = dict(np.load(sys.argv[2], allow_pickle=True))
    h, f = cartes(c["P"], c["N"], c["masque"], t)
    np.savez_compressed(sys.argv[3], hauteur=h, fil=f)
    print(f"cartes {h.shape} : creux {h.min():.4f} mm, coutures {h.max():.4f} mm", flush=True)
