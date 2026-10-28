# summary — outils/

| Fichier | Rôle | Dépendances |
|---|---|---|
| non_regression.py | Dump d'un .blend (maillages, matières, positions, visibilité) dans Blender, puis comparaison de deux dumps (tolérance 0,002) ; code 0 = identiques | Blender 5.1 (dump), Python (comparaison) |
| planches/ | Planches de contrôle dans le studio du site (voir [planches/summary.md](planches/summary.md)) | hero.blend (lecture), Pillow |
| essais/ | Essais des fonctions dans une scène vide (voir [essais/summary.md](essais/summary.md)) | Blender 5.1 |
| fdm/ | Étude des vrais trajets FDM avec OrcaSlicer (profils, tranchage, lecture du G-code, planche) : [fdm/summary.md](fdm/summary.md) | Python système, OrcaSlicer 2.4.2 |

## Historique
- 2026-10-27 : non_regression.py (repris de la vérification de la version noire du F-COM2, MFS).
- 2026-10-27 : planches/ et essais/ (chunk-02).
- 2026-10-27 : fdm/ (feature fdm-trajets, chunk-01).
