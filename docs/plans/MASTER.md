# Plan — bibliothèque commune « material-library » (matières, impression 3D, vis, arêtes, méthode de conception)

**Statut : `pending`** (plan écrit le 2026-10-27, rien d'implémenté) · demandé par Lou le 2026-10-27, après le F-COM2 réplique.
Ce plan vit dans MFS le temps de démarrer ; au chunk-01 il devient le `MASTER.md` du nouveau dépôt (MFS garde un lien).

## Demande (Lou, 2026-10-27)
« Je veux qu'on standardise la création des éléments précis. On doit avoir notre bibliothèque de matériel, les impressions 3D
donnent un look matériau spécifique, la création et le shading des vis, les questions sur les bevel et la sharpness des angles.
Ces points-là sont généralisés, ils pourront être utilisés pour d'autres projets également. Les questions de norme, taille du
boîtier, matériaux du boîtier, placement des vis, supports, etc. L'idée est de gagner du temps et d'hériter de la méthodologie
qu'on a eue pour la F-COM2. »

Décisions de Lou (questions du 2026-10-27) :
- **dépôt à part**, hors de MFS, importé par MFS et les autres projets ; la méthode portée par un **skill Claude global** (comme
  `rendu-distant`), utilisable dans n'importe quel projet ;
- forme : **scripts Python** (pour Claude) **+ un `.blend` « bibliothèque de matières »** déclaré comme *Asset Library* dans Blender
  (pour que Lou glisse les matières à la main dans ses scènes) ;
- ordre : pas encore tranché (voir « À trancher »).

## Point de départ (état au 2026-10-27)
Tout existe déjà, mais dispersé dans `boitier/scripts/` de MFS, écrit pour le F-COM1 puis le F-COM2 :

| Domaine | Où c'est aujourd'hui | Ce qu'il y a |
|---|---|---|
| Matières | `photoreal.py` (27 fonctions) ; `mat_uniforme`, `MATIERES_FACADE`, `MATIERES_CAISSON`, `peinture_acrylique`, `pla_imprimeur`, `inox_noirci_use`, `resine_jlc_lisse` (retirée) dans `maquette_grand_format.py` ; `carte/matieres.py`, `pcb_photoreal.py` | résine 9600, nylon PA12 MJF, PLA FDM (`pla_fdm`, `couches_fdm`), inox, acier des vis, PVC, alu brossé, OLED, SLA JLC Black huilée, acrylique peint « jour / nuit » à grain net, acier oxydé noir usé, verre fumé, PCB |
| Couleurs | `carte_pipette.py`, mémoire « couleurs vues par Lou » | bases compensées à la pipette dans le studio du site (ex. FS 36118 : base #3b3f45 rend #5f656c) |
| Impression 3D | `photoreal.pla_fdm`, `appliquer_traces` + `simulation_lettres_facade.py` (traces U1), `impression_calques.py`, `encre.py`, `impression*.py` | couches FDM, plateau texturé, traces de tranchage, encre « un peu baveuse » |
| Arêtes | `adoucir`, `bevel_rendu`, `profil_arrondi`, `plaque_xz`, `coupe_xz` (maquette), `photoreal.aretes_douces` ; mémoire « pas d'arête vive », « arêtes de contention » | biseau appliqué, nœud Bevel (acrylique R 0,4, PLA R 0,3, vis R 0,2), congés des découpes, lissage par angle (35°) |
| Vis | `fixations.py` (standard du 2026-10-27), `visserie_photoreal.py` (filets, écrous, rondelles), `tige()` / `ecrou()` de la maquette ; règle `docs/methodes/fixations_facade.md` | attaches M4 DIN 84 en collerette, petites vis M3 ISO 7046 à fleur, fraisages, encoches en U à congé, filets |
| Imperfections | `imperfections.py` + cartes `G:\Blender\MFS\imperfections\`, `uv_plan_mm` (maquette) | poussière, frottements, micro-rayures ; UV dépliés en mm |
| Conception | `maquette_grand_format.py` (P, contrôles trous / collisions), `supports.py`, `pcb/scripts/grand_format/interface.py`, `etude-fabrication-pcb.md`, `chunk-03-replique.md` | cotes de panneau (145,7 × 66,3), caisson SLA vissé, colonnes d'inserts, supports clipsés 15°, boîte à lumière, choix imprimeur FDM / JLC / atelier, chiffrage |
| Chaîne de rendu | `scenes/scripts/construire.py`, assets `G:\Blender\MFS\assets\`, plans fixes, skill `rendu-distant`, aperçus puis rendus finaux | asset → plans fixes liés → aperçus → PC-B → copie |

Les retours de Lou qui fondent la méthode sont dans la mémoire de Claude (matières physiques, couleurs, méthode de modélisation,
fabrication réelle, pas d'arête vive, arêtes de contention, nylon, fixations standard, argent là où ça se voit).

## Objectif
Un dépôt `material-library` (nom à confirmer) qui fournit à tout projet de Lou :
1. une **bibliothèque de matières** physiques, chacune avec sa fiche (procédé, valeurs mesurées, photo de référence, base
   compensée), générée par script **et** livrée en `.blend` *Asset Library* ;
2. des **looks par procédé de fabrication** (FDM de l'imprimeur FDM, SLA JLC, MJF, acrylique laser peint, métaux usinés), paramétrés
   (buse, couche, orientation, finition) ;
3. les **règles et outils d'arêtes** : quand un biseau géométrique, quand un nœud Bevel, quels rayons, quel angle de lissage ;
4. la **visserie standard** : tables DIN / ISO, géométrie (têtes, empreintes, fraisages, collerettes, encoches), shading
   (inox, acier oxydé, têtes peintes), imperfections sur UV en mm ;
5. la **méthode de conception d'un boîtier** (document + outils) : normes de panneau, tailles, matériaux et où les fabriquer,
   placement des vis et des inserts, supports, boîte à lumière, contrôles automatiques, chiffrage ;
6. un **skill Claude global** qui déroule la méthode (nouvelle façade → maquette → contrôles → asset → aperçus → rendus) ;
7. MFS **branché dessus** sans rien changer à ses rendus (non-régression prouvée).

## Périmètre
**Dedans** : tout ce qui sert à concevoir et rendre un boîtier ou une pièce imprimée / usinée ; la migration de MFS (F-COM2 réplique
et noire, transpondeur) vers le dépôt ; le `.blend` de matières ; le skill.
**Dehors** : le PCB (KiCad, bibliothèque de composants : autre sujet) ; le site et le packaging (seulement leurs matières, s'ils les
reprennent) ; la régénération de l'asset du F-COM1 (il garde `photoreal.py` de MFS tant qu'on ne le refait pas) ; Houdini ; le film.

## Structure proposée du dépôt
```
material-library/
  CLAUDE.md, README.md, summary.md, docs/plans/MASTER.md (ce plan)
  material_library/              paquet Python importé par les scripts Blender (bpy, bmesh)
    matieres/                  catalogue.py (fiches), procedes.py (FDM, SLA, MJF, acrylique, métaux), couleurs.py (pipette)
    aretes.py                  biseau appliqué, nœud Bevel, profils arrondis, découpes à congé, règle d'angle de lissage
    visserie/                  normes.py (tables DIN / ISO), fixations.py, filets.py, shading.py
    imperfections/             imperfections.py, uv_mm.py
    impression/                encre.py, decalques.py, calques.py
    conception/                panneau.py (cotes, normes), caisson.py, supports.py, controles.py (trous, collisions)
  blender/                     construire_bibliotheque.py → bibliotheque/blender_<X.Y>/bibliotheque_matieres.blend
  bibliotheque/                la bibliothèque de matières générée (suivie par git), une par version de Blender (4.4, 5.1)
  methode/                     conception_boitier.md, rendu_produit.md, fixations_facade.md (déplacé), aretes.md, matieres.md
  skill/                       source du skill ~/.claude/skills/material-library/
```
Les fichiers lourds (cartes d'imperfections, planches, archives) restent sur `G:\Blender\` (comme les assets) ; seule la
bibliothèque de matières générée est dans le dépôt (Lou, 2026-10-28 : un clone suffit à l'installer). MFS l'importe par un chemin fixe (`D:\Claude\material-library`, aussi valable dans l'éditeur de texte de Blender) ;
`VERSIONS.md` de MFS note la version (tag git) utilisée.

## Chunks (un par contexte neuf, statut dans chaque fichier)
| Chunk | Contenu | Dépend de |
|---|---|---|
| [chunk-01-depot](chunk-01-depot.md) | créer le dépôt, squelette, règles (CLAUDE.md, summary.md), import depuis MFS, test de non-régression outillé | — |
| [chunk-02-aretes](chunk-02-aretes.md) | règles et outils d'arêtes (biseau, Bevel, congés, lissage) | 01 |
| [chunk-03-matieres](chunk-03-matieres.md) | catalogue des matières + fiches + compensation pipette | 01, 02 |
| [chunk-04-procedes](chunk-04-procedes.md) | looks par procédé d'impression / usinage, paramétrés | 03 |
| [chunk-05-visserie](chunk-05-visserie.md) | normes DIN / ISO, géométrie et shading des vis, imperfections sur UV en mm | 02, 03 |
| [chunk-06-blend-matieres](chunk-06-blend-matieres.md) | `.blend` *Asset Library* généré, aperçus, déclaration dans Blender | 03, 04, 05 |
| [chunk-07-methode-conception](chunk-07-methode-conception.md) | méthode de conception d'un boîtier (doc + outils de contrôle et de cotes) | 02, 05 |
| [chunk-08-skill](chunk-08-skill.md) | skill Claude global « material-library » | 07 |
| [chunk-09-migration-mfs](chunk-09-migration-mfs.md) | F-COM2 (réplique, noire) et transpondeur importent le dépôt ; non-régression | 02 à 07 |

Features ajoutées ensuite (chacune son plan et ses chunks, dans `features/`) :
- [fdm-trajets](features/fdm-trajets/plan.md) (Lou, 2026-10-27) : PLA FDM d'après les vrais trajets de la buse (étude
  d'OrcaSlicer, notre simulation calibrée, réglages sur la pièce + « recalculer ») ; remplace `procedes.fdm` du chunk-04.

## À trancher avec Lou
1. **Nom et emplacement** : `D:\Claude\material-library\` proposé.
2. **Dépôt GitHub** : tranché le 2026-10-28 : privé, https://github.com/AppleIsTurtle/material-library.
3. **Où vit le `.blend` de matières** : tranché le 2026-10-28 : dans le dépôt, `bibliotheque/blender_4.4/` et `blender_5.1/`.
4. **Ordre** : rendu d'abord (chunks 02 → 06, déjà mûrs) ou conception d'abord (07) ; la migration de MFS (09) en dernier.

## Watch-outs (communs à tous les chunks)
- **Ne rien changer aux rendus de MFS** : avant / après chaque migration, comparer les dumps des assets (maillages, matières,
  positions : outil du 2026-10-27, `dump.py`) et un aperçu à l'œil ; les versions réplique **et** noire.
- Les `.blend` retouchés par Lou ne sont jamais réécrits sans archive (règle MFS) ; l'asset du F-COM1 n'est pas touché.
- Scripts lancés dans Blender par `outils/blender_garde.ps1` ; chemins absolus pour l'éditeur de texte de Blender.
- Syncthing / ferme : ne jamais lancer Syncthing depuis une session Claude (dossier virtualisé de l'appli).
- Règles de Lou dans tout ce qui sort : vouvoiement, aucun nom d'avionneur ni de modèle d'avion dans ce qui est public, pas d'arête vive, matières
  d'après des mesures et des photos réelles, chaque choix chiffré.
- `summary.md` dans chaque dossier du nouveau dépôt (règle globale de Lou).
