# Chunk 07 — cordons procéduraux (netteté sans résolution)

**Statut : `done`** (2026-11-13, demandé par Lou ; validé sur la façade du F-COM3 noir : lignes nettes avec des cartes de 2048, pic 6 Go ; planche fdm_cordons et non-régression des assets : à faire quand Lou voudra régénérer des assets) · **Plan : [plan.md](plan.md)** · reprend le chunk-03

## Pourquoi
Le chunk-03 cuit le **relief** des cordons dans une image (`cartes.py` → carte « hauteur ») : la netteté est celle de la carte.
Sur la façade du F-COM3 noir (145 mm), un cordon plat au sillon net (≈ 0,05 mm) passe sous le texel même en 5120 px (0,028 mm) et
la cuisson dépasse 12 Go en 6144. Lou, 2026-11-13 : « c'est un pixel que tu fais ce shader ? Ça devrait être du procédural sans
pixels » ; « dans la vraie vie le rendu est plus sharp, moins arrondi ; léger grain ; les lignes ont de toutes petites
imperfections, parfois des coupures sur les bords, pas parfaitement droites ».

## Principe
Les vrais trajets disent **où** passent les lignes ; on ne cuit plus que des **champs lisses**, exacts à toute résolution par
interpolation, et le shader construit le relief à chaque point rendu :
- **phase** des lignes : distance signée à l'axe du cordon le plus proche (direction rendue canonique), divisée par le pas,
  cuite en `(cos 2πc, sin 2πc)` : continue d'une ligne à l'autre (le sillon tombe à la phase π, que l'interpolation garde) ;
- **profondeur** des sillons (part de la couche, nulle loin de tout cordon : vides comblés) ;
- direction du fil (anisotropie) et coutures des tranches : inchangées.
Shader : |c| = |atan2(sin, cos)| / 2π, x = |c| × pas / demi-largeur, + ondulation (bruit ≈ 2 mm, ± 0,012 mm), + coutures éparses
(bruit ≈ 0,12 mm seuillé), profil super-ellipse (exposant 6 : plat, bord net), × profondeur → Bump. Grain du plateau lisse :
relief seul ± 1,2 µm (procédural, `plateau_texture`).

## Fichiers
- `material_library/impression/cartes.py` : sortie `cordons` (cos, sin, profondeur) ; la carte `hauteur` ne garde que les coutures.
- `material_library/matieres/procedes.py` : `trajets()` lit `cordons` et construit le profil ; `GRAINS["lisse"]`.
- `material_library/rendu.py` : `res_premier_lit` garde son intérêt (ombrage plat du plan) mais plus besoin de cartes géantes.

## Vérification
- Gros plan de la façade du F-COM3 noir (vis M3, encoche M4, dos) : lignes nettes à tout zoom, aucun pixel visible.
- Planche `outils/planches/planche_fdm_cordons.py` refaite ; `outils/non_regression.py` sur les pièces FDM des projets (le look
  change exprès : à montrer à Lou avant de régénérer les assets).

## Points de vigilance
- Changement de look voulu pour **toutes** les pièces FDM : ne pas régénérer un asset validé sans accord de Lou.
- Les champs de phase ont une discontinuité de signe (sin) là où la direction canonique bascule : sans effet sur |c| (profil symétrique).
