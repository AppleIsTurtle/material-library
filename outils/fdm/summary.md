# summary — outils/fdm/

Outils d'étude des vrais trajets FDM avec OrcaSlicer (feature [fdm-trajets](../../docs/plans/features/fdm-trajets/plan.md),
chunk-01, 2026-10-27) ; tous en Python système (numpy, Pillow). OrcaSlicer 2.4.2 portable : `F:\OrcaSlicer\2.4.2`. Sorties
hors git : `G:\Blender\Bibliotheque\fdm\orca\` (Orca) et `G:\Blender\Bibliotheque\fdm\simulation\` (nous, comparaisons). Ce qu'on en a appris : [methode/fdm_trajets.md](../../methode/fdm_trajets.md).

| Fichier | Rôle | Dépendances |
|---|---|---|
| profil.py | Réglages d'un profil OrcaSlicer, héritage résolu ; `--aplatir` écrit le profil complet | OrcaSlicer (profils système) |
| trancher.py | Tranche des STL (une pièce, ses matières assemblées) avec le profil U1 par défaut + variantes `--set` → plate_1.gcode | profil.py, OrcaSlicer |
| gcode.py | G-code d'Orca → trajets.npz (segments typés, largeur, hauteur), bilan.json (largeurs, pas et angles du dessus, coutures), PNG des couches | numpy, Pillow |
| planche_orca.py | Planche des vrais trajets (embase, bouton TFR, buses 0,4 / 0,2, variantes) → planche_orca.png | gcode.py |
| comparer.py | Nos trajets (tranchage.py) contre ceux d'Orca : longueurs et largeurs par type, pas et angle du dessus par couche, axe des parois extérieures, coutures, couverture visible ; seuils du chunk-02 ; superpositions | gcode.py, shapely |
| planche_comparaison.py | Planche « Orca · nous · superposition » de tous les cas → simulation/planche_comparaison.png | comparer.py |

## Historique
- 2026-10-27 : création (chunk-01 de fdm-trajets).
- 2026-10-28 : planche_orca.coutures repère aussi les débuts après un déplacement (chunk-05).
- 2026-10-28 : comparer.py, planche_comparaison.py ; gcode.bilan repère aussi les débuts de chemin après un déplacement (chunk-02).
