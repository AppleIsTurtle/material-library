r"""Compare nos trajets simulés (material_library/impression/tranchage.py) aux vrais trajets d'OrcaSlicer (feature fdm-trajets,
chunk-02) : Python système (numpy, shapely, Pillow).
    python comparer.py <dossier Orca (trancher.py + gcode.py)> <nos trajets .npz> <dossier de sortie> [<zoom xmin,ymin,xmax,ymax>]
Nos trajets sont déplacés comme Orca a déplacé la pièce sur le plateau (reglages.json). Écrit ecarts.json et superposition_<k>.png
(rouge : Orca seul, vert : nous seuls, jaune : les deux) pour la première couche, une couche courante et la dernière. Seuils
(plan du chunk-02) : pas et largeur du dessus ± 5 %, angle ± 1°, mêmes couches, couverture de chaque couche ± 2 %."""
import json, os, sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gcode as G

PX = 20                                                # px / mm des masques de couverture
VISIBLES = ("Outer wall", "Inner wall", "Top surface", "Bottom surface", "Internal solid infill", "Sparse infill", "Bridge",
            "Internal Bridge")
VUS = ("Outer wall", "Top surface", "Bottom surface", "Bridge")      # ce qui se voit d'une pièce finie (tranches, dessus, plateau)


def charger(orca, nous):
    o = dict(np.load(os.path.join(orca, "lecture", "trajets.npz")))
    n = dict(np.load(nous, allow_pickle=True)); dep = json.load(open(os.path.join(orca, "reglages.json")))["deplacement"]
    for c in ("x0", "x1"): n[c] = n[c] + dep[0]
    for c in ("y0", "y1"): n[c] = n[c] + dep[1]
    return o, n


def masque(t, k, cadre, types=None):
    s = t["couche"] == k
    if types is not None: s &= np.isin(t["type"], [G.TYPES.index(x) for x in types])
    u = {c: t[c][s] for c in ("couche", "type", "largeur", "x0", "y0", "x1", "y1")}
    im = G.image_couche(u, k, px=PX, cadre=cadre, fond=(0, 0, 0)) if s.any() else None
    W, H = int((cadre[2] - cadre[0]) * PX), int((cadre[3] - cadre[1]) * PX)
    return np.asarray(im).max(2) > 0 if im is not None else np.zeros((H, W), bool)


def ecarts(o, n):
    bo, bn = G.bilan(o), G.bilan(n)
    e = {"couches": [bo["couches"], bn["couches"]], "hauteurs": [bo["hauteurs"], bn["hauteurs"]], "types": {}}
    for ty in VISIBLES:
        a, b = bo["types"].get(ty), bn["types"].get(ty)
        if a or b:
            e["types"][ty] = dict(longueur=[a and a["longueur_mm"], b and b["longueur_mm"]],
                                  largeur=[a and a["largeur_moy"], b and b["largeur_moy"]],
                                  rapport_longueur=round(b["longueur_mm"] / a["longueur_mm"], 3) if a and b else None)
    e["dessus_pas"] = [bo.get("dessus_pas_mm"), bn.get("dessus_pas_mm")]
    e["dessus_angles"] = [bo.get("dessus_angles"), bn.get("dessus_angles")]
    # coutures : pour chaque couture d'Orca, distance à la nôtre la plus proche, même couche
    co, cn = np.array(bo["coutures"]), np.array(bn["coutures"])
    if len(co) and len(cn):
        d = [np.hypot(cn[cn[:, 0] == k][:, 1] - x, cn[cn[:, 0] == k][:, 2] - y).min() if (cn[:, 0] == k).any() else np.nan
             for k, x, y in co]
        e["coutures_mm"] = dict(mediane=round(float(np.nanmedian(d)), 3), part_sous_1mm=round(float(np.nanmean(np.array(d) < 1.0)), 3))
    # couverture par couche (toutes extrusions visibles) et IoU
    tout = np.r_[o["x0"], o["x1"]], np.r_[o["y0"], o["y1"]]
    cadre = (tout[0].min() - 1, tout[1].min() - 1, tout[0].max() + 1, tout[1].max() + 1)
    for cle, types in (("couverture", VISIBLES), ("couverture_visible", VUS)):
        cv = []
        for k in range(min(bo["couches"], bn["couches"])):
            mo, mn = masque(o, k, cadre, types), masque(n, k, cadre, types)
            if not (mo.any() or mn.any()): continue
            cv.append((k, round(float(mo.mean()), 5), round(float(mn.mean()), 5),
                       round(float((mo & mn).sum() / max((mo | mn).sum(), 1)), 4)))
        e[cle] = [dict(couche=k, orca=a, nous=b, ecart=round((b - a) / max(a, 1e-9), 4), iou=i) for k, a, b, i in cv]
    e["cadre"] = cadre
    # parois extérieures (ce qui se voit sur les tranches) : distance de l'axe d'Orca au nôtre, même couche
    from shapely.geometry import MultiLineString, Point
    ow = G.TYPES.index("Outer wall"); dist = []
    for k in range(min(bo["couches"], bn["couches"])):
        sn = (n["couche"] == k) & (n["type"] == ow); so = np.where((o["couche"] == k) & (o["type"] == ow))[0][::5]
        if not sn.any() or not len(so): continue
        ml = MultiLineString([((a, b), (c, d)) for a, b, c, d in zip(n["x0"][sn], n["y0"][sn], n["x1"][sn], n["y1"][sn])])
        dist += [ml.distance(Point((o["x0"][i] + o["x1"][i]) / 2, (o["y0"][i] + o["y1"][i]) / 2)) for i in so]
    if dist: e["parois_mm"] = dict(mediane=round(float(np.median(dist)), 4), p95=round(float(np.percentile(dist, 95)), 4))
    # angle du dessus couche par couche (angle principal de chaque couche qui a un dessus)
    def angles(t):
        s = t["type"] == G.TYPES.index("Top surface"); L = np.hypot(t["x1"] - t["x0"], t["y1"] - t["y0"]); r = {}
        for k in np.unique(t["couche"][s]):
            m = s & (t["couche"] == k) & (L > 0.5)
            if m.any():
                a = np.round(np.degrees(np.arctan2(t["y1"][m] - t["y0"][m], t["x1"][m] - t["x0"][m])) % 180).astype(int) % 180
                r[int(k)] = int(np.argmax(np.bincount(a, weights=L[m], minlength=180)))
        return r
    ao, an = angles(o), angles(n)
    e["dessus_angle_par_couche"] = {k: [ao[k], an.get(k)] for k in ao}
    return e


def verdict(e):
    ok = {}
    po, pn = e["dessus_pas"]
    if po and pn: ok["pas du dessus ± 5 %"] = abs(pn / po - 1) <= 0.05
    t = e["types"].get("Top surface")
    if t and all(t["largeur"]): ok["largeur du dessus ± 5 %"] = abs(t["largeur"][1] / t["largeur"][0] - 1) <= 0.05
    pc = e["dessus_angle_par_couche"]
    if pc: ok["angle du dessus ± 1° (chaque couche)"] = all(b is not None and min(abs(a - b), 180 - abs(a - b)) <= 1 for a, b in pc.values())
    ok["mêmes couches"] = e["couches"][0] == e["couches"][1]
    ok["couverture visible ± 2 % (somme des couches)"] = abs(sum(c["nous"] for c in e["couverture_visible"]) /
                                                         max(sum(c["orca"] for c in e["couverture_visible"]), 1e-9) - 1) <= 0.02
    if "parois_mm" in e: ok["axe des parois extérieures : médiane <= 0,03 mm, 95 % <= 0,15 mm"] = (
        e["parois_mm"]["mediane"] <= 0.03 and e["parois_mm"]["p95"] <= 0.15)
    return ok


def superposition(o, n, k, cadre, px=40):
    a = G.image_couche(o, k, px=px, cadre=cadre, fond=(0, 0, 0)).convert("L").point(lambda v: 255 if v else 0)
    b = G.image_couche(n, k, px=px, cadre=cadre, fond=(0, 0, 0)).convert("L").point(lambda v: 255 if v else 0)
    return Image.merge("RGB", (a, b, Image.new("L", a.size, 0)))


if __name__ == "__main__":
    orca, nous, dest = sys.argv[1:4]; os.makedirs(dest, exist_ok=True)
    o, n = charger(orca, nous); e = ecarts(o, n); e["verdict"] = verdict(e)
    json.dump(e, open(os.path.join(dest, "ecarts.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    zoom = tuple(map(float, sys.argv[4].split(","))) if len(sys.argv) > 4 else e["cadre"]
    nk = e["couches"][0]
    for k in sorted({0, nk // 2, nk - 1}): superposition(o, n, k, zoom).save(os.path.join(dest, f"superposition_{k:03d}.png"))
    print(json.dumps({k: e[k] for k in ("couches", "dessus_pas", "parois_mm", "coutures_mm", "verdict") if k in e},
                     ensure_ascii=False))
    for ty, v in e["types"].items(): print(f"  {ty:24s} longueur {v['longueur']}  largeur {v['largeur']}  rapport {v['rapport_longueur']}")
    print("  visible, pires couches (IoU) :", sorted(e["couverture_visible"], key=lambda c: c["iou"])[:3])
    print("  totale (info), pires couches :", sorted(e["couverture"], key=lambda c: -abs(c["ecart"]))[:2])
