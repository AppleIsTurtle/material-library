# Cartons — construire un carton ondulé kraft et l'imprimer

Outil : [`material_library/matieres/carton.py`](../material_library/matieres/carton.py). Fiches : `carton_e_kraft_ext`, `carton_e_kraft_int`, `carton_e_cannelure`, et pour les papiers `papier_offset_ivoire`, `carte_pelliculee_mate`.

```python
from material_library.matieres import catalogue as CAT
ext = CAT.construire("carton_e_kraft_ext", masque=png, masque_cadre=(xmin, ymin, largeur, hauteur), matiere="SP_carton_imprime")   # encre = blanc dans le PNG
```
La matière lit la couche UV `uv_mm` (coordonnées du patron à plat, en mm) et l'attribut de point `pli` (0 à 1).

## Ce que dit la fabrication
On modélise le carton comme il est fait, pas comme une plaque texturée :
1. **Trois feuilles** : deux couvertures kraft (≈ 0,2 mm) collées sur une cannelure ondulée. Cannelure E : pas de 3,2 à 3,5 mm, carton de 1,5 mm. La tranche montre donc de vrais tubes, sombres dedans.
2. **La couverture** : fibres couchées dans le sens de la machine, marbrure en nuages de la pâte recyclée, quelques paillettes sombres. La cannelure se devine en lignes très faibles.
3. **Le pli** : un rainage écrase le carton côté intérieur et bombe à peine l'extérieur ; perpendiculaire aux cannelures, l'écrasement suit leur pas. Le papier blanchit et se fissure là où il s'étire.
4. **La coupe** : l'emporte-pièce écrase le carton sur environ 1 mm le long de chaque coupe : couvertures rapprochées, cannelure aplatie. Sans cela, les tubes ouverts bâillent en noir dès qu'on voit le bord de biais.
5. **L'encre** : noir de flexographie, mat. Elle boit la couverture, les fibres claires affleurent, le bord est légèrement baveux. Trop de reflet la fait virer au brun sous un studio : garder un niveau de reflet bas sous l'encre.
6. **La boîte** : jamais plane. Bombés à plusieurs octaves, nuls aux plis, et quelques petits chocs aux coins et aux bords.

## Mesures et limites
| Grandeur | Valeur | Origine |
|---|---|---|
| Épaisseur | 1,5 mm | déduite d'un patron du commerce : extérieur annoncé − cote de pli à pli |
| Pas de la cannelure | 3,3 mm | ordre de grandeur de la cannelure E |
| Teintes | #c49a5f, #bb9460 | choisies par Lou sur rendu parmi trois essais (2026-11-01) |
| Marbrure | nuages de 10 à 80 mm, ± 3 % seulement | photos de boîtes du commerce ; plus fort, la boîte fait sale (Lou, 2026-11-01) |

Sur une pièce découpée, mailler le contour et repousser les triangles vers l'intérieur : une grille coupée au bord laisse des marches dans le relief (Lou, 2026-11-01).

À contrôler sur un échantillon reçu : teinte, force de la marbrure, couleur de la cannelure.
