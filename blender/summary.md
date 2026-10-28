# summary — blender/

Construction du .blend « bibliothèque de matières » pour l'Asset Browser de Blender (chunk-06). Le .blend généré est suivi par git :
`bibliotheque/blender_<X.Y>/bibliotheque_matieres.blend` (+ `blender_assets.cats.txt`), un par version de Blender qui lance le script
(4.4 : `F:\Blender\blender.exe`, 5.1 : `F:\Blender\5.1\blender.exe`) ; archives hors git dans `G:\Blender\Bibliotheque\_archives\`. Déclaration dans
Blender : [methode/matieres.md](../methode/matieres.md) § Bibliothèque dans Blender.

| Fichier | Rôle | Dépendances |
|---|---|---|
| scripts/addons/material_library_fdm/ | Add-on « Material library — Impression FDM » : enregistre `material_library.matieres.reglages_fdm` (panneau et bouton « Recalculer les trajets ») ; installation : README.md § Panneau Impression FDM | material_library |
| construire_bibliotheque.py | Écrit dans `bibliotheque/blender_<version de Blender>/` ; scène vide en mm → une matière par fiche du catalogue + variantes FDM + 7 pièces de visserie, marquées assets (catalogues à uuid stables, descriptions des fiches, auteur), aperçus rendus en Cycles, images packées ; archive l'ancien fichier puis enregistre ; `quick` = aperçus rapides | Blender 4.4 ou 5.1, material_library (catalogue, procedes, visserie.pieces, imperfections.uv_mm) |

## Historique
- 2026-10-27 : création (vide).
- 2026-10-27 : construire_bibliotheque.py (chunk-06).
- 2026-10-28 : scripts/addons/material_library_fdm/ (fdm-trajets, chunk-04).
- 2026-10-28 : descriptions des 4 matières FDM : couches procédurales, vrais trajets par le panneau (chunk-05).
- 2026-10-28 : add-on en version 0.2.3 (réglage « Grain du plateau ») ; vérifié chargé dans les préférences de Lou.
- 2026-10-28 : la bibliothèque s'écrit dans le dépôt (`bibliotheque/blender_<X.Y>/`, suivie par git) ; construite aussi par Blender 4.4.
