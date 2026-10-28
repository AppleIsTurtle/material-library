# summary — outils/essais/

Essais « dans une scène vide » (`blender -b --factory-startup --python …`) : chaque fonction de la bibliothèque marche seule.

| Fichier | Rôle | Dépendances |
|---|---|---|
| essai_aretes.py | Essaie plaque, coupe (congé, chanfrein, encoche), retrancher, aretes_vives, adoucir, lisser, bevel_rendu, aretes_douces ; « ESSAI ARETES OK » | Blender 5.1, material_library.aretes |
| essai_matieres.py | Construit chaque fiche du catalogue par son nom (Bevel compris, pas de doublon), aller-retour des couleurs ; « ESSAI MATIERES OK » | Blender 5.1, matieres.catalogue |
| essai_procedes.py | Chaque procédé sur une plaque, vrais trajets FDM (`reglages_fdm.imprimer` sur la plaque), lettres sur les .npz de la planche, décalque d'encre ; « ESSAI PROCEDES OK » | Blender 5.1, matieres.procedes, impression.decalques, Python système + Pillow |
| essai_reglages_fdm.py | Add-on « Impression FDM » enregistré ; `reglages_fdm.imprimer()` et le bouton « Recalculer les trajets » donnent les mêmes cartes ; buse 0,2 + 1 paroi change le résultat sans empiler la matière ; grain du plateau limité au contact ; UV existantes gardées ; fichiers à côté du .blend ; objet lié refusé ; « ESSAI REGLAGES FDM OK » | Blender 5.1, matieres.reglages_fdm, Python système (numpy, scipy, shapely, Pillow) |
| essai_bibliotheque.py | `ouvrir` : la bibliothèque s'ouvre, chaque asset a aperçu et catalogue, images packées, aperçus exportés ; `studio` : chaque matière ajoutée (append) dans le studio du site rend comme sur la planche du chunk-03 (écart ≤ 2) | Blender 4.4 ou 5.1 (lit `bibliotheque/blender_<sa version>/`), releve_quick.json |

## Historique
- 2026-10-27 : essai_aretes.py (chunk-02).
- 2026-10-27 : essai_matieres.py (chunk-03).
- 2026-10-27 : essai_procedes.py (chunk-04).
- 2026-10-27 : essai_bibliotheque.py (chunk-06).
- 2026-10-28 : essai_reglages_fdm.py (fdm-trajets, chunk-04).
- 2026-10-28 : essai_procedes.py passe aux trajets (chunk-05).
- 2026-10-28 : essai_bibliotheque.py lit la bibliothèque de la version de Blender qui le lance (4.4 ou 5.1).
