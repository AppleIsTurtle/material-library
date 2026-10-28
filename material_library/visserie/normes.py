r"""Tables de la visserie du commerce (DIN / ISO) : cotes de tête, empreintes, pas, écrous, rondelles, inserts. Python pur (sans
bpy) : se teste hors de Blender. Cotes en mm, valeurs maximales (nominales) des normes, celles d'une pièce neuve du commerce.

Sources (relevées le 2026-10-27) :
- pas gros ISO 261 / 262 ;
- DIN 84 (remplacée par ISO 1207, mêmes cotes) : fasten.it/Norms/Norm/DIN_84 — fente : largeur nominale n, profondeur t min ;
- ISO 7045 (bombée cruciforme H) : dk, k, m d'après engineersedge.com « ISO Phillips Pan Head » et la fiche Würth M5 (dk 9,5,
  k 3,7) ; fasten.it donne d'anciennes valeurs DIN 7985 (M3 dk 6) : écartées ; rf (rayon du dôme) d'après ISO 7045, valeurs de
  référence ;
- ISO 7046-1 / -2 (fraisée 90° cruciforme H, remplace DIN 965) : fasten.it/Norms/Norm/DIN_EN_ISO_7046_2 (dk = diamètre réel, M3
  5,5 × 1,65) ; fiche Würth 5105004006 (M4 × 6 A2, H2) ;
- ISO 4762 (tête cylindrique à six pans creux, ex-DIN 912) : valeurs usuelles des catalogues (accu.co.uk, pts-uk.com) ;
- ISO 4032 (écrou hexagonal, ex-DIN 934 ; M5 à M8 un peu plus hauts que DIN 934) ; DIN 125-A (rondelle plate) ;
- inserts laiton à chaud ruthex (RX-M2x4, RX-M3x5.7, RX-M4x8.1 ; tableau constructeur repris par 3djake.ch) : D1 extérieur,
  D3 = trou à prévoir dans la pièce imprimée.
Empreinte cruciforme « de rendu » (croix_rendu) : règle tirée des petites vis du F-COM2 validées par Lou (M3 ISO 7046 : bras de
1,35, demi-largeur 0,3, profondeur 1,1)."""
import re

PAS = {2: 0.4, 2.5: 0.45, 3: 0.5, 4: 0.7, 5: 0.8, 6: 1.0, 8: 1.25}          # ISO 261, pas gros

# tête cylindrique fendue : dk diamètre, k hauteur, n largeur de fente (nominale), t profondeur de fente (min)
DIN_84 = {2: dict(dk=3.8, k=1.3, n=0.5, t=0.6), 2.5: dict(dk=4.5, k=1.6, n=0.6, t=0.7), 3: dict(dk=5.5, k=2.0, n=0.8, t=0.85),
          4: dict(dk=7.0, k=2.6, n=1.2, t=1.1), 5: dict(dk=8.5, k=3.3, n=1.2, t=1.3), 6: dict(dk=10.0, k=3.9, n=1.6, t=1.6),
          8: dict(dk=13.0, k=5.0, n=2.0, t=2.0)}

# tête bombée cruciforme H : rf rayon du dôme, ph numéro d'empreinte, m diamètre de l'empreinte en surface (référence)
ISO_7045 = {2: dict(dk=4.0, k=1.6, rf=3.2, ph=0, m=1.9), 2.5: dict(dk=5.0, k=2.1, rf=4.0, ph=1, m=2.7),
            3: dict(dk=5.6, k=2.4, rf=5.0, ph=1, m=3.0), 4: dict(dk=8.0, k=3.1, rf=6.5, ph=2, m=4.4),
            5: dict(dk=9.5, k=3.7, rf=8.0, ph=2, m=4.9), 6: dict(dk=12.0, k=4.6, rf=10.0, ph=3, m=6.9),
            8: dict(dk=16.0, k=6.0, rf=13.0, ph=4, m=9.0)}

# tête fraisée 90° cruciforme H (dk réel, celui de la pièce)
ISO_7046 = {2: dict(dk=3.8, k=1.2, ph=0, m=1.9), 2.5: dict(dk=4.7, k=1.5, ph=1, m=2.9), 3: dict(dk=5.5, k=1.65, ph=1, m=3.2),
            4: dict(dk=8.4, k=2.7, ph=2, m=4.6), 5: dict(dk=9.3, k=2.7, ph=2, m=5.2), 6: dict(dk=11.3, k=3.3, ph=3, m=6.8),
            8: dict(dk=15.8, k=4.65, ph=4, m=8.9)}

# tête cylindrique à six pans creux : s six pans (sur plats), t profondeur (min)
ISO_4762 = {2: dict(dk=3.8, k=2.0, s=1.5, t=1.0), 2.5: dict(dk=4.5, k=2.5, s=2.0, t=1.1), 3: dict(dk=5.5, k=3.0, s=2.5, t=1.3),
            4: dict(dk=7.0, k=4.0, s=3.0, t=2.0), 5: dict(dk=8.5, k=5.0, s=4.0, t=2.5), 6: dict(dk=10.0, k=6.0, s=5.0, t=3.0),
            8: dict(dk=13.0, k=8.0, s=6.0, t=4.0)}

ISO_4032 = {2: dict(s=4.0, m=1.6), 2.5: dict(s=5.0, m=2.0), 3: dict(s=5.5, m=2.4), 4: dict(s=7.0, m=3.2), 5: dict(s=8.0, m=4.7),
            6: dict(s=10.0, m=5.2), 8: dict(s=13.0, m=6.8)}                  # s sur plats, m hauteur

DIN_125 = {2: dict(d1=2.2, d2=5.0, h=0.3), 2.5: dict(d1=2.7, d2=6.0, h=0.5), 3: dict(d1=3.2, d2=7.0, h=0.5),
           4: dict(d1=4.3, d2=9.0, h=0.8), 5: dict(d1=5.3, d2=10.0, h=1.0), 6: dict(d1=6.4, d2=12.0, h=1.6),
           8: dict(d1=8.4, d2=16.0, h=1.6)}                                   # d1 alésage, d2 extérieur, h épaisseur

INSERT_LAITON = {2: dict(d1=3.6, d2=3.1, trou=3.2, l=4.0, paroi=1.3), 3: dict(d1=4.6, d2=3.9, trou=4.0, l=5.7, paroi=1.6),
                 4: dict(d1=6.3, d2=5.5, trou=5.6, l=8.1, paroi=2.1)}      # ruthex ; paroi = matière minimale autour

PH_DEMI_LARGEUR = {0: 0.2, 1: 0.3, 2: 0.4, 3: 0.6, 4: 0.75}               # demi-largeur des bras d'une empreinte PH (rendu)

# désignation → (table, forme) ; ISO 1207 = DIN 84, DIN 965 = ISO 7046, DIN 912 = ISO 4762, DIN 934 ≈ ISO 4032
NORMES = {"DIN 84": (DIN_84, "cylindrique_fendue"), "ISO 1207": (DIN_84, "cylindrique_fendue"),
          "ISO 7045": (ISO_7045, "bombee_cruciforme"), "ISO 7046": (ISO_7046, "fraisee_cruciforme"),
          "DIN 965": (ISO_7046, "fraisee_cruciforme"), "ISO 4762": (ISO_4762, "btr"), "DIN 912": (ISO_4762, "btr"),
          "ISO 4032": (ISO_4032, "ecrou"), "DIN 934": (ISO_4032, "ecrou"), "DIN 125": (DIN_125, "rondelle"),
          "INSERT": (INSERT_LAITON, "insert")}

MATIERES = {"inox": "inox", "a2": "inox", "a4": "inox", "oxyde": "oxyde", "oxydé": "oxyde", "noir": "oxyde", "laiton": "laiton"}


def norme(nom):
    """Nom canonique d'une norme (« iso7046 », « DIN965 », « din 84 » → clé de NORMES)."""
    cle = re.sub(r"\s+", "", nom).upper()
    for n in NORMES:
        if n.replace(" ", "") == cle:
            return n
    raise KeyError(f"norme inconnue : {nom} (connues : {', '.join(NORMES)})")


def cotes(nom, d):
    """Cotes d'une pièce (norme, diamètre nominal) + d, pas, forme ; KeyError si la taille n'existe pas dans la table."""
    n = norme(nom); table, forme = NORMES[n]
    if d not in table:
        raise KeyError(f"{n} : pas de M{d:g} dans la table (tailles : {', '.join(f'M{x:g}' for x in table)})")
    return dict(table[d], d=d, pas=PAS[d], norme=n, forme=forme)


def designation(texte):
    """« M4 × 8 DIN 84 inox A2 » → dict(d=4, l=8.0, norme='DIN 84', matiere='inox') ; l = None pour un écrou, une rondelle…"""
    t = texte.replace("×", "x").replace(",", ".")
    m = re.match(r"\s*M(\d+(?:\.\d+)?)\s*(?:x\s*(\d+(?:\.\d+)?))?\s*(.*)$", t, re.I)
    if not m:
        raise ValueError(f"désignation illisible : {texte}")
    d = float(m.group(1)); d = int(d) if d.is_integer() else d
    reste = m.group(3)
    n = next((k for k in sorted(NORMES, key=len, reverse=True) if re.search(k.replace(" ", r"\s*"), reste, re.I)), None)
    if n is None:
        raise ValueError(f"norme absente de la désignation : {texte}")
    mat = next((v for k, v in MATIERES.items() if re.search(rf"\b{k}\b", reste, re.I)), "inox")
    return dict(d=d, l=float(m.group(2)) if m.group(2) else None, norme=n, matiere=mat)


def croix_rendu(nom, d):
    """Empreinte cruciforme modélisée : (demi-longueur des bras en surface, demi-largeur, profondeur), arrondis à 0,05.
    Règle des petites vis du F-COM2 (M3 ISO 7046, m 3,2 → 1,35 / 0,3 / 1,1) : bras 0,42 m, profondeur 0,34 m."""
    c = cotes(nom, d)
    return (round(round(0.42 * c["m"] / 0.05) * 0.05, 2), PH_DEMI_LARGEUR[c["ph"]], round(round(0.34 * c["m"] / 0.05) * 0.05, 2))


def passage(d):
    """Rayon du trou de passage d'une vis Md (Ø d + 0,4 : M3 → 3,4, M4 → 4,4 ; entre les séries fine et moyenne d'ISO 273)."""
    return round(d / 2 + 0.2, 3)
