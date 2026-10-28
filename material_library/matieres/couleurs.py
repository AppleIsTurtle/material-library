r"""Couleurs : conversions, pipette et compensation de la base d'une matière pour un studio (reprend MFS carte_pipette.py et la
méthode « couleurs vues par Lou », 2026-10-16 → 27).
La teinte visée (celle que Lou voit sur la vraie pièce, ou une norme : FS 595, RAL…) prime sur les photos de téléphone. Une matière
brillante ou satinée reflète le studio et s'éclaircit : on rend une pastille dans le studio, on mesure à la pipette (médiane hors
reflets et ombres), on corrige la base, jusqu'à ce que l'écart à la cible soit ≤ 3 par canal (sur 255). La base compensée
dépend donc du studio : chaque fiche du catalogue dit pour quel studio elle vaut.
mesurer() marche dans Blender (bpy) et hors Blender (Pillow)."""
import colorsys


def srgb(h):
    """'#rrggbb' → RGBA linéaire (pour Base Color)."""
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


def hexa(lin):
    """RGB linéaire → '#rrggbb'."""
    c = [min(max(x, 0.0), 1.0) for x in lin[:3]]
    c = [12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055 for x in c]
    return "#%02x%02x%02x" % tuple(round(x * 255) for x in c)


def octets(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ecart(h1, h2):
    """Plus grand écart par canal, sur 255."""
    return max(abs(a - b) for a, b in zip(octets(h1), octets(h2)))


def tsv(h):
    t, s, v = colorsys.rgb_to_hsv(*(x / 255 for x in octets(h))); return round(t * 360), round(s, 2), round(v, 2)


def _pixels(chemin):
    """Pixels RGB 0..1 (valeurs de l'image, donc après la vue AgX du rendu) : (hauteur, largeur, 3), ligne 0 en haut."""
    import numpy as np
    try:
        import bpy
        im = bpy.data.images.load(chemin, check_existing=False)
        w, h = im.size; a = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(a); bpy.data.images.remove(im)
        return a.reshape(h, w, 4)[::-1, :, :3]
    except ImportError:
        from PIL import Image
        return np.asarray(Image.open(chemin).convert("RGB"), np.float32) / 255


def mesurer(chemin, zone=(0.3, 0.3, 0.7, 0.7)):
    """Pipette : couleur médiane d'une zone (x0, y0, x1, y1 en fractions de l'image, y vers le bas), hors reflets et ombres
    (on ne garde que l'interquartile de luminance) → '#rrggbb'."""
    import numpy as np
    px = _pixels(chemin); H, W = px.shape[:2]
    x0, y0, x1, y1 = zone
    sel = px[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)].reshape(-1, 3)
    lum = sel @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    q = (lum >= np.quantile(lum, 0.25)) & (lum <= np.quantile(lum, 0.75))
    c = np.median(sel[q], 0)
    return "#%02x%02x%02x" % tuple(int(round(x * 255)) for x in c)


def corriger(base, mesure, cible, force=1.0):
    """Nouvelle base : chaque canal linéaire multiplié par (cible / mesure)^force (la vue du rendu est monotone : ça converge)."""
    b, m, c = srgb(base), srgb(mesure), srgb(cible)
    return hexa([bb * (max(cc, 1e-4) / max(mm, 1e-4)) ** force for bb, mm, cc in zip(b[:3], m[:3], c[:3])])


def compenser(base, cible, rendre_et_mesurer, tours=6, tolerance=3):
    """Boucle de compensation : rendre_et_mesurer(base) rend la pastille avec cette base et renvoie la teinte mesurée.
    → (base compensée, teinte mesurée, écart, historique [(base, mesure)])."""
    hist = []
    for _ in range(tours):
        mes = rendre_et_mesurer(base); hist.append((base, mes))
        if ecart(mes, cible) <= tolerance: break
        base = corriger(base, mes, cible)
    else:
        mes = hist[-1][1]; base = hist[-1][0]
    return base, mes, ecart(mes, cible), hist
