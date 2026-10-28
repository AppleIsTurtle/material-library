# CLAUDE.md — dépôt material-library (bibliothèque commune de Lou)

Bibliothèque commune aux projets de Lou (MFS en premier) : matières physiques, looks par procédé de fabrication, règles et outils
d'arêtes, visserie normalisée, imperfections, méthode de conception d'un boîtier. Code Python exécuté **dans Blender** (bpy,
bmesh), importé par les scripts des projets ; plan : [docs/plans/MASTER.md](docs/plans/MASTER.md).

## Règles (reprises de MFS)
- Français, noms en minuscules, mots séparés par `_`, ni espace ni accent dans les noms de fichiers.
- Le fichier de travail actuel n'a ni version ni date dans son nom ; les versions sont des **tags git** (`v0.1.0`…) et chaque
  projet note dans son `VERSIONS.md` la version qu'il utilise.
- `summary.md` dans chaque dossier (rôle de chaque fichier, dépendances, historique) ; tenu à jour à chaque changement.
- **Données lourdes hors git** : cartes d'images, planches et archives dans `G:\Blender\Bibliotheque\` (`material_library.DONNEES`).
  Exception (Lou, 2026-10-28) : la bibliothèque de matières générée, `bibliotheque/blender_<X.Y>/`, est suivie par git pour
  qu'un clone du dépôt suffise à l'installer ; une par version de Blender (4.4 et 5.1), régénérées ensemble.
- **Une fonction = une vérité** : un projet n'a plus sa propre copie d'une matière, d'une vis ou d'une règle d'arête ; s'il en a
  besoin d'une variante, elle s'ajoute ici avec un paramètre.
- **Ne jamais changer le rendu d'un projet sans le vouloir** : avant / après toute modification utilisée par MFS, comparer les
  dumps de ses assets avec `outils/non_regression.py` (maillages, matières, positions, visibilité) et un aperçu à l'œil.
- Blender se lance par `D:\Claude\MFS\outils\blender_garde.ps1` (garde-fou mémoire) ; scripts lancés depuis l'éditeur de texte de
  Blender : chemins absolus.
- Règles de Lou dans tout ce qui sort : vouvoiement ; aucun nom d'avionneur ni de modèle d'avion dans ce qui est public ; **pas d'arête vive** ;
  matières d'après des photos réelles et des mesures, couleurs compensées à la pipette ; aperçus avant tout rendu final ; chaque
  choix chiffré (« l'argent là où ça se voit »).
- Plusieurs sessions Claude peuvent travailler ici en même temps : chacune ne touche que ses dossiers, et commite **dans la même
  commande** que son `git add` (l'index est partagé) ; le `summary.md` racine n'est mis à jour que par la session qui coordonne.
- **Dépôt public** (GitHub, MIT, depuis la 0.3.1) : n'y écrire ni nom de personne autre que Lou (l'imprimeur FDM, les amis), ni
  prix de revient, prix de vente ou marge de ses produits (les prix publics des fournisseurs restent) ; commits signés avec l'adresse
  noreply de GitHub. L'historique de travail d'avant la 0.3.1 est dans le remote privé `prive` : ne jamais le pousser sur `origin`.
