# material-library

Bibliothèque commune de Lou pour concevoir et rendre des boîtiers et des pièces fabriquées (impression 3D, usinage, découpe laser) :
matières physiques, looks par procédé, arêtes sans angle vif, visserie normalisée, imperfections, méthode de conception.

## Installer la bibliothèque de matières dans Blender
1. Récupérer le dépôt : `git clone https://github.com/AppleIsTurtle/material-library.git`.
2. Dans **chaque** Blender : *Edit › Preferences › File Paths › Asset Libraries* → **+** → choisir le dossier de sa version,
   `bibliotheque\blender_4.4\` ou `bibliotheque\blender_5.1\` (Blender 4.4 n'ouvre pas les fichiers de la 5.x) → nommer
   « material-library » ; *Import Method* : **Append (Reuse Data)** en 4.4, **Append** en 5.1.
3. Dans un éditeur *Asset Browser*, choisir « material-library » en haut à gauche, puis glisser une matière sur un objet.

Les matières sont réglées **en mm** (*Scene › Units* : Unit Scale 0,001, Length en millimètres) ; dans une scène en mètres, le
grain et les couches FDM seraient 1 000 fois trop gros. Pour régénérer après une retouche du catalogue :
`blender -b --factory-startup --python blender\construire_bibliotheque.py`, avec **les deux** Blender (chacun écrit dans le dossier
de sa version). Le panneau « Impression FDM » (vrais trajets de la buse) n'est vérifié que sous Blender 5.1.

## Utiliser depuis un projet (script Blender)
```python
import sys
sys.path.insert(0, r"D:\Claude\material-library")
import material_library as SP
print(SP.__version__, SP.DONNEES)
```
Dans MFS : `outils/bibliotheque_commune.py` fait l'import et vérifie la version attendue. Points d'entrée, exemple testé et pièges :
[AGENTS.md](AGENTS.md). Ailleurs que sur le PC de Lou : variables d'environnement `MATERIAL_LIBRARY_DONNEES` (données lourdes,
défaut `G:\Blender\Bibliotheque`) et `MATERIAL_LIBRARY_PYTHON` (Python système).

## Panneau « Impression FDM » dans Blender
1. Préférences > Fichiers > *Script Directories* : ajouter `D:\Claude\material-library\blender\scripts` ; redémarrer Blender.
2. Préférences > Add-ons : activer « Material library — Impression FDM ».
3. Vue 3D > barre latérale (N) > onglet **Material library** : choisir la pièce, régler matière, buse, parois, dessus, couture, face
   sur le plateau, puis **Recalculer les trajets** (quelques secondes ; cartes enregistrées dans `<nom du .blend>_fdm\`).
Par script : `from material_library.matieres import reglages_fdm as RF ; RF.imprimer(ob, matiere="pla_noir", buse=0.4, plateau="-Z")`.
Il faut le Python système avec numpy, scipy, shapely et Pillow (`material_library.PYTHON_SYSTEME`).

## Licence
MIT : voir [LICENSE](LICENSE).

## Contenu
Voir [summary.md](summary.md) et le plan [docs/plans/MASTER.md](docs/plans/MASTER.md).
