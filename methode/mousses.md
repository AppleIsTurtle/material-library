# Mousses — construire une mousse PE à cellules fermées

Outils : [`material_library/matieres/mousse.py`](../material_library/matieres/mousse.py) (matière et forme de l'objet entier),
[`outils/mousse/`](../outils/mousse/summary.md) (vraie géométrie, calibrage, comparaison). Fiche : `mousse_pe_ld33`.

```python
from material_library.matieres import catalogue as CAT, mousse as MO
MO.poser(ob, CAT.construire("mousse_pe_ld33"))     # ob : maillage fermé, 1 unité = 1 mm ; voxel=0.1 pour un gros plan
sc.render.engine = "CYCLES"; sc.cycles.dicing_rate = 1.5; sc.cycles.max_subdivisions = 8; sc.cycles.offscreen_dicing_scale = 8
```

Dans l'Asset Browser (catalogue « Mousses ») : glisser `SP_mousse_forme` sur un maillage fermé (il pose aussi la matière), puis
ajouter une Subdivision *Simple* adaptative. La matière seule, sans la forme, donne un flanc partout et demande un maillage dense.

## Ce que dit la fabrication
On modélise dans l'ordre où la mousse se fait, pas un motif de surface :
1. **La matière** : polyéthylène réticulé, expansé à l'azote. Les bulles sont à peu près isotropes, de tailles variables ; elles se
   touchent par des films plans. Une alvéole est donc une bulle coupée, simple et arrondie, à 4 ou 5 coins, et chacune a sa place.
2. **Le dessus, tranché à la scie à ruban** : la lame écrase et couche les parois. Rebords épais et arrondis, creux peu profonds,
   surface plus brillante et comme fondue.
3. **Les flancs, au jet d'eau** : parois fines et effrangées, cellules profondes, stries le long du jet, arrachements. Face plus
   sombre et plus mate que le dessus.
4. **La pièce** : jamais plane. Gonflement lent, bosselage, chocs, affaissement au bord de coupe. L'arête entre tranche et peau reste
   **franche** (exception à « pas d'arête vive », voir [aretes.md](aretes.md)) ; c'est le bord déchiqueté des cellules qui l'adoucit.
5. **Le collage de plaques** : une fine couche fondue, dense et bosselée (`outils/mousse/geometrie_reference.py`, étape 3).

## Deux niveaux de modèle
| | Vraie géométrie | Matière calibrée |
|---|---|---|
| Fichier | `outils/mousse/geometrie_reference.py` | `material_library/matieres/mousse.py` |
| Principe | grille SDF : bulles, films, découpes | en chaque point, rayon vers la sphère de la bulle coupée ; vrai déplacement Cycles |
| Usage | gros plan de quelques mm, référence | objet entier, sans répétition |

Les gains de la matière viennent de `outils/mousse/calibrer.py`, qui vise les mesures de la géométrie (Sa, médiane et 95e centile des
creux). `outils/mousse/comparer.py` rend le même bloc, au même cadrage que la référence.

## Taille et proportions (2026-11-01)
| Grandeur | Valeur | Origine |
|---|---|---|
| Diamètre de cellule | 0,4 mm (LD33) | fiche Zotefoams, lue en extrait de recherche, méthode de mesure non précisée |
| Autres valeurs relevées | LD33 0,37 mm ; LD24 0,3 mm (une source à 0,4) ; LD45 0,4 mm | revendeurs |
| Modèle | 0,36 mm de médiane apparente en coupe ; 0,50 mm en volume équivalent ; ≈ 3 cellules par mm | mesuré sur `mousse.hauteur` |

Répartition des creux, comparée à une mousse idéale simulée avec les mêmes bulles (parois nulles, coupe parfaite). Cette mousse idéale
est une borne théorique, pas une mesure :

| µm | Mousse idéale | Flanc | Dessus |
|---|---|---|---|
| Sa | 132 | 102 | 50 |
| Médiane | 133 | 140 | 62 |
| 95e centile | 442 | 319 | 172 |

## Limites connues
- **Aucune photo à échelle connue** n'a pu confirmer la taille : à contrôler à la règle sur un échantillon reçu.
- Le flanc manque d'environ 25 % de creux très profonds et garde quelques plats (2,8 % de la surface à plus de 60 µm d'un creux, contre
  0,2 % pour la mousse idéale). Cela ne se voit qu'en gros plan sur la tranche.
- Un brevet (US 6340717) donne 0,1 à 0,2 mm pour les mousses en bloc réticulées chimiquement, lu en extrait seulement : la fiche de la
  nuance fait foi.
- Teinte réglée sur rendu, à comparer à un échantillon. L'occlusion des creux assombrit la base : c'est de la lumière qui manque au fond
  d'une alvéole de quelques pixels, pas une variation de teinte de la matière.
- Une seule nuance est calibrée. Une autre taille de cellule se règle par `CELL`, puis on relance le calibrage.

## Sources
- [Fiche LD33 de Zotefoams](https://zotefoams.com/wp-content/uploads/2016/03/LD33-December-2017.pdf)
- Brevet US 11753513 : Sa de 20 à 75 µm pour une mousse de polyoléfine tranchée
- [Brevet US 6340717](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/6340717)

## Décisions de Lou
- 2026-11-01 : pas de carte cuite ni de motif répété ; imperfections à plusieurs échelles ; méthode par étapes préférée aux essais de
  surface (Worley, alligator en hauteur) ; ne jamais seuiller un bruit en parois fines, cela redonne des polygones.
- 2026-11-01 : look validé pour la bibliothèque.
