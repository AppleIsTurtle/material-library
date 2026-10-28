# Impression d'une grande surface (façade, masque de vitre) en image d'encre (encre.py) : inscriptions, traits, anneaux et aplats
# dessinés en mm, chaque calque de l'image (L, ou R / G / B) rendu en encre imprimée — un peu baveuse (Lou, 2026-10-26).
# Repris de MFS boitier/scripts/impression_calques.py (2026-10-26), material-library chunk-04.
# Python système ou de KiCad (PIL) : python calques.py <description.json> <sortie.png>
# description : {"w": mm, "h": mm, "px_mm": 50, "police": ".ttf", "instance": "Condensed", "echelle_x": 0.93,
#                "calques": [[op, …], …]} — un calque (L) ou trois (R, G, B) ; op, dans l'ordre, valeur 255 = encre, 0 = efface :
#   ["texte", x, z, texte, capitale, valeur] (centre des capitales), ["trait", x0, z0, x1, z1, largeur, valeur] (bouts ronds),
#   ["anneau", x, z, rayon, largeur, valeur], ["rect", x, z, l, h, rayon, valeur] (centre) ; x depuis le centre, z depuis le bas.
import json, os, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import encre

d = json.load(open(sys.argv[1], encoding="utf-8"))
W, H, K = d["w"], d["h"], d["px_mm"]
X = lambda x: (x + W / 2) * K
Z = lambda z: (H - z) * K


def texte(im, x, z, t, cap, v):
    f = ImageFont.truetype(d["police"], max(8, round(cap * K / 0.72)))
    if d.get("instance"): f.set_variation_by_name(d["instance"])
    hb = f.getbbox("H"); capx = hb[3] - hb[1]
    f = ImageFont.truetype(d["police"], max(8, round(cap * K / 0.72 * cap * K / capx)))      # capitales exactement à `cap`
    if d.get("instance"): f.set_variation_by_name(d["instance"])
    hb, b = f.getbbox("H"), f.getbbox(t)
    m = Image.new("L", (b[2] - b[0] + 4, hb[3] - hb[1] + 4), 0)
    ImageDraw.Draw(m).text((2 - b[0], 2 - hb[1]), t, font=f, fill=255)
    m = m.resize((max(1, round(m.width * d.get("echelle_x", 1.0))), m.height), Image.LANCZOS)   # chasse étroite
    x0, y0 = round(X(x) - m.width / 2), round(Z(z) - m.height / 2)
    fond = Image.new("L", m.size, v); im.paste(fond, (x0, y0), m)


calques = []
for ops in d["calques"]:
    im = Image.new("L", (round(W * K), round(H * K)), 0); dr = ImageDraw.Draw(im)
    for op in ops:
        k, a, v = op[0], op[1:-1], op[-1]
        if k == "texte": texte(im, *a, v)
        elif k == "trait":
            x0, z0, x1, z1, l = a; dr.line((X(x0), Z(z0), X(x1), Z(z1)), fill=v, width=max(1, round(l * K)))
            for x_, z_ in ((x0, z0), (x1, z1)):
                r = l * K / 2; dr.ellipse((X(x_) - r, Z(z_) - r, X(x_) + r, Z(z_) + r), fill=v)
        elif k == "anneau":
            x, z, r, l = a; dr.ellipse((X(x) - (r + l / 2) * K, Z(z) - (r + l / 2) * K, X(x) + (r + l / 2) * K, Z(z) + (r + l / 2) * K),
                                       outline=v, width=max(1, round(l * K)))
        elif k == "rect":
            x, z, l, h, r = a; dr.rounded_rectangle((X(x - l / 2), Z(z + h / 2), X(x + l / 2), Z(z - h / 2)), radius=r * K, fill=v)
    calques.append(encre.effet(im, K, etalement=0.022, bord=0.15, pale=0.2, trous=2.0, graine=7 + len(calques)))
(calques[0] if len(calques) == 1 else Image.merge("RGB", calques)).save(sys.argv[2])
print("IMAGE", sys.argv[2])
