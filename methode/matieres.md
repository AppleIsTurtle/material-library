# Matières — catalogue, fiches, couleurs compensées

Outils : [`material_library/matieres/catalogue.py`](../material_library/matieres/catalogue.py) (fiches et constructions),
[`couleurs.py`](../material_library/matieres/couleurs.py) (pipette, compensation), [`noeuds.py`](../material_library/matieres/noeuds.py)
(briques de nœuds). Planche : [`outils/planches/planche_matieres.py`](../outils/planches/planche_matieres.py).

```python
from material_library.matieres import catalogue as CAT
m = CAT.construire("nylon_pa12_noir")        # matière « SP_nylon_PA12_noir », nœud Bevel compris
CAT.noms("Métaux")                           # fiches d'une famille
```

## Règles de Lou
- **Physiquement juste** : partir de la construction réelle du matériau (couches, procédé) et de valeurs mesurées (réflectance,
  IOR, transmission), pas d'une couleur « qui fait gris ». Noter la source de chaque valeur dans la fiche.
- **Teinte uniforme, grain en relief seul** : sur une vraie pièce (résine, nylon, peinture), ni la teinte ni la rugosité ne varient
  par taches ; seul le relief (Bump, en vraie hauteur en mm) casse les reflets.
- **La teinte vue par Lou prime** sur les photos de téléphone (balance des blancs) : quand elle donne une teinte, c'est la cible.
- **Pas d'arête vive** : chaque fiche a son rayon de nœud Bevel (voir [aretes.md](aretes.md)).
- La matière et le **procédé** sont deux choses : le PLA noir est une matière ; ses couches de 0,2, le plateau texturé, les
  traces de tranchage sont le procédé FDM de l'imprimeur FDM ([procedes.md](procedes.md)). Idem résine JLC lisse ou poncée.

## Une fiche
`titre`, `famille` (catalogue de l'Asset Browser), `procede`, `matiere` (nom Blender, préfixe `SP_`), `fabrique` (fonction),
`cible` (teinte visée : vue par Lou ou norme ; `None` quand seul un rendu validé fait foi), `base` (base pour le studio de
référence, `STUDIO`), `rugosite` (valeur, ou (min, max, échelle) pour une brillance qui varie doucement), `metal`, `ior`, `voile`
(sheen), `transmission`, `diffusion` (poids, rayon RGB, échelle mm), `grain` (pas mm, amplitude mm, détail), `bevel` (mm),
`source`, `date`, `decision`.
Les matières de la visserie (inox A2, acier oxydé noir, laiton) sont construites par `visserie/shading.py` : la fiche y renvoie
(une fonction = une vérité).

## Ajouter une matière
1. **Photo réelle d'abord** (pièce reçue, échantillon, fiche du fabricant) et mesures (réflectance, transmission, rugosité Ra, taille
   du grain) ; demander à Lou la teinte qu'elle voit.
2. Choisir la construction : `uniforme` (la plupart), `peinture_grain_net`, `caoutchouc`, `alu_brosse`, ou une nouvelle fonction
   si la matière a des couches (comme l'étiquette alu + encre + pelliculage).
3. Écrire la fiche (source, date) ; la construire seule : `CAT.construire(nom)`.
4. **Pipette** si la fiche a une cible : `planche_matieres.py … seul=<nom>` rend une pastille de face dans le studio, mesure la
   médiane hors reflets et ombres, corrige la base en linéaire (cible / mesure) et recommence jusqu'à un écart ≤ 3 par canal ;
   reporter la base trouvée dans la fiche.
5. **Gros plan de contrôle** (boule + plaque à arêtes arrondies) et rasant ; regarder soi-même, puis montrer à Lou.
6. Décision de Lou dans la fiche (`decision`).

## Bases compensées : de quoi elles dépendent
Une matière satinée ou brillante reflète le studio et s'éclaircit : la base est plus foncée que la teinte visée. La base
compensée vaut **pour un studio et une vue de mesure** :
- studio de référence : celui du site (`G:\Blender\MFS\plans_fixes\site\hero.blend`, `studio.blend` lié) ;
- vue de mesure de la bibliothèque : pastille 30 × 30 vue de face, au centre du studio (planche_matieres.py).
Mesuré le 2026-10-27 : la peinture FS 36118 de base #3b3f45 rend **#646a71** sur la pastille, mais **#5f656c** sur le rendu de
face du F-COM2 (MFS) ; la vue compte pour ≈ 5 niveaux. **Décision de Lou (2026-10-27) : garder la base #3b3f45 validée dans
MFS** (référence = rendu de face du F-COM2) ; la base qu'il faudrait sur la pastille (#363940, rend #5f646c) reste notée dans la
fiche. Une nouvelle compensation se lance avec `planche_matieres.py … seul=<nom> compenser`.

## Bibliothèque dans Blender (Asset Browser)
`bibliotheque\blender_<X.Y>\bibliotheque_matieres.blend` dans le dépôt (+ `blender_assets.cats.txt` à côté), **un fichier par
version de Blender** (`blender_4.4\`, `blender_5.1\` : Blender 4.4 n'ouvre pas un .blend de la 5.x) : une matière par fiche, les variantes
FDM de l'imprimeur FDM (buses 0,4 / 0,2, PLA naturel translucide) et 7 pièces de visserie toutes faites, avec aperçu, description (fiche :
procédé, base, source, décision) et catalogues (Peintures, Résines, Impression FDM, Nylon, Métaux, Verres, Caoutchoucs, Visserie).
Le fichier est **généré** par [`blender/construire_bibliotheque.py`](../blender/construire_bibliotheque.py) : ne pas le retoucher à
la main (une retouche va dans la fiche du catalogue, puis on régénère **avec les deux Blender** ; l'ancien est archivé dans
`G:\Blender\Bibliotheque\_archives\`).

**La déclarer (une fois par Blender)** : *Edit › Preferences › File Paths › Asset Libraries* → **+** → choisir le dossier de **sa**
version (`D:\Claude\material-library\bibliotheque\blender_4.4\` ou `…\blender_5.1\`) → nommer « material-library » ; *Import Method* :
**Append (Reuse Data)** en 4.4, **Append** en 5.1 (la 5.x ne propose plus *Reuse Data*). Puis, dans un éditeur *Asset Browser*,
choisir la bibliothèque « material-library » en haut à gauche. Fait chez Lou le 2026-10-28 dans les deux Blender (préférences
sauvegardées avant : `userpref_avant_material_library_2026-10-28.blend`).

**Glisser une matière** sur un objet la **copie** dans la scène (*Append*) : elle devient locale, modifiable, et ne suit plus
la bibliothèque. *Link* la garderait liée (non modifiable, mise à jour à chaque régénération) ; *Append (Reuse Data)* évite les
doublons « .001 » quand on glisse deux fois la même (en 5.1, *Append* simple : un doublon « .001 » reste possible). Une pièce de
visserie arrive comme une collection (tête + tige).

**Unités** : toutes les matières sont réglées **en mm** (1 unité Blender = 1 mm, échelle 0,001), comme les scènes de MFS : le
grain, les couches FDM et les cartes d'imperfections seraient 1 000 fois trop gros dans une scène en mètres. L'alu brossé et
l'acier oxydé lisent les **UV** (brossage le long de U, cartes sur UV en mm : `imperfections.uv_mm.uv_plan_mm`) ; les couches FDM
suivent l'**axe Y de l'objet** (face -Y sur le plateau).

Vérifié le 2026-10-27 (`outils/essais/essai_bibliotheque.py`) : le fichier s'ouvre dans Blender 5.1, 29 assets ont leur aperçu et
un catalogue connu, images packées ; chaque matière ajoutée dans le studio du site rend la même teinte que sur la planche du
chunk-03 (écart 0 à la pipette). Le 2026-10-28 : les deux fichiers (4.4 et 5.1) s'ouvrent dans leur Blender avec 29 assets ;
leurs aperçus ont la même teinte moyenne (écart ≤ 2,5 / 255, le nylon ; ≤ 1 pour les autres). Seule différence de code : sous 4.4,
le booléen des vis passe de *Manifold* (4.5+) à *Exact*.
