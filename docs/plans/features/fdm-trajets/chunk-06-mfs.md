# Chunk 06 — MFS : embase de la réplique, bouton TFR, autres pièces FDM

**Statut : `in-progress`** (2026-10-28 : F-COM2 fait — embase, boîte à lumière, cadres, collerettes, boutons TFR / TEST, plaque
noire sur plaque granuleuse, Weighted Normal sur toutes les pièces (MFS 4dadb60, 4566e0e, 35dd1c9), assets régénérés en 0.2.3,
15 plans rendus en local ; bouton TFR du F-COM1 écrit puis refait en 0.2.3 dans `boitier.blend` (MFS a99eaef, a897aca), plans du
site re-rendus. **Lou, 2026-10-28 : on ne travaille plus sur le F-COM1, seulement sur le F-COM2** : façade Satin Grey et lettres
du F-COM1 abandonnées ; reste : transpondeur) ·
**Plan : [plan.md](plan.md)** · dépend du chunk-05 (et de l'avancement du chunk-09 du MASTER : migration
de MFS)

## But
Les deux défauts vus par Lou disparaissent de ses rendus, puis toutes les pièces FDM de MFS passent au nouveau PLA.

## Ordre
1. **Embase de la F-COM2 réplique** (`GF_EMBASE`, `D:\Claude\MFS\boitier\f-com\commun\scripts\maquette_grand_format.py`, branche
   `FAC == "acrylique"`, ~l. 1066-1078) : PLA noir de l'imprimeur FDM, **face avant sur le plateau** (Lou, 2026-10-27) → grain du PEI
   sur la face, cordons et couture sur les tranches (bords extérieurs et bords des fenêtres, du TFR, du COMM TEST, des vis), dessus
   en lignes au dos. Vérifier aussi la F-COM2 noire (même embase, `version=noire`).
   Plans fixes de `G:\Blender\MFS\plans_fixes\grand_format\` refaits (aperçus puis rendus finaux, skill `rendu-distant` pour
   les finaux).
2. **Bouton TFR du F-COM1** : supprimer les « plaques » — cause trouvée au chunk-03 : `boitier/commun/scripts/imperfections.py`
   (appelé par `asset_boitier.py`, l. 71, sur toutes les matières) met des cartes de rugosité « frottements » (tuile 17 mm) et
   « traces de doigts » (60 mm) ; les retirer (ou les réduire fortement) sur les matières FDM — et poser le nouveau PLA (face sur le plateau,
   couches sur les flancs). ⚠ C'est l'asset `G:\Blender\MFS\assets\boitier\boitier.blend` (shading retouché par Lou, référence) :
   archiver avant, reporter la retouche dans les scripts (`build_boitier.py` / `asset_boitier.py -- maj`), montrer avant / après,
   accord de Lou avant d'écraser. Le MASTER met la régénération de l'asset du F-COM1 hors périmètre : cette exception est demandée
   par Lou (2026-10-27).
3. **Autres pièces FDM de MFS** (inventaire au début du chunk : `pla_imprimeur`, `M_CADRE`, `M_COLL_LISSE` de la maquette,
   `photoreal.pla_fdm` / `pla_tous` du F-COM1, transpondeur…) : une par une, avant / après.

## Branchement (choix de Claude, 2026-10-27, sans attendre le chunk-09 du MASTER)
- F-COM2 : `maquette_grand_format.py` n'importe pas encore material-library (vérifié le 2026-10-28 : aucun script de MFS n'appelle
  `MFS/outils/bibliotheque_commune.py`) ; il l'importe par ce module pour ses seules matières FDM (migration partielle,
  compatible avec le chunk-09 qui fera le reste).
- F-COM1 : la chaîne de l'asset (`asset_boitier.py`, `photoreal.pla_tous`) importe material-library **pour la seule matière FDM**
  (pas de copie dans `photoreal.py` : « une fonction = une vérité ») ; c'est l'exception au MASTER demandée par Lou.

⚠ material-library est en **0.2.0** (tag `v0.2.0`, fdm-trajets) : passer `VERSION_ATTENDUE = "0.2"` dans
`D:\Claude\MFS\outils\bibliotheque_commune.py` (sinon l'import refuse la bibliothèque) et noter la version dans `VERSIONS.md`.

## Fichiers (MFS)
`maquette_grand_format.py`, `photoreal.py` ou leur migration vers material-library (chunk-09), scripts de construction des assets,
`VERSIONS.md` (version de material-library utilisée), `summary.md`, `docs/plans/REPRISE.md`.

## Fini quand
Lou a validé les nouveaux rendus de l'embase (réplique et noire) et du bouton TFR ; les autres pièces FDM sont passées ou listées
comme restantes dans `REPRISE.md`.

## Watch-outs
- `outils/non_regression.py` : prouver que **seules** les matières FDM visées changent (maillages, positions, autres matières
  identiques).
- Les `.blend` retouchés par Lou ne sont jamais écrasés sans archive (`_archives\`) ni accord.
- Rendus lourds sur PC-B par le skill `rendu-distant` ; `.blend` enregistrés (pas de variantes par script).
