# Chunk 09 — brancher MFS sur material-library

**Statut : `pending`** · **Plan : [MASTER.md](MASTER.md)** · dépend des chunks 02 à 07

## But
Les maquettes de MFS utilisent la bibliothèque au lieu de leurs copies locales, sans que leurs rendus changent.

## Fichiers (MFS)
- `boitier/scripts/maquette_grand_format.py` : matières, arêtes, vis, imperfections, contrôles pris dans `material_library` ; les
  fonctions locales retirées (`mat_uniforme`, `peinture_acrylique`, `pla_imprimeur`, `inox_noirci_use`, `bevel_rendu`, `adoucir`,
  `uv_plan_mm`…).
- `boitier/scripts/fixations.py` : remplacé par un renvoi vers le dépôt, puis retiré ; `docs/methodes/fixations_facade.md` : lien
  vers la version du dépôt.
- `boitier/scripts/maquette_replique.py` (transpondeur) : passe aux fixations standard (attaches en collerette, petites vis à
  fleur) — c'est un changement d'aspect, à montrer à Lou en aperçus avant tout rendu final.
- `summary.md` des dossiers touchés, `VERSIONS.md`, `ASSETS.md`.

## Fini quand
- F-COM2 réplique et noire : dumps identiques avant / après (maillages, positions, visibilité ; seuls les noms de matières peuvent
  changer, listés) et aperçus identiques à l'œil ;
- transpondeur : aperçus validés par Lou avec les fixations standard ;
- l'asset du F-COM1 n'a pas bougé.

## Watch-outs
- Migrer un domaine à la fois (arêtes, puis matières, puis vis), avec la non-régression à chaque pas.
- Le transpondeur relève d'une autre session : prévenir Lou avant d'y toucher.
- Commits : seulement les fichiers de ce chunk (l'index git est partagé).
