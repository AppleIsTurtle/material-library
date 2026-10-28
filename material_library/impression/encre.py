# Encre imprimée (Lou, 2026-10-26 : « les écritures sont imprimées, un peu baveuses, pas parfaitement imprimées ») : à partir d'un
# masque net (texte, sérigraphie), l'aspect d'une impression réelle — l'encre s'étale un peu (bords adoucis et gonflés), le bord
# suit le grain du support (irrégulier à ~0,1 mm), l'épaisseur varie (zones plus pâles), quelques micro-manques dans les aplats.
# PIL + numpy seulement (Python système ou de KiCad : texte.py, calques.py). Masque et résultat : images « L ».
# Repris de MFS boitier/scripts/encre.py (2026-10-26), material-library chunk-04.
import numpy as np
from PIL import Image, ImageFilter


def _bruit(shape, cellule_px, rng):
    """Bruit lisse dans [−1, 1] à cellules de `cellule_px` pixels (grille aléatoire agrandie en bicubique)."""
    h, w = shape
    gh, gw = max(2, int(h / cellule_px) + 3), max(2, int(w / cellule_px) + 3)
    g = Image.fromarray(((rng.random((gh, gw)) * 255).astype(np.uint8)), "L")
    g = g.resize((int(gw * cellule_px), int(gh * cellule_px)), Image.BICUBIC)
    a = np.asarray(g, dtype=np.float32)[:h, :w] / 127.5 - 1.0
    return a


def effet(masque, px_mm, etalement=0.03, bord=0.10, pale=0.12, trous=0.6, graine=7):
    """masque (Image L, 255 = encre) → Image L de l'encre imprimée. etalement : étalement de l'encre (mm) ; bord : amplitude de
    l'irrégularité du bord ; pale : variation d'épaisseur (0..1) ; trous : micro-manques par mm² d'aplat."""
    rng = np.random.default_rng(graine)
    s = max(etalement * px_mm, 0.6)
    a = np.asarray(masque.filter(ImageFilter.GaussianBlur(s)), dtype=np.float32) / 255.0
    n1 = _bruit(a.shape, 0.12 * px_mm, rng); n2 = _bruit(a.shape, 0.035 * px_mm, rng)
    seuil = 0.45 + bord * n1 + 0.5 * bord * n2                  # < 0,5 : l'encre gagne un peu sur le bord (elle bave)
    lis = 0.05
    t = np.clip((a - (seuil - lis)) / (2 * lis), 0.0, 1.0); t = t * t * (3 - 2 * t)
    t *= 1.0 - pale * (0.5 + 0.5 * _bruit(a.shape, 0.4 * px_mm, rng))          # épaisseur qui varie
    if trous > 0:                                                # micro-manques (bulles, poussière) dans les aplats
        h, w = a.shape; n = int(trous * h * w / (px_mm * px_mm))
        ys, xs = rng.integers(0, h, n), rng.integers(0, w, n)
        im = Image.new("L", (w, h), 0); from PIL import ImageDraw; d = ImageDraw.Draw(im)
        for y, x in zip(ys, xs):
            r = rng.uniform(0.006, 0.02) * px_mm
            d.ellipse((x - r, y - r, x + r, y + r), fill=int(rng.uniform(120, 255)))
        tr = np.asarray(im.filter(ImageFilter.GaussianBlur(0.5)), dtype=np.float32) / 255.0
        t *= 1.0 - tr * (a > 0.9)
    return Image.fromarray((np.clip(t, 0, 1) * 255).astype(np.uint8), "L")
