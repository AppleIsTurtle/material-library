# Chunk 02 — notre simulation de tranchage, calibrée sur OrcaSlicer

**Statut : `done`** (2026-10-28 : `tranchage.py` réécrit, `outils/fdm/comparer.py` et `planche_comparaison.py` ; embase 0,4 / 0,2,
TFR 0,4 et variantes : tous les seuils ; TFR 0,2 : 4 / 6, écart limité aux bouts des nervures de 0,6 mm ; détail et écarts connus :
[methode/fdm_trajets.md](../../../../methode/fdm_trajets.md) § Notre simulation ; seuils révisés : l'IoU des cordons remplacé par la
distance entre axes des parois, l'angle comparé couche par couche) · **Plan : [plan.md](plan.md)** · dépend du chunk-01

## But
Remplacer `material_library/impression/tranchage.py` par une simulation générale qui produit, pour n'importe quelle pièce et
n'importe quels réglages, des **trajets** (polylignes typées avec largeur et hauteur, couche par couche) proches de ceux d'Orca,
sans avoir besoin d'Orca pour les rendus.

## Ce que la simulation doit savoir faire
- **Orientation** : la face posée sur le plateau et l'axe de montée sont des paramètres (aujourd'hui : toujours −y).
- **Réglages** : buse (0,4 / 0,2) → hauteur de couche et largeurs par défaut (celles relevées au chunk-01, pas les valeurs
  actuelles 0,45 / 0,22 si Orca dit autre chose) ; nombre de contours (1, 2, 3) ; motif du dessus (au minimum ceux retenus au
  chunk-01, dont monotone et concentrique) et son angle ; couture (alignée, arrière, aléatoire).
- **Tous les dessus** : toute zone d'une couche qui n'est pas couverte par la couche du dessus est un « dessus » (marches,
  bossages, fond des lamages), pas seulement la dernière couche.
- **Contours** autour du bord et de chaque trou, dans l'ordre et avec le recouvrement relevés au chunk-01 ; demi-tours des
  lignes du dessus ; petits espaces remplis comme Orca (ou laissés vides s'il les laisse).
- **Ponts** sous les surplombs, comme aujourd'hui.
- **Multi-matière** (choix de Claude, 2026-10-27) : chaque matière d'une pièce (un objet / un STL par couleur : bouton TFR =
  noir + flèche blanche + guide naturel, façade du F-COM1 + lettres) est tranchée comme une région à part, avec ses propres
  contours et son propre dessus — c'est ce que fait un trancheur ; vérifier au chunk-01 sur le bouton TFR multi-matière d'Orca.
  Les cartes restent par objet Blender.
- Sortie : un `.npz` (ou format au choix du chunk) contenant les trajets visibles (tranches, dessus, ponts) — le rendu (chunk-03)
  en tire ses cartes. Garder la compatibilité avec `appliquer_traces` n'est **pas** demandé : elle sera remplacée.

## Comparaison avec Orca
`outils/fdm/comparer.py` (nouveau) : même pièce, mêmes réglages → nos trajets et ceux du G-code (lecteur du chunk-01) superposés
en image, et des écarts chiffrés : largeur moyenne des cordons, pas et angle des lignes du dessus, nombre de tours, position de
la couture, part de la surface couverte. Seuils à fixer au début du chunk d'après ce qui se voit à l'œil sur un gros plan
(proposition : pas et largeur à ± 5 %, angle à ± 1°, même nombre de tours, couverture à ± 2 %).

## Fichiers
- `material_library/impression/tranchage.py` (réécrit ; Python système : numpy, scipy, shapely) ; `outils/fdm/comparer.py` ;
  `summary.md` des dossiers touchés.
- Hors git : `G:\Blender\Bibliotheque\fdm\simulation\` (sorties et images de comparaison).

## Fini quand
Pour l'embase et le bouton TFR, buses 0,4 et 0,2, réglages par défaut d'Orca : la comparaison passe les seuils et la superposition
ne montre pas de différence visible au zoom d'un rendu gros plan.

## Watch-outs
- Temps et mémoire : l'embase (≈ 145 × 66 mm) en buse 0,2 = beaucoup de couches et de lignes ; mesurer, et ne garder en
  mémoire que ce qui est visible (contours extérieurs des tranches, dessus, ponts).
- La simulation tourne hors de Blender (Python système) : elle lit un STL ou un maillage exporté, jamais un `.blend`.
