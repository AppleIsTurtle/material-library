r"""Estimation de lettres telles que la U1 de l'imprimeur FDM les imprimerait (Python système : numpy, scipy, shapely, Pillow).
Les lettres blanches sont imprimées dans la masse d'une façade noire (multi-matière), face avant sur le plateau texturé : ce qu'on
voit est leur premier calque. On part de leur contour exact (premier calque, y = 0,1) et on applique un modèle d'impression FDM :
  - coins arrondis par le cordon : un coin, saillant ou rentrant, ne peut pas être plus vif qu'un demi-cordon ;
  - traits fins : un trait plus fin qu'un cordon est imprimé d'un seul cordon (élargi), un trait très fin disparaît ;
  - bord qui ondule : position de la buse et écrasement du cordon irréguliers (bruit de quelques centièmes, corrélé sur ~0,4 mm) ;
  - frontière noir / blanc floue : les deux matières se touchent encore chaudes et se mélangent sur quelques centièmes.
    python lettres.py <lettres.stl> <sortie .npz> [buse 0.4|0.2 | exact]
« exact » : lettres gravées au laser ou imprimées à plat (contour exact, bord anticrénelé).
Écrit un masque (0 = noir, 1 = blanc) sur une grille (x, z) du repère des maquettes, lu par matieres.procedes (lettres_imprimees,
lettres_gravees). Repris de MFS boitier/scripts/simulation_lettres_facade.py (2026-10-26) : STL des lettres en argument.
Valeurs = estimations de réglages courants (trancheur Orca / Snapmaker, PLA), à confirmer sur une impression d'essai chez l'imprimeur FDM.
"""
import struct, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from shapely.geometry import LineString, Polygon
from shapely.ops import polygonize, unary_union

STL_LETTRES, SORTIE = sys.argv[1], sys.argv[2]
EXACT = len(sys.argv) > 3 and sys.argv[3] == "exact"        # « exact » : lettres imprimées à plat (acrylique imprimé au dos, LCSC)
BUSE = float(sys.argv[3]) if len(sys.argv) > 3 and not EXACT else 0.4
LARGEUR = {0.4: 0.45, 0.2: 0.22}[BUSE]          # largeur du cordon (réglage courant du trancheur pour la buse)
MIN_TRAIT = 0.55 * LARGEUR                      # en dessous, le trancheur ne trace rien (« détection des murs fins »)
BRUIT, CORREL = {0.4: 0.05, 0.2: 0.02}[BUSE], 0.35  # ondulation du bord (mm) et sa longueur de corrélation (mm)
MELANGE = {0.4: 0.05, 0.2: 0.025}[BUSE]        # demi-largeur de la zone de mélange des deux matières (mm)
PAS = 0.02                                      # mm par pixel


def lire_stl(chemin):                           # même lecture que tranchage.py
    d = open(chemin, "rb").read()
    n = struct.unpack("<I", d[80:84])[0]
    a = np.frombuffer(d[84:84 + 50 * n], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return a["v"].reshape(-1, 3, 3).astype(np.float64)


def coupe(tri, y):                              # même découpe que tranchage.py
    segs = []
    for t in tri:
        d = t[:, 1] - y
        pts = []
        for i, j in ((0, 1), (1, 2), (2, 0)):
            if (d[i] < 0) != (d[j] < 0):
                a_, b_ = (i, j) if tuple(t[i]) < tuple(t[j]) else (j, i)
                k = (t[a_, 1] - y) / (t[a_, 1] - t[b_, 1]); p = t[a_] + k * (t[b_] - t[a_])
                pts.append((round(p[0], 5), round(p[2], 5)))
        if len(pts) == 2: segs.append(LineString(pts))
    s = Polygon()
    for p in polygonize(unary_union(segs)): s = s.symmetric_difference(Polygon(p.exterior))
    return s.buffer(0)


lettres = coupe(lire_stl(STL_LETTRES), 0.1)           # premier calque (0 → 0,2)
x0, z0, x1, z1 = lettres.bounds; x0 -= 1; z0 -= 1; x1 += 1; z1 += 1
nx, nz = int((x1 - x0) / PAS) + 1, int((z1 - z0) / PAS) + 1
im = Image.new("L", (nx, nz), 0); dr = ImageDraw.Draw(im)
for p in getattr(lettres, "geoms", [lettres]):
    px = lambda c: [((x - x0) / PAS, (z - z0) / PAS) for x, z in c]
    dr.polygon(px(p.exterior.coords), fill=255)
    for h in p.interiors: dr.polygon(px(h.coords), fill=0)
W = np.array(im) > 127                                                    # lignes = z, colonnes = x
print(f"lettres : {lettres.area:.1f} mm², grille {nx} × {nz} ({PAS} mm)")


def disque(r):
    n = int(round(r / PAS)); y, x = np.ogrid[-n:n + 1, -n:n + 1]; return x * x + y * y <= n * n


r = LARGEUR / 2
if EXACT:                                       # impression à plat (UV) : contour exact, bord adouci d'un pixel (anticrénelage)
    masque = ndimage.gaussian_filter(W.astype(np.float32), 0.5)
    np.savez_compressed(SORTIE, masque=masque, x0=x0, z0=z0, pas=PAS, buse=0.0, largeur=0.0)
    print("écrit (exact)", SORTIE); sys.exit(0)


def trace(M):
    """Ce que le trancheur trace d'une matière M : les parties assez larges (ouverture par un disque d'un demi-cordon : coins
    arrondis), plus les traits plus fins qu'un cordon mais assez larges pour être tracés, d'un seul cordon centré sur le trait."""
    ouvert = ndimage.binary_opening(M, structure=disque(r))
    epais = ndimage.distance_transform_edt(M) * PAS * 2                  # épaisseur locale ≈ 2 × distance au bord
    fins = M & ~ouvert & (epais >= MIN_TRAIT)
    coeur = fins & (ndimage.maximum_filter(epais, size=3) == epais)      # crête du trait fin
    return ouvert | ndimage.binary_dilation(coeur, structure=disque(r))


# 1-3. les deux matières, chacune tracée par ses cordons (le noir aussi : creux des lettres, intérieur du E, du S…) ; une zone que
# les deux réclament ou qu'aucune ne trace garde la matière dessinée
blanc, noir = trace(W), trace(~W)
imprime = np.where(blanc & ~noir, True, np.where(noir & ~blanc, False, W))
# 4. bord qui ondule : distance signée au bord + bruit corrélé, puis 5. mélange des matières (bord flou)
sd = (ndimage.distance_transform_edt(imprime) - ndimage.distance_transform_edt(~imprime)) * PAS
rng = np.random.default_rng(11)
bruit = ndimage.gaussian_filter(rng.normal(0, 1, sd.shape), CORREL / PAS)
bruit *= BRUIT / bruit.std()
masque = np.clip(0.5 + (sd + bruit) / (2 * MELANGE), 0, 1).astype(np.float32)
perdu, ajoute = (W & (masque < 0.5)).sum() * PAS ** 2, (~W & (masque >= 0.5)).sum() * PAS ** 2
print(f"modèle buse {BUSE} : cordon {LARGEUR}, trait mini {MIN_TRAIT:.2f}, ondulation ±{BRUIT} mm, mélange ±{MELANGE} mm ; "
      f"blanc perdu {perdu:.2f} mm², ajouté {ajoute:.2f} mm²")
np.savez_compressed(SORTIE, masque=masque, x0=x0, z0=z0, pas=PAS, buse=BUSE, largeur=LARGEUR)
print("écrit", SORTIE)
