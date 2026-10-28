r"""Cotes et normes d'un panneau (façade) et vérification du dessin à plat, avant toute 3D. Python seul (sans bpy).
Méthode : methode/conception_boitier.md, étapes 1, 2, 4 et 5. Repère des maquettes : x à droite (0 = milieu), z en haut
(0 = bas de la façade), y en profondeur (0 = face avant, positif vers l'arrière), mm.

Statut de chaque cote (« ne pas figer une norme non vérifiée ») :
  « fiche »   lue sur une fiche de fabricant ou de vendeur, ou mesurée sur un modèle 1:1 ;
  « estimée » relevée sur photo ou déduite d'autres cotes : à vérifier avant de fabriquer.
"""
from dataclasses import dataclass, field
import math

POUCE = 25.4

# --- normes des pupitres de cockpit à rails (console « Dzus ») : déduites des panneaux relevés, aucun texte normatif lu
NORMES = {
    "largeur_nominale": dict(valeur=5.75 * POUCE, statut="estimée",
                             source="5,75 in = 146,05 : largeur des pupitres à rails (relevé MFS, grand-format/plan.md)"),
    "pas_hauteur": dict(valeur=0.375 * POUCE, statut="estimée",
                        source="3/8 in = 9,525 : cran des rails (MFS, transpondeur/references.md) ; vérifié sur les deux "
                               "panneaux relevés : 66,3 = 7 crans − jeu, 56,8 = 6 crans − jeu"),
    "jeu": dict(valeur=0.015 * POUCE, statut="estimée",
                source="0,015 in = 0,38 : écart entre la cote nominale et les panneaux relevés (145,7 pour 146,05)"),
    "entraxe_rails": dict(valeur=122.0, statut="estimée", source="croquis de pupitre (MFS, etude-fabrication-pcb.md § 15)"),
    "entraxe_attaches_z": dict(valeur=3 * 0.375 * POUCE, statut="estimée",
                               source="28,58 = 3 crans entre deux attaches d'un même côté (transpondeur, references_replique.md)"),
}

# --- panneaux relevés (projet MFS) ; le nom du panneau réel ne sort jamais dans ce qui est public
RELEVES = {
    "radio_vhf": dict(largeur=145.7, hauteur=66.3, profondeur_reelle=140.0, statut="fiche",
                      source="fiches vendeur du panneau réel, 5,735 × 2,610 in (MFS, grand-format/plan.md)"),
    "transpondeur": dict(largeur=145.7, hauteur=56.8, profondeur_reelle=127.0, statut="fiche",
                         source="cockpit 3D 1:1 d'un add-on + plan coté d'une réplique (MFS, transpondeur/references_replique.md)"),
}

# --- règles de dessin (chacune vient d'un aller-retour du F-COM2 ou du transpondeur : methode/conception_boitier.md, pièges)
REGLES = dict(
    marge_lettres=0.8,       # trou d'attache / vis → bord d'une lettre
    bord_min=2.0,            # trou → bord du panneau : en dessous, le trou s'ouvre sur le bord en U (angles arrondis R 1)
    mur_min=1.2,             # cloison entre deux creux : 1,2 en FDM buse 0,4 (0,5 vu au F-COM2 : non imprimable) ; une plaque
                             # acrylique découpée au laser en tient moins (≈ 1,0, estimé) : regles=dict(mur_min=…)
    paroi_collerette=1.0,    # paroi d'une petite pièce PLA en buse 0,4 (fond 0,8)
    cap_min_fdm=2.8,         # hauteur de capitale minimale des lettres imprimées en buse 0,4
    largeur_lettre=0.72,     # chasse moyenne d'une capitale ≈ 0,72 × sa hauteur (Arial Bold) : encombrement approché
)

# --- empilage type d'un panneau rétroéclairé (y, mm) : façade jour / nuit sur embase, boîte à lumière, carte (F-COM2)
EMPILAGE = dict(plaque=3.0, embase=1.6, boite_lumiere=8.2, carte=1.6, parois_caisson=2.5, retrait_caisson=0.3)


def taille(crans, largeur_nominale=None):
    """Largeur et hauteur d'un panneau de `crans` crans de rail (cotes estimées : jeu retiré de la cote nominale)."""
    j = NORMES["jeu"]["valeur"]
    l = (largeur_nominale or NORMES["largeur_nominale"]["valeur"]) - j
    return round(l, 2), round(crans * NORMES["pas_hauteur"]["valeur"] - j, 2)


@dataclass
class Panneau:
    """Ce qu'on dessine à plat. ouvertures : dict(nom, x, z, l, h, r) (rectangle arrondi ; r = l / 2 = h / 2 pour un rond) ;
    inscriptions : dict(texte, x, z, cap, eclairee=True, vertical=False) (x, z = centre) ; attaches : (x, z) façade → caisson
    (vis dans une collerette, trou de rayon r_trou_attache) ; vis : (x, z) petites vis traversantes (fraisage de rayon r_vis) ;
    axes : (x, z) des axes qui traversent (encodeur…)."""
    nom: str
    largeur: float
    hauteur: float
    ouvertures: list = field(default_factory=list)
    inscriptions: list = field(default_factory=list)
    attaches: list = field(default_factory=list)
    vis: list = field(default_factory=list)
    axes: list = field(default_factory=list)
    r_trou_attache: float = 5.15     # collerette Ø 9,5 + 0,4 de jeu (fixations_facade.md)
    r_vis: float = 2.85              # fraisage d'une M3 ISO 7046 (Ø 5,5 + 0,1 de jeu)
    retrait_caisson: float = EMPILAGE["retrait_caisson"]
    parois_caisson: float = EMPILAGE["parois_caisson"]
    zone_lumiere: tuple = None       # (x0, x1, z0, z1) que la carte et la boîte à lumière couvrent ; défaut : l'intérieur du caisson

    def boite_inscription(self, i):
        """Encombrement approché (x0, x1, z0, z1) d'une inscription."""
        n = len(i["texte"]); cap = i["cap"]
        if i.get("vertical"):        # lettres empilées (ex. inscriptions de côté)
            w, h = cap * REGLES["largeur_lettre"], cap * (1.4 * n - 0.4)
        else:
            w, h = cap * REGLES["largeur_lettre"] * n, cap
        return i["x"] - w / 2, i["x"] + w / 2, i["z"] - h / 2, i["z"] + h / 2

    def interieur_caisson(self):
        """Zone (x0, x1, z0, z1) derrière la façade où la carte et la lumière peuvent aller (dans les parois du caisson)."""
        e = self.retrait_caisson + self.parois_caisson
        return -self.largeur / 2 + e, self.largeur / 2 - e, e, self.hauteur - e


def _dist_rect(x, z, b):
    """Distance d'un point à un rectangle (0 dedans)."""
    x0, x1, z0, z1 = b
    return math.hypot(max(x0 - x, 0, x - x1), max(z0 - z, 0, z - z1))


def _rect(o):
    return o["x"] - o["l"] / 2, o["x"] + o["l"] / 2, o["z"] - o["h"] / 2, o["z"] + o["h"] / 2


def _ecart_rects(a, b):
    """Plus petite distance entre deux rectangles (0 s'ils se touchent ou se chevauchent)."""
    return math.hypot(max(b[0] - a[1], a[0] - b[1], 0), max(b[2] - a[3], a[2] - b[3], 0))


def verifier(p, regles=None):
    """Contrôle du dessin à plat ; renvoie (erreurs, remarques) en texte et les affiche. Erreurs : trou trop près d'une lettre,
    cloison trop mince entre deux ouvertures, inscription éclairée hors de la zone de la carte (pas de LED possible derrière : VHF / COMM
    du F-COM2), lettres trop petites pour l'impression, trou hors du panneau. Remarques : trou d'attache ouvert en U."""
    R = dict(REGLES, **(regles or {})); err, rem = [], []
    lettres = [(i["texte"], p.boite_inscription(i)) for i in p.inscriptions]
    trous = ([("attache", x, z, p.r_trou_attache) for x, z in p.attaches] + [("vis", x, z, p.r_vis) for x, z in p.vis]
             + [("axe", x, z, 0.0) for x, z in p.axes])
    for t, x, z, r in trous:
        if not (-p.largeur / 2 < x < p.largeur / 2 and 0 < z < p.hauteur):
            err.append(f"{t} ({x:.2f} ; {z:.2f}) hors du panneau")
        for txt, b in lettres:
            d = _dist_rect(x, z, b) - r
            if d < R["marge_lettres"]:
                err.append(f"{t} ({x:.2f} ; {z:.2f}) à {d:.2f} de « {txt} » (≥ {R['marge_lettres']})")
        bord = min(p.largeur / 2 - abs(x), z, p.hauteur - z) - r
        if t == "attache" and bord < R["bord_min"]:
            rem.append(f"attache ({x:.2f} ; {z:.2f}) : {bord:.2f} jusqu'au bord → trou ouvert en U (angles R 1)")
        elif t != "attache" and bord < R["bord_min"]:
            err.append(f"{t} ({x:.2f} ; {z:.2f}) à {bord:.2f} du bord (≥ {R['bord_min']})")
        for o in p.ouvertures:
            d = _dist_rect(x, z, _rect(o)) - r
            if d < R["mur_min"]:
                err.append(f"{t} ({x:.2f} ; {z:.2f}) à {d:.2f} de l'ouverture {o['nom']} (≥ {R['mur_min']})")
    for k, a in enumerate(p.ouvertures):
        for b in p.ouvertures[k + 1:]:
            d = _ecart_rects(_rect(a), _rect(b))
            if d < R["mur_min"]:
                err.append(f"cloison de {d:.2f} entre {a['nom']} et {b['nom']} (≥ {R['mur_min']})")
    ci = p.zone_lumiere or p.interieur_caisson()
    for i, (txt, b) in zip(p.inscriptions, lettres):
        if i["cap"] < R["cap_min_fdm"]:
            err.append(f"« {txt} » : capitales de {i['cap']} < {R['cap_min_fdm']} (impression buse 0,4)")
        if i.get("eclairee", True) and not (ci[0] <= b[0] and b[1] <= ci[1] and ci[2] <= b[2] and b[3] <= ci[3]):
            err.append(f"« {txt} » éclairée mais hors de la zone de la carte (x {b[0]:.1f} → {b[1]:.1f}) : pas de LED possible derrière")
        for o in p.ouvertures:
            if _ecart_rects(b, _rect(o)) < R["marge_lettres"]:
                err.append(f"« {txt} » à moins de {R['marge_lettres']} de l'ouverture {o['nom']}")
    for e in err: print("DESSIN ERREUR", e, flush=True)
    for r_ in rem: print("DESSIN REMARQUE", r_, flush=True)
    print(f"CONTROLE DESSIN {p.nom} : {len(err)} erreur(s), {len(rem)} remarque(s)", flush=True)
    return err, rem


def chambres(p, marge=(3.0, 0.75)):
    """Une chambre de lumière par inscription éclairée (boîte à lumière, LED de la carte au fond) : son encombrement agrandi de
    `marge` (x, z) ; dict(nom, x, z, l, h). F-COM2 : ACTIVE 28 × 6,5 pour des capitales de 5."""
    out = []
    for i in p.inscriptions:
        if not i.get("eclairee", True): continue
        x0, x1, z0, z1 = p.boite_inscription(i)
        out.append(dict(nom=i["texte"], x=(x0 + x1) / 2, z=(z0 + z1) / 2, l=x1 - x0 + 2 * marge[0], h=z1 - z0 + 2 * marge[1]))
    return out


def jours_embase(chambres_, retrait=0.5):
    """Jours à ouvrir dans l'embase en face de chaque chambre (0,5 de moins en haut et en bas) : une embase pleine bouche le
    rétroéclairage de la plaque « jour / nuit » (oubli du F-COM2, 2026-10-27)."""
    return [dict(c, nom="jour_" + c["nom"], h=c["h"] - 2 * retrait) for c in chambres_]
