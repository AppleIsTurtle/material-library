# Fixations standard des façades

Règle commune à toutes les façades des projets de Lou (F-COM2, transpondeur, panneaux suivants), validée par Lou le 2026-10-27 :
« il faut standardiser ces éléments pour notre projet », d'après une photo de panneaux d'origine dans un cockpit, puis « des vis
accessibles à un prix correct, des vis standards ». Déplacée de MFS (`docs/methodes/fixations_facade.md`) au chunk-05.

Code : [`material_library/visserie/`](../material_library/visserie/summary.md) — cotes des normes dans `normes.py`, géométrie des
attaches et des vis à fleur dans `fixations.py` (`ATTACHE`, `VIS_FLEUR`, `attache_cotes()`, `fleur_cotes()`), pièces complètes par
leur désignation dans `pieces.py` (`vis("M4 x 8 DIN 84 inox A2", …)`), matières dans `shading.py`. Chaque maquette les appelle au
lieu de dessiner ses propres vis.

**Visserie du commerce** (normes DIN / ISO, en vente partout) : pas de Dzus (pièces d'avion ou imitations de cockpit maison), pas
de têtes peintes sur mesure (minimum de commande). Seule pièce faite pour nous : la **collerette** des attaches (« on garde les
collerettes autour des vis principales », Lou), imprimée avec les cadres.

## 1. Attaches (façade → caisson)
Ce que montre la référence : une tête cylindrique à fente (Dzus) entourée d'un œillet, dans un trou de la façade un peu plus large
(anneau d'ombre). Notre équivalent :

| Élément | Standard |
|---|---|
| Vis | **M4 × 8 à tête cylindrique fendue, DIN 84 / ISO 1207, inox A2** : tête Ø 7 × 2,6, fente 1,2 × 1,1 (la plus proche d'une Dzus) |
| Collerette | coupelle en **PLA noir imprimé chez l'imprimeur FDM** (buse 0,4 : parois de 1,0, fond de 0,8 ; Lou 2026-10-27 ; résine JLC en secours), **Ø 9,5** (l'œillet des vraies Dzus), alésage Ø 7,5 (0,25 autour de la tête), fond 0,8 percé Ø 4,4 sur lequel la tête appuie, bord extérieur arrondi R 0,4 ; posée sur l'embase, **sommet à fleur de la façade** |
| Trou de la plaque | Ø 10,3 (collerette + 0,4 de jeu) ; s'il reste moins de 2 mm jusqu'au bord, il s'ouvre sur le bord en **U**, angles de l'encoche **arrondis R 1** (entrée du U), **bord avant du trou arrondi (congé 0,6)** |
| Hauteur | fond de la collerette + tête = 3,4 pour une plaque de 3,0 : la tête **dépasse de 0,4** de la façade, comme une Dzus |
| Fixation | dans l'insert M4 de la colonne du caisson (≥ 2 mm de matière autour de l'insert, jamais de colonne qui ressort du flanc) |
| Place | sur les bords latéraux, dans l'alignement des inscriptions verticales, à ≥ 0,8 des lettres |

Autre taille : `attache_cotes(d)` garde les mêmes règles (alésage = tête + 0,25, paroi 1,0, fond 0,8, jeu du trou 0,4) ; une
attache M3 DIN 84 donne une collerette Ø 8,0 dans un trou Ø 8,8.

## 2. Petites vis (traversent la façade)
| Élément | Standard |
|---|---|
| Vis | **M3 fraisée 90° cruciforme ISO 7046, acier oxydé noir** (ou inox noirci), à fleur de la face avant (Ø 5,5 × 1,65) ; longueur selon l'empilage (F-COM2 : M3 × 18), écrou au dos de la carte |
| Fraisage | 90°, 0,1 de jeu autour de la tête, **arête arrondie R 0,25** (pas d'arête vive) |

## Rendu (maquettes)
- Petites vis : matière d'après une vraie photo (DIN 965 oxydées noires) : gris anthracite satiné, marbré, fin piqueté, usure claire
  sur les arêtes, micro-rayures et frottements (cartes de `G:\Blender\Bibliotheque\imperfections`) lus sur des **UV dépliés en mm**
  (sans déformation, `imperfections/uv_mm.py`) ; **nœud Bevel R 0,2** sur la normale (arêtes arrondies au rendu) en plus du biseau du
  maillage (`shading.acier_oxyde_noir`).
- Attaches : inox A2 naturel, gris clair uniforme (`shading.inox_naturel`), biseau 0,2 + Bevel R 0,2.
- Collerettes : PLA noir imprimé (couches de 0,2), sans grain de ponçage.

## 3. Comment choisir une vis
1. **Une norme courante, pas un modèle de catalogue.** Désigner la vis par sa norme, son diamètre, sa longueur et sa matière
   (« M4 × 8 DIN 84 inox A2 ») : n'importe quel vendeur la fournit, à l'identique. Normes courantes chez tous les vendeurs
   (`normes.py`) : DIN 84 / ISO 1207 (cylindrique fendue), ISO 7045 (bombée cruciforme), ISO 7046 / DIN 965 (fraisée cruciforme),
   ISO 4762 / DIN 912 (BTR), écrous ISO 4032 / DIN 934, rondelles DIN 125, inserts laiton à chaud (ruthex : M2, M3, M4).
2. **Disponible chez au moins trois vendeurs**, en petit lot (25 à 100) comme en gros (500 à 1000) : sinon on change de vis, pas de
   vendeur. Les tailles M2,5, M5 et les têtes peintes ne se trouvent que chez les spécialistes : à éviter.
3. **Inox A2 par défaut** (ne rouille pas, aspect métal qui se voit) ; **acier oxydé noir** quand la tête doit disparaître sur une
   façade sombre (l'oxyde s'use un peu sur les arêtes : c'est voulu) ; **inox noirci** (A2 + traitement noir) si l'humidité compte.
4. **Longueurs du commerce** : 4, 5, 6, 8, 10, 12, 16, 18, 20 ; on dessine l'empilage autour, pas l'inverse. Une fraisée se mesure
   tête comprise, les autres sous la tête.
5. **L'argent là où ça se voit** : les vis visibles (attaches, petites vis de façade) sont choisies pour leur aspect ; celles du dos
   (cartes, supports) au moins cher, de la même norme.

### Prix relevés (2026-10-27, au détail, port non compris)
| Vis | Vendeurs | Prix |
|---|---|---|
| M4 × 8 DIN 84 inox A2 | bolts.co.uk (25 pièces), Fabory (petit lot), SFS (boîte de 500), Rubix / Spartex (1000) | ≈ 5 £ les 25 (0,20–0,25 € pièce) ; 12,10 £ HT les 1000 en A2-50 (≈ 0,015 € pièce) |
| M3 ISO 7046 / DIN 965 inox A2 | RS (100 pièces, Pozi M3 × 5 : 8,46 € HT ; 500 pièces M3 × 8 : 30,65 € HT), SFS, Würth | ≈ 0,06–0,09 € pièce |
| M3 DIN 965 acier oxydé noir | CDE Fasteners (4000 pièces M3 × 6 : 120,51 $), spécialistes (monsterbolts…) | ≈ 0,03 € pièce en gros ; aucun petit lot trouvé chez les généralistes le 2026-10-27 (ManoMano : « galvanisé noir », autre finition) : commander tôt, ou inox noirci |
| M3 ISO 7045 inox A2 | SFS (4,90 à 14,30 CHF les 100 selon la longueur), RS / Bossard, accu.co.uk | ≈ 0,05–0,14 € pièce |
| M3 ISO 4762 inox A2 | pts-uk.com (4,96 £ HT les 100 ; 2,39 £ les 100 par 1000), accu.co.uk | ≈ 0,03–0,06 € pièce |
| Collerette | imprimée chez l'imprimeur FDM | quelques centimes de PLA |

Par boîtier F-COM2 (4 attaches + 7 petites vis) : ≈ 2 € au détail, < 0,50 € en gros. Sources : bolts.co.uk, uk.rubix.com,
fr.rs-online.com (914-1765, 264-6476), cdefasteners.com, sfs.ch, pts-uk.com, 3djake.ch (inserts ruthex).

## 4. Règles de forme
- Pas d'arête vive : têtes, collerettes, fraisages et encoches arrondis ou chanfreinés ; on garde les rayons de coin propres à chaque
  façade.
- ⚠ Façade « jour / nuit » (acrylique translucide peint) : le fraisage et le trou des attaches mettent l'acrylique à nu ; les faire
  **avant la peinture** (ou peindre l'intérieur), sinon un liseré s'allume la nuit autour des vis.
- À trancher : une tête de M2,5 sur un trou de M3 (transpondeur) — rien n'est figé dans le code.

## Appliqué à
- F-COM2, réplique (2026-10-27) : `maquette_grand_format.py` de MFS (la version noire garde ses vis à fente et ses godets) ; branchement
  sur la bibliothèque : chunk-09.
- Transpondeur : à faire (`maquette_replique.py` a encore ses propres Dzus et vis bombées).
