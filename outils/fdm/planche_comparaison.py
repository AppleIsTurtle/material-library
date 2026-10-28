r"""Planche « Orca | notre simulation | superposition » (feature fdm-trajets, chunk-02) : Python système (numpy, Pillow).
    python planche_comparaison.py [<dossier orca> <dossier simulation>]
Pour chaque cas (dossier Orca + nos trajets <cas>.npz) et chaque couche choisie : trajets d'Orca, les nôtres (mêmes couleurs que
gcode.py), superposition (rouge : Orca seul, vert : nous seuls, jaune : les deux) ; écarts chiffrés de comparer.py en légende.
Sortie : <dossier simulation>/planche_comparaison.png."""
import json, os, sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comparer as C
import gcode as G

ORCA = sys.argv[1] if len(sys.argv) > 2 else r"G:\Blender\Bibliotheque\fdm\orca"
SIM = sys.argv[2] if len(sys.argv) > 2 else r"G:\Blender\Bibliotheque\fdm\simulation"
T = 420
ZE, ZT = (190.0, 108.0, 204.0, 122.0), (129.5, 129.5, 141.5, 141.5)        # zooms : coin de l'embase, bouton TFR entier
CAS = [("embase_04_defaut", ZE, (0, 3, 7)), ("embase_02_defaut", ZE, (0, 15)), ("tfr_04_defaut", ZT, (0, 3, 20)),
       ("tfr_02_defaut", ZT, (0, 50, 71)), ("embase_04_1paroi", ZE, (3,)), ("embase_04_concentrique", ZE, (7,))]
try: P = ImageFont.truetype("arial.ttf", 18); PP = ImageFont.truetype("arial.ttf", 15)
except OSError: P = PP = ImageFont.load_default()


def main():
    lignes = []
    for cas, z, ks in CAS:
        o, n = C.charger(os.path.join(ORCA, cas), os.path.join(SIM, cas + ".npz"))
        e = json.load(open(os.path.join(SIM, cas, "ecarts.json"), encoding="utf-8"))
        px = int(T / (z[2] - z[0]))
        for k in ks:
            ims = [G.image_couche(o, k, px=px, cadre=z), G.image_couche(n, k, px=px, cadre=z), C.superposition(o, n, k, z, px=px)]
            ims = [i.resize((T, T)) for i in ims]
            l = Image.new("RGB", (260 + 3 * (T + 10), T + 30), (245, 244, 240)); d = ImageDraw.Draw(l)
            ok = sum(e["verdict"].values()); pm = e.get("parois_mm", {})
            d.multiline_text((10, 30), f"{cas}\ncouche {k}\n\nseuils : {ok}/{len(e['verdict'])}\npas dessus {e['dessus_pas']}\n"
                             f"axe parois {pm.get('mediane')} mm\n(95 % : {pm.get('p95')})", fill=(20, 20, 20), font=PP, spacing=4)
            for j, (im, leg) in enumerate(zip(ims, ("OrcaSlicer", "notre simulation", "superposition"))):
                l.paste(im, (260 + j * (T + 10), 26)); d.text((260 + j * (T + 10), 4), leg, fill=(40, 40, 40), font=P)
            lignes.append(l)
    W = max(l.width for l in lignes); pl = Image.new("RGB", (W, sum(l.height for l in lignes) + 50), (245, 244, 240))
    ImageDraw.Draw(pl).text((10, 12), "Trajets : OrcaSlicer 2.4.2 (profil U1) contre notre simulation (tranchage.py) — "
                            "superposition : rouge Orca seul, vert nous seuls, jaune les deux", fill=(0, 0, 0), font=P)
    y = 50
    for l in lignes: pl.paste(l, (0, y)); y += l.height
    s = os.path.join(SIM, "planche_comparaison.png"); pl.save(s); print(s, pl.size)


if __name__ == "__main__":
    main()
