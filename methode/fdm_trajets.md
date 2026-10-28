# Trajets réels d'une impression FDM (Snapmaker U1, PLA) — ce que notre simulation doit reproduire

Étude du 2026-10-27 (feature [fdm-trajets](../docs/plans/features/fdm-trajets/plan.md), chunk-01) : OrcaSlicer 2.4.2 portable
(`F:\OrcaSlicer\2.4.2`), **profil Snapmaker U1 par défaut** (choix de Lou), filament « Snapmaker PLA @U1 », pièces : embase de la
F-COM2 (face avant sur le plateau, mono-matière) et bouton TFR du F-COM1 (face sur le plateau). Planche :
`G:\Blender\Bibliotheque\fdm\orca\planche_orca.png` ; G-code et lectures : `G:\Blender\Bibliotheque\fdm\orca\<cas>\`.
Outils : [outils/fdm/](../outils/fdm/summary.md) (`profil.py`, `trancher.py`, `gcode.py`, `planche_orca.py`).

## Réglages par défaut du profil U1
| Réglage | Buse 0,4 (« 0.20 Standard ») | Buse 0,2 (« 0.10 Standard ») |
|---|---|---|
| Hauteur de couche · première couche | 0,20 · 0,25 | 0,10 · 0,10 |
| Largeur paroi extérieure · intérieure | 0,42 · 0,45 | 0,22 · 0,22 |
| Largeur dessus · plein interne · première couche | 0,42 · 0,42 · 0,50 | 0,22 · 0,22 · 0,25 |
| Nombre de parois | 2 | 4 |
| Couches pleines dessus · dessous | 5 (≥ 1,0 mm) · 3 | 7 (≥ 0,8 mm) · 5 |
| Motif du dessus · du dessous · plein interne | monotone ligne · monotone · monotone | idem |
| Remplissage clairsemé | croisé (crosshatch) 15 % | idem |
| Direction du remplissage | 45° (alterne 45° / 135° d'une couche à l'autre) | idem |
| Générateur de parois | Arachne (largeur variable) | idem |
| Ordre des parois · sens | intérieure puis extérieure · anti-horaire | idem |
| Couture | alignée, écart de couture 10 % | idem |
| Une seule paroi sur les dessus | oui | oui |
| Recouvrement dessus / parois · remplissage / parois | 25 % · 15 % | idem |
| Remplissage des petits espaces | nulle part (gap_fill_target = nowhere) | idem |
| Lissage du dessus (ironing) · peau floue | non · non | idem |
| Compensation du pied d'éléphant | 0,15 mm | 0,15 mm |

## Ce qu'on mesure dans le G-code (règles à reproduire, par ordre d'importance visuelle)
1. **Pas des lignes = largeur − hauteur × (1 − π/4)** (écrasement du cordon, formule de Slic3r) : dessus en buse 0,4 :
   0,42 − 0,2 × 0,215 = **0,377 mm** mesuré ; buse 0,2 : **0,199 mm** mesuré. Première couche (0,50 × 0,25) : 0,446 mm (calcul).
   Le même écrasement vaut entre deux parois voisines.
2. **Chaque couche** : parois (2 en buse 0,4, 4 en buse 0,2) autour du bord extérieur **et** de chaque trou, puis le plein en
   lignes parallèles ; les lignes font demi-tour contre la paroi intérieure, qu'elles recouvrent (festons visibles au zoom).
3. **Couches de dessus** (toute zone non couverte par la couche du dessus, y compris les marches : l'épaulement du TFR, couche 3
   en buse 0,4) : **une seule paroi**, puis les lignes du dessus en monotone (toutes dans le même sens, posées dans l'ordre, sans
   aller-retour visible) à 45° ou 135° selon la couche — dernière couche de l'embase : 135°.
4. **Face sur le plateau** (première couche) : 2 parois + lignes monotones à 45°, cordons larges (0,50) et écrasés sur le PEI ;
   c'est la face visible de l'embase et du bouton TFR : le grain du plateau domine, les lignes et les anneaux autour des trous
   restent à peine lisibles sous lumière rasante.
5. **Tranches** : une paroi extérieure par couche (0,2 / 0,1 de haut), **largeur variable** (Arachne : 0,42 à 0,54 relevé sur le
   TFR), donc des cordons un peu plus gros dans les zones étroites et aux angles.
6. **Couture alignée** : un point de départ par contour, **le même à chaque couche** (une ligne verticale sur la tranche),
   placé dans un angle quand le contour en a (TFR : coin arrière droit) ; variantes : « arrière » (tous vers l'arrière du
   plateau), « aléatoire » (points épars, plus de bourrelets mais pas de ligne).
7. **Petits espaces non remplis** : de petits triangles vides restent entre parois et plein dans les angles étroits (TFR,
   variante concentrique) — invisibles de l'extérieur, sauf sur un dessus.
8. **Variantes** : 1 paroi (la paroi intérieure disparaît, le plein vient contre l'extérieure) ; dessus concentrique (anneaux
   qui suivent les bords et les trous, fronts qui se rencontrent avec des petits manques).

## Ce que ça veut dire pour nos rendus
- **Embase de la réplique** : face avant = première couche sur le PEI (grain + lignes à 45° très discrètes + anneaux autour des
  fenêtres et des trous) ; tranches = cordons de 0,2 et couture verticale à un coin de chaque contour ; dos = une paroi + lignes
  à 135° au pas de 0,377 (éclaté, vues de dos).
- **Bouton TFR** : face = première couche sur le PEI (plus de taches) ; flancs = cordons de 0,2 ; épaulement = dessus en lignes.

## Notre simulation (chunk-02, 2026-10-28) : `material_library/impression/tranchage.py`
Règles reprises d'Orca, mesurées dans son G-code (embase et bouton TFR, buses 0,4 et 0,2) :
- tranches à mi-hauteur de couche ; dernière couche au-dessus du sommet (n = 1 + ⌈(H − 1re couche) / couche⌉) ;
- première couche : bord rentré de 0,15 (pied d'éléphant) ; axe de la paroi extérieure à **½ largeur** du bord ; chaque paroi
  intérieure un **pas d'écrasement** plus loin (largeur − hauteur × 0,215) ;
- plein : bord de la zone intérieure + ½ pas − recouvrement (15 % ; dessous 25 %) ; lignes du dessus : bouts à 0,77 × largeur du
  bord ; une seule paroi sous un dessus ; lignes alignées sur l'origine du plateau, 45° les couches paires, 135° les impaires ;
  **raccords** entre lignes voisines le long du bord (monotone ligne) ;
- coques : plein sur 5 couches sous un dessus et 3 au-dessus du bas en buse 0,4 (8 et 5 en buse 0,2 : l'épaisseur 0,8 mm
  l'emporte) ; ailleurs clairsemé croisé 15 %, plein sous 15 mm² ; pont interne sur le clairsemé ;
- parties trop fines pour deux tours : un cordon central de largeur adaptée (Arachne) ; bande trop étroite après le tour
  extérieur : un cordon central ;
- couture alignée : le coin le plus marqué, puis, sur un contour lisse, un côté en x (Orca : 0° ou 180°), le même d'une couche à
  l'autre ; « arrière », « aléatoire » ;
- chaque matière d'une pièce est coupée à part puis réunie (fentes < 0,01 mm refermées) : une seule matière, comme Orca en ligne
  de commande.

Comparaison (`outils/fdm/comparer.py`, planche `G:\Blender\Bibliotheque\fdm\simulation\planche_comparaison.png`) :
| Cas | Pas du dessus (Orca / nous) | Axe des parois ext. (médiane / 95 %) | Seuils |
|---|---|---|---|
| Embase, buse 0,4 | 0,377 / 0,377 | 0,004 / 0,024 mm | 6 / 6 |
| Embase, buse 0,2 | 0,199 / 0,199 | 0,001 / 0,025 mm | 6 / 6 |
| Bouton TFR, buse 0,4 | 0,390 / 0,377 | 0,015 / 0,041 mm | 6 / 6 |
| Bouton TFR, buse 0,2 | 0,201 / 0,199 | 0,011 / 0,194 mm | 4 / 6 (bouts des nervures de 0,6 mm) |
| Embase 0,4 : 1 paroi · couture arrière · aléatoire | 0,377 / 0,377 | 0,004 / 0,024 mm | 6 / 6 |
| Embase 0,4 : dessus concentrique | (pas sans objet) | 0,004 / 0,024 mm | 5 / 6, superposition identique à l'œil |
Seuils : pas et largeur du dessus ± 5 %, angle ± 1° à chaque couche, mêmes couches, couverture visible (parois extérieures,
dessus, face plateau, ponts) ± 2 %, axe des parois extérieures ≤ 0,03 mm en médiane et ≤ 0,15 mm à 95 %. L'IoU des cordons (pixels
communs) a été écarté : un anneau de 0,22 mm fait 4 pixels, il chute pour un écart invisible.

Écarts connus (invisibles sur une pièce finie, ou presque) : largeur fixe par type au lieu de la largeur variable d'Arachne
(remplissage des zones étroites à l'intérieur) ; bouts des nervures très fines arrondis chez Orca, vifs chez nous ; vide de
couture (10 %) non reproduit ; deux coins non remplis sur l'épaulement du TFR (caché derrière la façade) ; côté de la couture d'un
trou rond (gauche / droite) pas toujours le même qu'Orca — la ligne verticale reste.

## Rendu des cordons (chunk-03, 2026-10-28) : `procedes.trajets(o, trajets.npz)`
```python
PR.poser(o, PR.fdm("pla_noir", buse=0.4, plateau="-Z"))      # matière (catalogue) + grain du plateau sur la face posée
PR.trajets(o, "trajets.npz")                                 # trajets de tranchage.py pour CE maillage (même repère)
```
1. UV dépliés (smart project), position et normale de chaque texel cuites par Cycles (repère de l'objet) ;
2. `impression/cartes.py` (Python système, `material_library.PYTHON_SYSTEME`) : chaque texel est ramené dans le repère d'impression ;
   dessus (n.z > 0,7) et dessous (n.z < −0,7) → cordons de la couche à cette hauteur (segment le plus proche, distance exacte,
   profil en demi-ellipse de la largeur réelle) ; tranches → bourrelet de couture ; direction du fil partout ;
3. shader : couches des tranches **calculées** (vraie première couche, cordon arrondi, creux de 22 % de la couche, couches un peu
   inégales), + carte de hauteur → Bump (mm) ; carte du fil → Tangent, anisotropie 0,3 (reflet étiré le long du fil) ; le relief
   de couches procédural de `fdm()` est éteint.

Reliefs (creux entre cordons, part de la hauteur de couche) : tranche 0,22 · dessus 0,16 (buse qui lisse) · face plateau 0,035
(écrasée sur le PEI) · dessous en l'air 0,30 ; couture 0,18. Grain du plateau (`plateau_texture`, `procedes.GRAINS`) : « fin » (défaut) = bruit de 0,06 mm, ± 0,003 mm ; « granuleux » =
plaque granuleuse du F-COM1 (cellules de 0,35 mm, ± 0,05 mm, photo de Lou du 2026-10-26 ; façade noire du F-COM2) ; sommets plus
brillants, **aucune variation à grande échelle**. **Teinte uniforme** (Lou, 2026-10-28 : pas de bruit dans la diffuse, comme le nylon).
**Grain seulement au contact du plateau** (Lou, 2026-10-28) : une face tournée vers le plateau mais en retrait (creux, lamage,
fond de poche) ne l'a jamais touché ; `trajets()` multiplie le masque du grain par la hauteur d'impression (1 jusqu'à 0,03 mm,
0 dès 0,08 mm, nœud « plateau_contact ») ; sans trajets (matière glissée de la bibliothèque), le grain suit la normale seule.
Résolution par défaut : ≥ 5 texels par largeur de cordon (embase : 2401² en buse 0,4, 5043² en 0,2) ; pic mémoire mesuré 10 Go
pour la planche des quatre cas (lancer par `blender_garde.ps1`).
Planche : `outils/planches/planche_fdm_cordons.py` → `G:\Blender\Bibliotheque\planches\fdm_cordons\`.

**Les « plaques » du bouton TFR (Lou, 2026-10-27)** ne viennent pas du grain du plateau : dans MFS, `boitier/commun/scripts/
imperfections.py` pose sur toutes les matières du F-COM1 des cartes de rugosité « frottements » (tuile 17 mm) et « traces de
doigts » (60 mm) ; sur un bouton noir de 10 mm, une tuile de 17 mm donne de grandes plaques mates. Règle : sur une pièce FDM, pas
de frottements ni de traces de doigts à grande échelle ; poussière fine et éparse seulement (à appliquer au chunk-06).

## Réglages sur la pièce (chunk-04, 2026-10-28) : `matieres/reglages_fdm.py` + add-on
Panneau **Impression FDM** (vue 3D > barre latérale > Material library ; installation : [README](../README.md)) et la même chose par
script : `RF.imprimer(ob, matiere=…, buse=0.4, parois=…, motif_dessus=…, angle=…, couture=…, plateau="-Z")`, ou `RF.recalculer(ob)`
avec les réglages déjà posés (`ob.sp_fdm`, enregistrés dans le .blend ; 0 = défaut du profil U1 de la buse). Le calcul :
maillage évalué → `tranchage.py` → `procedes.fdm()` (matière refaite) → `procedes.trajets(copie=False)` ; fichiers dans
`<dossier du .blend>\<nom>_fdm\` (STL, trajets .npz, cartes .exr) ; UV dans « UV_fdm » (les autres UV ne bougent pas) ; un
objet lié (plan qui lie un asset) est refusé : on recalcule dans l'asset. Durées mesurées : bouton TFR 4 s (buse 0,4), 9 s (0,2).
Essai : `outils/essais/essai_reglages_fdm.py` (script et bouton : cartes identiques).
Pour une maquette qui construit ses pièces : `npz = RF.trancher_objet(ob, dossier, 0.4, "-Y")` puis
`PR.trajets(PR.poser(ob, PR.fdm(…)), npz, copie=False, dossier=dossier)` (MFS : embase du F-COM2, bouton TFR du F-COM1). Cartes
en EXR 16 bits compressé ZIP (OpenImageIO, livré avec Blender), résolution ≥ 256 (petites pièces) ; empaquetées dans les assets.

## Limites de l'étude (points ouverts)
- **Multi-matière** : la ligne de commande d'Orca 2.4.2 fond en une matière les STL assemblés (`--assemble`), et trancher les
  matières en objets séparés est faux (la flèche de 0,2 sous une première couche de 0,25 disparaît). Le vrai découpage par
  matière demandera un `.3mf` à parties avec un extrudeur par partie (à faire au chunk-02 si la frontière entre matières se voit).
- Un profil filament aplati fait planter Orca avec plusieurs filaments : `trancher.py` lit le fichier système.
- Pas de vraie pièce imprimée pour comparer : le rendu sera jugé sur ces trajets et sur les photos de Lou
  (`G:\Blender\Bibliotheque\fdm\references\`).
