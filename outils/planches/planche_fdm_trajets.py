r"""Planche de validation de la feature fdm-trajets (chunk-05) : Python système (numpy, Pillow).
    python outils\planches\planche_fdm_trajets.py
Pour l'embase de la F-COM2 et le bouton TFR du F-COM1, buses 0,4 et 0,2, trois lignes (face posée sur le plateau, dessus,
tranche) et trois colonnes : trajets réels d'OrcaSlicer (G:\Blender\Bibliotheque\fdm\orca\) · notre simulation
(…\fdm\simulation\, écarts de comparer.py en légende) · rendu Cycles (planche_fdm_cordons.py). Photos de référence de Lou en bas.
Sortie : G:\Blender\Bibliotheque\planches\fdm_trajets\planche_fdm_trajets.png."""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(ICI), "fdm"))
import comparer as C                                  # noqa: E402
import gcode as G                                     # noqa: E402
import planche_orca as PO                             # noqa: E402

FDM = r"G:\Blender\Bibliotheque\fdm"
RENDUS = r"G:\Blender\Bibliotheque\planches\fdm_cordons"
SORTIE = r"G:\Blender\Bibliotheque\planches\fdm_trajets"
TW, TH = 480, 360
ZE, ZT = (188.0, 108.0, 206.0, 121.5), (128.0, 130.5, 143.0, 141.75)   # zooms 4:3 (repère du plateau) : coin de l'embase, TFR
CAS = [("embase_04", "Embase F-COM2, buse 0,4", ZE), ("embase_02", "Embase F-COM2, buse 0,2", ZE),
       ("tfr_04", "Bouton TFR F-COM1, buse 0,4", ZT), ("tfr_02", "Bouton TFR F-COM1, buse 0,2", ZT)]
P = lambda t, g=False: ImageFont.truetype(rf"C:\Windows\Fonts\arial{'bd' if g else ''}.ttf", t)
FOND, ENCRE, GRIS = (246, 246, 247), (22, 22, 26), (95, 95, 102)


def case(im):
    """Image ramenée à TW × TH sans déformation (recadrée au centre)."""
    w, h = im.size; r = TW / TH
    if w / h > r: nw = int(h * r); im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else: nh = int(w / r); im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    return im.convert("RGB").resize((TW, TH), Image.LANCZOS)


def couche_dessus(t):
    s = t["type"] == G.TYPES.index("Top surface"); L = np.hypot(t["x1"] - t["x0"], t["y1"] - t["y0"])
    return int(np.argmax(np.bincount(t["couche"][s], weights=L[s])))


def main():
    os.makedirs(SORTIE, exist_ok=True)
    blocs = []
    for cas, titre, z in CAS:
        o, n = C.charger(os.path.join(FDM, "orca", cas + "_defaut"), os.path.join(FDM, "simulation", cas + "_defaut.npz"))
        e = json.load(open(os.path.join(FDM, "simulation", cas + "_defaut", "ecarts.json"), encoding="utf-8"))
        px = int(TW / (z[2] - z[0])); kd = couche_dessus(o)
        lignes = [("face (sur le plateau)", G.image_couche(o, 0, px=px, cadre=z), G.image_couche(n, 0, px=px, cadre=z), f"{cas}_face.png"),
                  (f"dessus (couche {kd})", G.image_couche(o, kd, px=px, cadre=z), G.image_couche(n, kd, px=px, cadre=z), f"{cas}_dos.png"),
                  ("tranche (coutures)", PO.coutures(o), PO.coutures(n), f"{cas}_tranche.png")]
        ok = sum(e["verdict"].values()); pm = e.get("parois_mm", {})
        note = (f"pas du dessus {e['dessus_pas'][0]} / {e['dessus_pas'][1]} mm · axe des parois {pm.get('mediane')} mm "
                f"(95 % : {pm.get('p95')}) · seuils {ok} / {len(e['verdict'])}")
        blocs.append((titre, note, [(t, case(a), case(b), case(Image.open(os.path.join(RENDUS, r)))) for t, a, b, r in lignes]))
    refs = [case(Image.open(os.path.join(RENDUS, f"ref_{k}.png"))) for k in (2, 3, 5)]
    G_, M = 12, 230                                       # gouttière, marge des titres de ligne
    H = 130 + sum(66 + 3 * (TH + G_) for _ in blocs) + 46 + TH + 60
    W = M + 3 * (TW + G_)
    pl = Image.new("RGB", (W, H), FOND); d = ImageDraw.Draw(pl)
    d.text((16, 16), "PLA FDM d'après les vrais trajets de la buse — validation", fill=ENCRE, font=P(30, True))
    for j, c in enumerate(("OrcaSlicer 2.4.2 (profil U1)", "notre simulation (tranchage.py)", "rendu (procedes.trajets)")):
        d.text((M + j * (TW + G_), 80), c, fill=ENCRE, font=P(20, True))
    y = 120
    for titre, note, lignes in blocs:
        d.text((16, y + 4), titre, fill=ENCRE, font=P(21, True)); d.text((16, y + 34), note, fill=GRIS, font=P(16)); y += 66
        for t, a, b, r in lignes:
            d.multiline_text((16, y + 8), t, fill=GRIS, font=P(16))
            for j, im in enumerate((a, b, r)): pl.paste(im, (M + j * (TW + G_), y))
            y += TH + G_
    d.text((16, y + 6), "Vos photos de référence (2, 3, 5)", fill=ENCRE, font=P(21, True)); y += 46
    for j, im in enumerate(refs): pl.paste(im, (M + j * (TW + G_), y))
    d.text((16, y + TH + 18), "Couleurs des trajets : orange paroi extérieure · jaune paroi intérieure · rouge dessus · bleu face plateau · "
           "violet plein ; coutures : un point par contour et par couche. Trajets vus du dessus du plateau (la face est donc en miroir "
           "du rendu). TFR tranché d'une seule matière.", fill=GRIS, font=P(15))
    s = os.path.join(SORTIE, "planche_fdm_trajets.png"); pl.save(s); print(s, pl.size)


if __name__ == "__main__":
    main()
