# Chunk 01 — créer le dépôt material-library

**Statut : `done`** (2026-10-27) · **Plan : [MASTER.md](MASTER.md)**

## But
Le dépôt existe, vide de fonctions mais prêt : structure, règles, import depuis MFS, outil de non-régression.

## Fichiers
- Nouveau dépôt (emplacement à confirmer : `D:\Claude\material-library\`) : `CLAUDE.md` (règles reprises de MFS : français,
  noms en minuscules, `summary.md` partout, chemins relatifs au script sauf éditeur Blender, archives), `README.md`,
  `summary.md`, `docs/plans/MASTER.md` (= ce plan, déplacé ; MFS garde un lien), dossiers vides du paquet `material_library/`
  avec leur `summary.md`, `.gitignore` (`.blend`, `.blend1`, `__pycache__`, `.log`).
- `material_library/__init__.py` : version (`__version__`), chemin des données lourdes (`G:\Blender\Bibliotheque\` à confirmer).
- `outils/non_regression.py` : dump d'un `.blend` (maillages : sommets, faces, encombrement, matrices ; matières ; visibilité)
  et comparaison de deux dumps (repris de `dump.py` du 2026-10-27).
- MFS : `outils/material_library.py` (ajoute le dépôt à `sys.path`, vérifie la version attendue) ; `VERSIONS.md` (ligne
  « material-library ») ; `docs/plans/features/summary.md` (statut).
- Mémoire : nouvelle entrée « dépôt material-library » (chemin, import, règles).

## Fini quand
Le dépôt est créé (git init, premier commit), MFS l'importe depuis un script Blender lancé par `blender_garde.ps1` sans erreur,
et `non_regression.py` compare deux dumps identiques (asset F-COM2 réplique) avec 0 différence.

## Watch-outs
- Nom, GitHub (privé ou local) et emplacement du `.blend` : à trancher avec Lou **avant** ce chunk.
- Ne rien déplacer de MFS ici : seulement créer ; la migration est le chunk-09.
- L'index git de MFS est partagé avec d'autres sessions : ne rien indexer sans commiter aussitôt.

## Fait (2026-10-27)
- Dépôt `D:\Claude\material-library\` (git local ; publication GitHub à demander à Lou), squelette, `CLAUDE.md`, `README.md`,
  `summary.md` partout, `.gitignore`, `material_library/__init__.py` (version 0.1.0, `DONNEES = G:\Blender\Bibliotheque`).
- `outils/non_regression.py` : dump de l'asset F-COM2 réplique (529 maillages) comparé à lui-même → 0 différence, code 0.
- MFS : `outils/bibliotheque_commune.py` (`charger()` ; le nom `material_library.py` masquait le paquet) : import vérifié dans
  Blender 5.1.2.
