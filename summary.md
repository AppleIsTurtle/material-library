# summary — material-library/ (racine)

Bibliothèque commune de Lou (créée le 2026-10-27, depuis le projet MFS) : matières, looks par procédé, arêtes, visserie,
imperfections, méthode de conception d'un boîtier. Plan : [docs/plans/MASTER.md](docs/plans/MASTER.md).

| Fichier / dossier | Rôle | Dépendances |
|---|---|---|
| LICENSE | Licence MIT (code, matières et bibliothèque .blend) | — |
| AGENTS.md | Guide pour une IA qui utilise la bibliothèque depuis un autre projet : points d'entrée, exemple testé, pièges | — |
| CLAUDE.md | Règles du dépôt (noms, versions, données hors git, non-régression, règles de Lou, travail à plusieurs sessions) | — |
| README.md | Comment l'importer depuis un projet | — |
| material_library/ | Le paquet Python importé par les scripts Blender des projets ([summary](material_library/summary.md)) | Blender 5.1 (bpy, bmesh) |
| outils/ | Outils du dépôt, dont la non-régression des assets ([summary](outils/summary.md)) | Blender 5.1, Python |
| blender/ | Construction du `.blend` « bibliothèque de matières » (chunk-06) ([summary](blender/summary.md)) | material_library |
| bibliotheque/ | La bibliothèque de matières générée, à déclarer dans Blender : `blender_4.4/` et `blender_5.1/` ([summary](bibliotheque/summary.md)) | blender/construire_bibliotheque.py |
| methode/ | Méthode écrite : arêtes, matières, procédés, fixations, conception d'un boîtier ([summary](methode/summary.md)) | — |
| skill/ | Source du skill Claude global « material-library » (chunk-08), installé par jonction dans `~/.claude/skills/` ([summary](skill/summary.md)) | — |
| docs/plans/ | MASTER.md (plan) et chunks 01 à 09 ([summary](docs/plans/summary.md)) | — |

Données lourdes hors git : `G:\Blender\Bibliotheque\` (cartes d'images, planches, archives). Dépôt GitHub public :
https://github.com/AppleIsTurtle/material-library.

## Historique
- 2026-10-27 : création (chunk-01) : squelette, règles, non-régression, import depuis MFS (`MFS/outils/bibliotheque_commune.py`).
- 2026-10-28 : dépôt public (version 0.3.1) ; l'imprimeur FDM n'est plus nommé ; l'historique de travail d'avant reste privé.
- 2026-10-28 : AGENTS.md et skill « material-library » (chunk-08), chemins réglables par variables d'environnement.
- 2026-10-28 : renommé material-library (dépôt, dossier, paquet `material_library`, add-on), licence MIT (version 0.3.0).
- 2026-10-28 : bibliotheque/ (matières pour Blender 4.4 et 5.1, suivies par git), dépôt GitHub privé.
