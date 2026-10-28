r"""Planche des vrais trajets d'OrcaSlicer (feature fdm-trajets, chunk-01) : Python système (numpy, Pillow).
    python planche_orca.py [<dossier orca>]        défaut : G:\Blender\Bibliotheque\fdm\orca
Lit les lectures de gcode.py (<cas>/lecture/trajets.npz) et compose planche_orca.png : embase de la F-COM2 et bouton TFR du
F-COM1, buses 0,4 et 0,2 (face sur le plateau, couche courante, dessus, coutures), puis les variantes de l'embase en buse 0,4."""
import os, sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gcode as G

ORCA = sys.argv[1] if len(sys.argv) > 1 else r"G:\Blender\Bibliotheque\fdm\orca"
TUILE = 560
ZOOM_EMBASE = (188.0, 106.0, 208.0, 124.0)            # coin de fenêtre, trou de vis et bord extérieur (repère plateau, mm)
try: POLICE = ImageFont.truetype("arial.ttf", 22); PETITE = ImageFont.truetype("arial.ttf", 17)
except OSError: POLICE = PETITE = ImageFont.load_default()


def charger(cas):
    return dict(np.load(os.path.join(ORCA, cas, "lecture", "trajets.npz")))


def tuile(t, k, cadre=None):
    px = TUILE / ((cadre[2] - cadre[0]) if cadre else max(np.ptp(np.r_[t["x0"], t["x1"]]), np.ptp(np.r_[t["y0"], t["y1"]])) + 2)
    im = G.image_couche(t, k, px=int(px), cadre=cadre)
    return im.resize((TUILE, int(TUILE * im.height / im.width)))


def coutures(t, cadre=None):
    """Début de chaque boucle de paroi extérieure, toutes couches (couleur = couche), sur la silhouette de la couche 1."""
    if cadre is None:
        cadre = (t["x0"].min() - 1, t["y0"].min() - 1, t["x0"].max() + 1, t["y0"].max() + 1)
    px = TUILE / max(cadre[2] - cadre[0], cadre[3] - cadre[1])
    im = G.image_couche(t, 1, px=max(1, int(px)), cadre=cadre, fond=(24, 24, 26)).point(lambda v: v // 4)
    im = im.resize((TUILE, int(TUILE * im.height / im.width))); d = ImageDraw.Draw(im); s = TUILE / (cadre[2] - cadre[0])
    ow = G.TYPES.index("Outer wall"); n = t["couche"].max() + 1
    saut = np.hypot(t["x0"][1:] - t["x1"][:-1], t["y0"][1:] - t["y1"][:-1]) > 0.01          # nouveau chemin (comme gcode.bilan)
    debut = np.r_[True, (t["type"][1:] != t["type"][:-1]) | (t["couche"][1:] != t["couche"][:-1]) | saut] & (t["type"] == ow)
    for x, y, k in zip(t["x0"][debut], t["y0"][debut], t["couche"][debut]):
        u, v = (x - cadre[0]) * s, (cadre[3] - y) * s; c = int(80 + 175 * k / max(n - 1, 1))
        d.ellipse([u - 4, v - 4, u + 4, v + 4], fill=(c, 230, 255 - c))
    return im


def ligne(titre, tuiles):
    h = max(i.height for i, _ in tuiles) + 40
    im = Image.new("RGB", (220 + len(tuiles) * (TUILE + 12), h), (245, 244, 240)); d = ImageDraw.Draw(im)
    d.multiline_text((12, 20), titre, fill=(20, 20, 20), font=POLICE, spacing=6)
    for j, (t_, leg) in enumerate(tuiles):
        x = 220 + j * (TUILE + 12); im.paste(t_, (x, 34)); d.text((x, 8), leg, fill=(40, 40, 40), font=PETITE)
    return im


def main():
    lignes = []
    for b in ("04", "02"):
        e = charger(f"embase_{b}_defaut"); n = e["couche"].max()
        lignes.append(ligne(f"Embase F-COM2\nbuse 0,{b[1]}\n(zoom 20 mm)", [
            (tuile(e, 0, ZOOM_EMBASE), "couche 0 : face avant, sur le plateau"), (tuile(e, n // 2, ZOOM_EMBASE), f"couche {n // 2} : parois + plein"),
            (tuile(e, n, ZOOM_EMBASE), f"couche {n} : dessus (dos)"), (coutures(e), "coutures, toutes couches")]))
    for b in ("04", "02"):
        t = charger(f"tfr_{b}_defaut"); n = t["couche"].max()
        ts = t["type"] == G.TYPES.index("Top surface"); L = np.hypot(t["x1"] - t["x0"], t["y1"] - t["y0"])
        kd = int(np.argmax(np.bincount(t["couche"][ts], weights=L[ts])))          # couche qui a le plus de dessus (épaulement)
        lignes.append(ligne(f"Bouton TFR F-COM1\nbuse 0,{b[1]}\n(entier, 10 mm)", [
            (tuile(t, 0), "couche 0 : face sur le plateau"), (tuile(t, n // 2), f"couche {n // 2} : flancs de la tige"),
            (tuile(t, kd), f"couche {kd} : dessus de l'épaulement"), (coutures(t), "coutures, toutes couches")]))
    v = {c: charger(f"embase_04_{c}") for c in ("1paroi", "concentrique", "couture_arriere", "couture_aleatoire")}
    lignes.append(ligne("Variantes\nembase buse 0,4", [
        (tuile(v["1paroi"], 3, ZOOM_EMBASE), "1 paroi au lieu de 2 (couche 3)"), (tuile(v["concentrique"], 7, ZOOM_EMBASE), "dessus concentrique"),
        (coutures(v["couture_arriere"]), "couture « arrière »"), (coutures(v["couture_aleatoire"]), "couture aléatoire")]))
    W = max(l.width for l in lignes); H = sum(l.height for l in lignes) + 120
    pl = Image.new("RGB", (W, H), (245, 244, 240)); d = ImageDraw.Draw(pl)
    d.text((12, 14), "Vrais trajets d'OrcaSlicer 2.4.2 — profil Snapmaker U1 par défaut, PLA", fill=(0, 0, 0), font=POLICE)
    d.text((12, 48), "orange : paroi extérieure · jaune : paroi intérieure · rouge : dessus · bleu : face plateau · violet : plein "
           "interne · vert : petits espaces · trait foncé : axe du cordon (largeur réelle)", fill=(60, 60, 60), font=PETITE)
    y = 90
    for l in lignes: pl.paste(l, (0, y)); y += l.height
    sortie = os.path.join(ORCA, "planche_orca.png"); pl.save(sortie); print(sortie, pl.size)


if __name__ == "__main__":
    main()
