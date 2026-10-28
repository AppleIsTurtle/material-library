r"""Lecteur de G-code d'OrcaSlicer (feature fdm-trajets, chunk-01) : Python système (numpy, Pillow).
    python gcode.py <plate.gcode> <dossier de sortie> [<n° de couche> …]
Écrit trajets.npz (un segment extrudé par ligne : couche, z, hauteur, largeur, type, x0, y0, x1, y1), bilan.json (par type :
segments, longueur, largeur moyenne ; coutures ; angles des lignes du dessus) et un PNG par couche demandée (défaut : première,
milieu, dernière + chaque couche qui contient du « Top surface »), cordons tracés à leur vraie largeur, une couleur par type.
Lit les commentaires d'Orca 2.4.2 : ;LAYER_CHANGE, ;Z:, ;HEIGHT:, ;TYPE:, ;WIDTH: ; extrusion relative (M83) ; arcs G2 / G3
(I, J) découpés en segments de ≤ 0,1 mm."""
import json, math, os, re, sys

import numpy as np

TYPES = ["Outer wall", "Inner wall", "Overhang wall", "Top surface", "Bottom surface", "Internal solid infill", "Sparse infill",
         "Bridge", "Internal Bridge", "Gap infill", "Skirt", "Brim", "Support", "Custom", "Ironing"]
COULEURS = {"Outer wall": (255, 140, 40), "Inner wall": (250, 220, 70), "Overhang wall": (230, 60, 60), "Top surface": (230, 70, 90),
            "Bottom surface": (110, 110, 240), "Internal solid infill": (160, 60, 200), "Sparse infill": (150, 40, 40),
            "Bridge": (80, 180, 220), "Internal Bridge": (60, 140, 190), "Gap infill": (40, 200, 120), "Ironing": (240, 240, 240)}
_mot = re.compile(r"([XYZEFIJ])(-?[\d.]+)")


def lire(chemin):
    """Segments extrudés du G-code : dict de tableaux numpy (une ligne par segment)."""
    seg = []; x = y = 0.0; couche = -1; z = h = w = 0.0; typ = "Custom"; rel = True
    for ligne in open(chemin, encoding="utf-8", errors="replace"):
        if ligne.startswith(";"):
            if ligne.startswith(";LAYER_CHANGE"): couche += 1
            elif ligne.startswith(";Z:"): z = float(ligne[3:])
            elif ligne.startswith(";HEIGHT:"): h = float(ligne[8:])
            elif ligne.startswith(";WIDTH:"): w = float(ligne[7:])
            elif ligne.startswith(";TYPE:"): typ = ligne[6:].strip()
            continue
        c = ligne.split(";")[0].strip()
        if not c: continue
        if c.startswith("M82"): rel = False
        elif c.startswith("M83"): rel = True
        if not c.startswith(("G0", "G1", "G2", "G3")): continue
        g = c.split()[0]; v = dict((k, float(n)) for k, n in _mot.findall(c))
        x1, y1 = v.get("X", x), v.get("Y", y)
        e = v.get("E", 0.0)
        if e > 0 and couche >= 0 and rel:
            pts = [(x, y), (x1, y1)]
            if g in ("G2", "G3") and "I" in v:
                cx, cy = x + v["I"], y + v.get("J", 0.0)
                a0, a1 = math.atan2(y - cy, x - cx), math.atan2(y1 - cy, x1 - cx)
                if g == "G3" and a1 <= a0: a1 += 2 * math.pi       # G3 : sens trigonométrique
                if g == "G2" and a1 >= a0: a1 -= 2 * math.pi       # G2 : sens horaire
                r = math.hypot(x - cx, y - cy); n = max(2, int(abs(a1 - a0) * r / 0.1) + 1)
                pts = [(cx + r * math.cos(a0 + (a1 - a0) * k / n), cy + r * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]
            ti = TYPES.index(typ) if typ in TYPES else len(TYPES)
            for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
                seg.append((couche, z, h, w, ti, xa, ya, xb, yb))
        x, y = x1, y1
    a = np.array(seg, dtype=np.float64)
    return dict(couche=a[:, 0].astype(int), z=a[:, 1], hauteur=a[:, 2], largeur=a[:, 3], type=a[:, 4].astype(int),
                x0=a[:, 5], y0=a[:, 6], x1=a[:, 7], y1=a[:, 8])


def bilan(t):
    """Par type : segments, longueur, largeur moyenne (pondérée par la longueur) ; coutures (début de chaque boucle de paroi
    extérieure : premier segment après un changement de type) ; angles des lignes du dessus (histogramme à 1°)."""
    L = np.hypot(t["x1"] - t["x0"], t["y1"] - t["y0"]); out = {"types": {}}
    for ti in np.unique(t["type"]):
        s = t["type"] == ti; nom = TYPES[ti] if ti < len(TYPES) else "autre"
        out["types"][nom] = dict(segments=int(s.sum()), longueur_mm=round(float(L[s].sum()), 1),
                                 largeur_moy=round(float((t["largeur"][s] * L[s]).sum() / max(L[s].sum(), 1e-9)), 4),
                                 couches=[int(t["couche"][s].min()), int(t["couche"][s].max())])
    saut = np.hypot(t["x0"][1:] - t["x1"][:-1], t["y0"][1:] - t["y1"][:-1]) > 0.01          # nouveau chemin (déplacement à vide)
    ow = TYPES.index("Outer wall"); debut = np.r_[True, (t["type"][1:] != t["type"][:-1]) | (t["couche"][1:] != t["couche"][:-1]) | saut]
    c = debut & (t["type"] == ow)
    out["coutures"] = [[int(k), round(float(a), 3), round(float(b), 3)] for k, a, b in zip(t["couche"][c], t["x0"][c], t["y0"][c])]
    ts = (t["type"] == TYPES.index("Top surface")) & (L > 1.0)
    if ts.any():
        ang = np.degrees(np.arctan2(t["y1"][ts] - t["y0"][ts], t["x1"][ts] - t["x0"][ts])) % 180
        hist = np.bincount(np.round(ang).astype(int) % 180, weights=L[ts], minlength=180)
        out["dessus_angles"] = {int(k): round(float(hist[k]), 1) for k in np.argsort(hist)[::-1][:3] if hist[k] > 0}
        pas = []                                            # pas des lignes du dessus : écart entre axes voisins, par couche
        for k in np.unique(t["couche"][ts]):
            s = ts & (t["couche"] == k); a0 = np.radians(np.argmax(np.bincount(np.round(ang[t["couche"][ts] == k]).astype(int) % 180)))
            off = np.sort(np.unique(np.round(-np.sin(a0) * (t["x0"][s] + t["x1"][s]) / 2 + np.cos(a0) * (t["y0"][s] + t["y1"][s]) / 2, 3)))
            dd = np.diff(off); dd = dd[(dd > 0.05) & (dd < 1.5)]
            if len(dd): pas.append(float(np.median(dd)))
        out["dessus_pas_mm"] = round(float(np.median(pas)), 4) if pas else None
    out["hauteurs"] = sorted({round(float(v), 3) for v in t["hauteur"]})
    out["couches"] = int(t["couche"].max()) + 1
    return out


def image_couche(t, k, px=40, marge=1.0, fond=(24, 24, 26), cadre=None):
    """Couche k tracée à `px` pixels par mm, cordons à leur largeur réelle (bouts ronds). cadre = (xmin, ymin, xmax, ymax) mm."""
    from PIL import Image, ImageDraw
    s = t["couche"] == k
    if cadre is None:
        tout = np.r_[t["x0"], t["x1"]], np.r_[t["y0"], t["y1"]]
        cadre = (tout[0].min() - marge, tout[1].min() - marge, tout[0].max() + marge, tout[1].max() + marge)
    x0, y0, x1, y1 = cadre
    W, H = int((x1 - x0) * px), int((y1 - y0) * px)
    im = Image.new("RGB", (W, H), fond); d = ImageDraw.Draw(im)
    P = lambda x, y: ((x - x0) * px, (y1 - y) * px)                   # y vers le haut, comme sur le plateau
    idx = np.where(s)[0]
    for i in idx:
        col = COULEURS.get(TYPES[t["type"][i]] if t["type"][i] < len(TYPES) else "", (200, 200, 200))
        a, b = P(t["x0"][i], t["y0"][i]), P(t["x1"][i], t["y1"][i]); r = t["largeur"][i] * px / 2
        d.line([a, b], fill=col, width=max(1, int(round(2 * r))))
        d.ellipse([b[0] - r, b[1] - r, b[0] + r, b[1] + r], fill=col)
    if px >= 20:                                       # axe de chaque cordon (sens du fil lisible au zoom)
        for i in idx:
            col = COULEURS.get(TYPES[t["type"][i]] if t["type"][i] < len(TYPES) else "", (200, 200, 200))
            d.line([P(t["x0"][i], t["y0"][i]), P(t["x1"][i], t["y1"][i])], fill=tuple(int(c * 0.45) for c in col),
                   width=max(1, px // 30))
    return im


if __name__ == "__main__":
    src, dest = sys.argv[1], sys.argv[2]; os.makedirs(dest, exist_ok=True)
    t = lire(src); np.savez_compressed(os.path.join(dest, "trajets.npz"), **t)
    b = bilan(t); json.dump(b, open(os.path.join(dest, "bilan.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    n = b["couches"]
    ks = [int(a) for a in sys.argv[3:]] or sorted({0, n // 2, n - 1} | set(np.unique(t["couche"][t["type"] == TYPES.index("Top surface")]).tolist()))
    for k in ks: image_couche(t, k).save(os.path.join(dest, f"couche_{k:03d}.png"))
    print(json.dumps(b["types"], ensure_ascii=False, indent=1)); print("coutures (10 premières)", b["coutures"][:10])
    print("angles du dessus", b.get("dessus_angles")); print("hauteurs", b["hauteurs"], "couches", n, "images", ks)
