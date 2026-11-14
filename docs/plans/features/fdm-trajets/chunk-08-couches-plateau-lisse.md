# Chunk 08 — face sortie d'un plateau lisse, décomposée couche par couche

**Statut : `in-progress`** (2026-11-14, demandé par Lou : « découper méthodiquement les différents layers qui composent le matériau de
la référence, plutôt que faire des va-et-vient avec la ref ») · **Plan : [plan.md](plan.md)** · suit le chunk-07

## Référence
`<DONNEES>\fdm\references\6.webp` : façade noire du F-COM3 (PLA noir, plateau lisse, couches 0,2), tenue en main sous un plafonnier.
Une seule photo, un seul éclairage : chaque couche ci-dessous est notée **vue** (lisible sur la photo), **déduite** (cause physique
connue, à peine lisible) ou **à confirmer** (demande une autre photo).

## Méthode
1. Une couche = une cause physique = un réglage nommé, isolable (nœud nommé, interrupteur dans `procedes`).
2. Banc : un gros plan et une vue « photo » du studio de référence, rendus **couche par couche** (chaque couche seule sur la base,
   puis empilées) — planche `outils/planches/planche_plateau_lisse.py`.
3. Lou valide chaque couche sur la planche avant la suivante ; aucune valeur n'est réglée en comparant l'image entière.

## Les couches (de la plus grande à la plus fine)

| # | Couche | Sur la photo | Cause physique | Échelle | Ce qu'elle change | État au 2026-11-13 | À faire |
|---|---|---|---|---|---|---|---|
| 0 | **Matière** : PLA noir, diélectrique, IOR 1,46 | vue : gris anthracite satiné, teinte uniforme | colorant noir dans le PLA | — | base, rugosité moyenne | fiche `pla_noir` (base compensée pour ce studio) | vérifier la rugosité moyenne (taille du reflet) sur la planche |
| 1 | **Planéité** (gauchissement) | vue : le reflet du plafonnier est déformé, pas un rectangle net | retrait au refroidissement, plaque mince décollée du plateau | 20–80 mm, ± 5–30 µm | normale (relief très doux) | `LISSE_ONDULATION` 20 mm ± 4 µm | calibrer amplitude et taille sur la forme du reflet |
| 2 | **Brillance par zones** (contact plateau) | vue : grand reflet nuageux, zones mates et brillantes | écrasement et refroidissement variables du premier lit, contact inégal avec le plateau | 5–30 mm | rugosité seule (pas la teinte) | `LISSE_PLAQUES` 25 mm × 0,85–1,15 | isoler : planche avec la seule rugosité variable |
| 3 | **Bandes de trajets** | vue : stries diagonales **dans le reflet seulement**, plusieurs lignes ensemble | lignes du premier lit à pression un peu inégale : brillance qui varie de bande en bande | 0,4 mm (ligne), 1–3 mm (bande) | rugosité par ligne + anisotropie, relief presque nul | chunk-07 : sillons procéduraux (× 0,5), anisotropie 0,3 | ajouter une **rugosité par ligne** (bruit indexé par la phase) ; sillons quasi invisibles hors reflet |
| 4 | **Périmètres** autour des bords et des trous | déduite (anneaux autour des trous, à peine) | contours imprimés avant le remplissage | 0,4 mm | idem couche 3, orientation suivant le contour | dans les cartes de phase (chunk-07) | rien de neuf : même réglage que 3 |
| 5 | **Micro-rugosité du plateau lisse** | vue : l'aspect satiné (le reflet est large, pas miroir) | état de surface du plateau (PEI lisse / verre) recopié | < 0,05 mm | rugosité de fond | `GRAINS["lisse"]` ± 1,2 µm | relier à la rugosité de la couche 0 plutôt qu'à un relief |
| 6 | **Bord du premier lit** (pied d'éléphant) | vue : liseré sur l'arête basse, plus clair | premier lit écrasé qui déborde | 0,1–0,3 mm | géométrie de l'arête + Bevel | Bevel 0,3 | à confirmer sur une photo de tranche |
| 7 | **Couches de la tranche** | déduite (bords) | empilement des couches | 0,2 mm | relief procédural des tranches | chunk-07 (profil 6) | rien |
| 8 | **Lettres et anneau** (multi-matière) | vue : blanc opaque, bords nets, à fleur | première couche blanche, cœur naturel | — | albédo, pas de Bevel à la frontière | matière FDM `pla_blanc` sans Bevel | rien |
| 9 | **Usage** : traces de doigts, gras | vue : la tache claire au centre peut en être une (pièce tenue en main) | sébum | 5–20 mm | rugosité (plus brillant), pas l'albédo | non posé sur le PLA (règle de fdm_trajets.md) | **non** (Lou, 2026-11-14 : « poussière seule ») : pas de trace de doigt dans le rendu produit |
| 10 | **Poussière, fibres** | à confirmer (rien de net à cette distance) | électricité statique du PLA noir | 0,02–0,2 mm, épars | albédo clair, mat | non posé sur le PLA | **oui** (Lou, 2026-11-14) : `imperfections.appliquer(..., seulement="poussiere")`, fine et éparse |

## Réglages : un nœud par couche
Chaque couche multiplie sa contribution par un nœud Valeur nommé `couche_<nom>` (1 par défaut) : `couche_ondulation` (1),
`couche_plaques` (2), `couche_lignes` (3-4 : brillance par ligne et par bande), `couche_sillons` (3-4 : relief des cordons),
`couche_poussiere` (10). La planche les met à 0 / 1.

## Fichiers
- `material_library/matieres/procedes.py` (`plateau_texture`, `trajets`) : une couche = un nœud nommé, désactivable.
- `outils/planches/planche_plateau_lisse.py` (nouveau) : couches seules puis empilées, gros plan + vue « photo ».

## Critères de fin
- Chaque couche validée par Lou sur la planche, valeurs notées ici avec leur source.
- Couches 9 et 10 décidées le 2026-11-14 : pas de trace de doigt, poussière seule.

## Journal
- 2026-11-14 : couches 1, 2, 3, 10 codées avec leurs interrupteurs ; planche faite. Le moutonnement régulier de la vue d'ensemble venait de la **base** (`fdm()` : rugosité par un bruit unique de 2 mm), trouvé en éteignant toutes les couches : remplacé par `noeuds.bruit_multi` (Lou : « de l'aléatoire à différentes échelles »). Couches 2 et 3 baissées (vue d'ensemble trop marquée).
- 2026-11-14 : rugosité de base refaite (`noeuds.bruit_zones` : 25 mm, 4,5 octaves, rugosité de bruit 0,7, contraste) après visualisation du champ seul (vue de face en émission) ; validée par Lou sur la façade (« parfait »).
