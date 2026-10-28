# Marquage imprimé d'un composant (lignes de texte) en image d'encre (encre.py), pour les décalques des rendus (decalques.py).
# Repris de MFS boitier/scripts/impression_texte.py (2026-10-26), material-library chunk-04.
# Python système ou de KiCad (PIL) : python texte.py <sortie.png> <hauteur des capitales en mm> <police .ttf | points> <ligne1|ligne2…>
# [interligne] — écrit l'image (200 px/mm, marge de 0,15 mm) et affiche « TEXTE <png> <largeur mm> <hauteur mm> ».
# Police « points » : matrice 5 × 7 en gouttes d'encre, comme les imprimantes jet d'encre industrielles des marquages de composants
# (flanc de l'afficheur SLR0363DYA1BD, photo LCSC).
import os, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import encre

PX_MM = 200
G5X7 = {"0": "01110 10001 10011 10101 11001 10001 01110", "1": "00100 01100 00100 00100 00100 00100 01110",
        "2": "01110 10001 00001 00010 00100 01000 11111", "3": "11111 00010 00100 00010 00001 10001 01110",
        "4": "00010 00110 01010 10010 11111 00010 00010", "5": "11111 10000 11110 00001 00001 10001 01110",
        "6": "00110 01000 10000 11110 10001 10001 01110", "7": "11111 00001 00010 00100 01000 01000 01000",
        "8": "01110 10001 10001 01110 10001 10001 01110", "9": "01110 10001 10001 01111 00001 00010 01100",
        "A": "01110 10001 10001 11111 10001 10001 10001", "B": "11110 10001 10001 11110 10001 10001 11110",
        "C": "01110 10001 10000 10000 10000 10001 01110", "D": "11100 10010 10001 10001 10001 10010 11100",
        "E": "11111 10000 10000 11110 10000 10000 11111", "L": "10000 10000 10000 10000 10000 10000 11111",
        "M": "10001 11011 10101 10101 10001 10001 10001", "P": "11110 10001 10001 11110 10000 10000 10000",
        "R": "11110 10001 10001 11110 10100 10010 10001", "S": "01111 10000 10000 01110 00001 00001 11110",
        "T": "11111 00100 00100 00100 00100 00100 00100", "Y": "10001 10001 01010 00100 00100 00100 00100",
        "-": "00000 00000 00000 11111 00000 00000 00000", " ": "00000 00000 00000 00000 00000 00000 00000"}

dst, cap, police, lignes = sys.argv[1], float(sys.argv[2]), sys.argv[3], sys.argv[4].split("|")
inter = float(sys.argv[5]) if len(sys.argv) > 5 else 1.45
pas = cap * inter * PX_MM; m = 0.15 * PX_MM
if police == "points":                                     # gouttes au pas de cap / 6, chasse de 6 pas
    p = cap / 6 * PX_MM; r = 0.42 * p
    lw = max(len(l) for l in lignes) * 6 * p - p
    W, H = int(lw + 2 * m), int(pas * (len(lignes) - 1) + cap * PX_MM + 2 * m)
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
    for k, l in enumerate(lignes):
        x0 = (W - (len(l) * 6 * p - p)) / 2
        for i, ch in enumerate(l):
            for ry, rang in enumerate(G5X7.get(ch, G5X7[" "]).split()):
                for cx, bit in enumerate(rang):
                    if bit == "1":
                        x, y = x0 + (i * 6 + cx) * p + p / 2, m + k * pas + ry * p + p / 2
                        d.ellipse((x - r, y - r, x + r, y + r), fill=255)
    effet = dict(etalement=0.008, bord=0.10, pale=0.25, trous=0.0)
else:
    f = ImageFont.truetype(police, max(8, round(cap * PX_MM / 0.72)))          # capitales ≈ 0,72 × la taille
    boites = [f.getbbox(l) for l in lignes]
    lw = max(b_[2] - b_[0] for b_ in boites)
    W, H = int(lw + 2 * m), int(pas * (len(lignes) - 1) + cap * PX_MM + 2 * m)
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
    asc = f.getbbox("H")[1]
    for k, (l, b_) in enumerate(zip(lignes, boites)):
        d.text(((W - (b_[2] - b_[0])) / 2 - b_[0], m + k * pas - asc), l, font=f, fill=255)
    effet = dict(etalement=0.022, bord=0.15, pale=0.2, trous=2.0)
encre.effet(im, PX_MM, graine=len(sys.argv[4]), **effet).save(dst)
print("TEXTE", dst, W / PX_MM, H / PX_MM)
