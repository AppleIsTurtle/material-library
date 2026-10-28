# summary — material_library/visserie/

Visserie du commerce par sa désignation normalisée (« M4 × 8 DIN 84 inox A2 ») : vraie géométrie, vrai shading. Règle des
fixations de façade : [methode/fixations_facade.md](../../methode/fixations_facade.md). Plan : [chunk-05](../../docs/plans/chunk-05-visserie.md).

| Fichier | Rôle | Dépendances |
|---|---|---|
| __init__.py | Marque le sous-paquet | — |
| normes.py | Tables DIN / ISO (DIN 84, ISO 7045, ISO 7046 / DIN 965, ISO 4762, ISO 4032, DIN 125, inserts ruthex), pas ISO 261, sources ; `cotes()`, `designation()`, `croix_rendu()`, `passage()` | Python pur (testable hors Blender) |
| fixations.py | Géométrie bmesh des têtes (cylindrique fendue, bombée, fraisée, BTR : `tete()`) et des fixations de façade (collerette, trou en U à congé, vis à fleur, fraisage) ; `ATTACHE` / `VIS_FLEUR` = cotes du F-COM2, `attache_cotes()` / `fleur_cotes()` pour une autre norme ou taille | normes.py, `material_library.aretes` (coupe, encoche_u, contour_cercle) |
| filets.py | Filet ISO réel (hélice à 60°), tige, écrou ISO 4032 taraudé, rondelle DIN 125, insert laiton moleté (bmesh) | normes.py |
| shading.py | Matières : `inox_naturel` (V3_vis_grise de MFS), `acier_oxyde_noir` (= `inox_noirci_use` de MFS, d'après photo DIN 965), `tete_peinte`, `laiton` ; `bevel_tete` (Bevel R 0,2) | imperfections/ (cartes sur UV en mm), `matieres.noeuds.neuf`, `matieres.couleurs.srgb`, `material_library.aretes.bevel_rendu` |
| pieces.py | Désignation → objets Blender habillés : `vis()`, `ecrou()`, `rondelle()`, `insert()`, `piece()` ; booléens appliqués, biseau, UV en mm ; noms par `prefixe` (GF_VIS_*… des maquettes) | tous les modules ci-dessus, `material_library.aretes` (retrancher, adoucir) |

Planche de contrôle : [outils/planches/planche_visserie.py](../../outils/planches/planche_visserie.py) (rendus dans
`G:\Blender\Bibliotheque\planches\visserie\`), validée par Lou le 2026-10-27.

Non-régression (2026-10-27) : `fixations.py`, `filets.tige()` et `filets.ecrou()` redonnent exactement les maillages de MFS
(`boitier/scripts/fixations.py`, `tige()` / `ecrou()` de `maquette_grand_format.py`) : 15 pièces comparées, écart 0.

## Historique
- 2026-10-27 : création (chunk-01).
- 2026-10-27 : chunk-05 — normes.py, fixations.py (repris de MFS, paramétré par la norme), filets.py (visserie_photoreal + tige /
  ecrou / tube_y de la maquette), shading.py, pieces.py.
