r"""Python système + Pillow : assemble des rendus en une planche (grille titrée).
    python outils\planches\assembler.py <grille.json> <planche.png>
grille.json : {"titre": "…", "colonnes": ["…"], "lignes": [{"titre": "…", "images": ["chemin.png" | null, …],
               "notes": ["…" | null, …]}], "pied": "…"} ; chaque planche_*.py l'écrit à côté de ses rendus."""
import json
import sys

from PIL import Image, ImageDraw, ImageFont

POLICE = lambda t, gras=False: ImageFont.truetype(rf"C:\Windows\Fonts\arial{'bd' if gras else ''}.ttf", t)
FOND, ENCRE, GRIS = (246, 246, 247), (22, 22, 26), (95, 95, 102)


def _ouvrir(chemin):
    """Image RGB ; une image à fond transparent (aperçus d'assets) est posée sur un gris clair."""
    im = Image.open(chemin)
    if im.mode in ("RGBA", "LA"):
        fond = Image.new("RGBA", im.size, (222, 223, 226, 255)); fond.alpha_composite(im.convert("RGBA")); im = fond
    return im.convert("RGB")


def assembler(g, sortie, largeur_case=600):
    ims = [[_ouvrir(c) if c else None for c in l["images"]] for l in g["lignes"]]
    ex = next(i for l in ims for i in l if i)
    hc = round(largeur_case * ex.height / ex.width)
    nc = len(g["colonnes"]); m, tl, th = 24, 260, 110
    tn = 16 + 28 * max([1] + [(n or "").count("\n") + 1 for l in g["lignes"] for n in (l.get("notes") or [])])
    L = tl + nc * (largeur_case + m) + m
    H = th + 50 + len(ims) * (hc + tn + m) + (60 if g.get("pied") else 0) + m
    pl = Image.new("RGB", (L, H), FOND); d = ImageDraw.Draw(pl)
    d.text((m, 26), g["titre"], font=POLICE(40, True), fill=ENCRE)
    for j, t in enumerate(g["colonnes"]):
        d.text((tl + j * (largeur_case + m), th), t, font=POLICE(28, True), fill=ENCRE)
    y = th + 50
    for l, li in zip(g["lignes"], ims):
        mots, ligne, lignes = l["titre"].split(), "", []
        for w in mots:                                         # titre de ligne sur plusieurs lignes
            if d.textlength(ligne + " " + w, font=POLICE(26, True)) > tl - 2 * m and ligne: lignes.append(ligne); ligne = w
            else: ligne = (ligne + " " + w).strip()
        lignes.append(ligne)
        for k, t in enumerate(lignes): d.text((m, y + 10 + 32 * k), t, font=POLICE(26, True), fill=ENCRE)
        for j, im in enumerate(li):
            x = tl + j * (largeur_case + m)
            if im: pl.paste(im.resize((largeur_case, hc), Image.LANCZOS), (x, y))
            note = (l.get("notes") or [None] * nc)[j]
            if note: d.multiline_text((x, y + hc + 8), note, font=POLICE(22), fill=GRIS, spacing=6)
        y += hc + tn + m
    if g.get("pied"): d.text((m, y + 6), g["pied"], font=POLICE(22), fill=GRIS)
    pl.save(sortie, optimize=True); print(sortie, pl.size)


if __name__ == "__main__":
    assembler(json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2])
