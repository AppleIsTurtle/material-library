# Plan — PLA FDM d'après les vrais trajets de la buse (`fdm-trajets`)

**Statut : `in-progress`** (plan écrit le 2026-10-27 ; chunks 01, 02, 03 faits le 2026-10-28 ; 04 et 05 en attente de Lou) · demandé par Lou le 2026-10-27 · plan parent :
[MASTER.md](../../MASTER.md) (suite du chunk-04 « procédés »).

## Demande (Lou, 2026-10-27)
« Je veux avoir un matériau plus convaincant pour les impressions 3D (PLA par exemple). […] Il faut pouvoir avoir un rendu
réaliste avec quelques paramétrages selon la taille de la buse et le pathing du remplissage. » Cinq photos de référence
(pièces FDM réelles), copiées dans `G:\Blender\Bibliotheque\fdm\references\` (fiche `references.md` écrite au chunk-01).

Ce qui ne va pas aujourd'hui (Lou) :
- le **bouton TFR** du F-COM1 a des « plaques d'imperfection qui ne sont pas la réalité » (taches claires sur le dessus,
  `boitier/f-com/f-com1/rendus/produit/f-com1_hero_v5.png` de MFS) ;
- il manque les **stries de filament** sur la **2e façade de la F-COM2 réplique** : l'embase (`GF_EMBASE`, PLA noir de l'imprimeur FDM),
  rendue « PLA noir lisse » (`maquette_grand_format.py`, ~l. 1078 de MFS).
- « Les impressions font les contours, 1 ou 2 tours, puis ensuite il y a des algorithmes pour optimiser le remplissage. »

Décisions de Lou (questions du 2026-10-27) :
1. **D'abord une vraie compréhension** : étudier les trajets réels d'un trancheur, **puis** écrire notre propre script qui simule
   le résultat (le trancheur reste l'étalon, les rendus n'en dépendent pas).
2. **Partout dans la bibliothèque** : le nouveau PLA remplace `procedes.fdm` ; toutes les pièces FDM en profitent.
3. **Impression propre** pour les rendus de vente : les traces normales du procédé, aucun défaut de pièce ratée.
4. **Réglages sur la pièce**, modifiables par Lou dans Blender **et** par Claude par script ; un bouton **« recalculer les
   trajets »** suffit (pas de mise à jour en direct).
5. Pas de vraie pièce imprimée à photographier : on juge sur les trajets du trancheur et sur les photos de référence.
6. Embase imprimée face avant sur le plateau ; étalon = profil U1 d'OrcaSlicer par défaut, buse 0,4 (voir plus bas).

## Point de départ (2026-10-27)
- `material_library/matieres/procedes.py` : `fdm()` = shader procédural (lignes de couches en bosse sinus le long d'un axe objet,
  teinte et rugosité qui varient, IOR 1,46) + `plateau_texture()` (grain du PEI sur la face posée) + `appliquer_traces()` (cuit
  position / normale en UV, puis hauteur texel par texel depuis un `.npz`, en relief Bump seulement).
- `material_library/impression/tranchage.py` (99 lignes, Python système : numpy, scipy, shapely) : notre simulation actuelle, écrite
  sans trancheur de référence. **Limites** : pièce toujours posée face −y sur le plateau, 2 périmètres et dessus à 45° (monotone)
  en dur, seule la **dernière** couche donne une carte de dessus (les marches intermédiaires n'ont pas de dessus), cordons rendus
  en relief seulement (pas d'effet de reflet le long du fil).
- Planche validée le matin même : `G:\Blender\Bibliotheque\planches\procedes\fdm04_*.png`. De près, les couches se lisent comme
  de fines rayures gravées sur une surface mate, pas comme des cordons arrondis qui accrochent la lumière (photos 2 et 5 de Lou) ;
  aucun trajet sur les dessus (photos 1 et 4).
- Utilisateurs de `PR.fdm` dans ce dépôt : `blender/construire_bibliotheque.py` (4 matières FDM de l'Asset Library),
  `outils/essais/essai_procedes.py`, `outils/planches/planche_procedes.py`. MFS ne l'importe pas encore (chunk-09 du MASTER) :
  il utilise `photoreal.pla_fdm` / `pla_imprimeur` / ses propres traces.
- Aucun trancheur installé sur le PC de Lou. Blender 5.1 (`F:\Blender\5.1\blender.exe`) ; Python système avec numpy 2.4,
  scipy 1.18, shapely 2.1 (le Python de Blender n'a ni scipy ni shapely).

## Objectif
Une pièce imprimée chez l'imprimeur FDM (Snapmaker U1, PLA) se reconnaît au premier coup d'œil, de près comme de loin :
- **tranches** : cordons empilés à section arrondie, qui accrochent la lumière le long du fil ; couture discrète (point de départ
  des tours, alignée ou non selon le réglage) ;
- **dessus** (toute surface exposée vers le haut, y compris les marches intermédiaires) : 1 ou 2 tours de contour (bord extérieur
  **et** chaque trou), puis le remplissage du dessus selon le motif du trancheur, avec ses demi-tours et ses petits manques
  réels ;
- **face posée sur le plateau texturé** : grain fin et régulier du PEI, sans taches ;
- **propre** : ni fils, ni affaissement, ni dessus creusé, ni grosses taches d'imperfection ; les imperfections d'usage
  (poussière, frottements) restent possibles mais ne doivent pas ressembler à des plaques ;
- paramétrée par : **buse** (0,4 / 0,2), **hauteur de couche**, **nombre de contours**, **motif et angle du remplissage du dessus**,
  **couture**, **orientation d'impression** (quelle face sur le plateau, axe de montée) — modifiables dans Blender sur l'objet et
  par une fonction Python, appliqués par « recalculer les trajets ».

## Périmètre
**Dedans** : étude des trajets d'OrcaSlicer (profil Snapmaker U1) ; notre simulation de tranchage généralisée et calibrée sur
lui ; le rendu des cordons (relief + reflet le long du fil) ; les réglages sur l'objet et le bouton dans Blender ; le remplacement
de `procedes.fdm` et de ses utilisateurs dans ce dépôt (Asset Library, essai, planche, `methode/procedes.md`) ; l'application aux
pièces FDM de MFS citées par Lou (embase de la réplique, bouton TFR) puis aux autres pièces FDM de MFS.
**Dehors** : les défauts d'impression (fils, surplombs affaissés, dessus creusés : option possible plus tard, pas maintenant) ;
le remplissage **interne** (grille, gyroïde : invisible sur une pièce propre, seul son effet sur le dessus compte) ; les autres
procédés (SLA, MJF, acrylique, métaux) ; un trancheur embarqué dans les rendus (OrcaSlicer ne sert qu'à l'étude et au contrôle) ;
la mise à jour en direct dans Blender.

⚠ **Écart avec le MASTER** : son périmètre met « la régénération de l'asset du F-COM1 » dehors. Lou demande que le bouton TFR
du F-COM1 soit corrigé : le chunk-06 touche donc l'asset du F-COM1 (`G:\Blender\MFS\assets\boitier\boitier.blend`, shading retouché
par Lou) — avec archive avant écriture et accord de Lou, comme toujours pour ce fichier.

## Chunks
| Chunk | Contenu | Dépend de |
|---|---|---|
| [chunk-01-etude-orca](chunk-01-etude-orca.md) | installer OrcaSlicer (accord de Lou), trancher l'embase et le bouton TFR, lire le G-code, comprendre et documenter les trajets | — |
| [chunk-02-simulation](chunk-02-simulation.md) | notre simulation de tranchage généralisée (orientation, réglages, tous les dessus), comparée au G-code d'Orca | 01 |
| [chunk-03-rendu-cordons](chunk-03-rendu-cordons.md) | trajets → cartes (hauteur, direction du fil) → shader : cordons arrondis, reflet le long du fil, plateau sans taches | 02 |
| [chunk-04-reglages-blender](chunk-04-reglages-blender.md) | réglages sur l'objet, panneau « Impression FDM », bouton « recalculer les trajets », même fonction pour les scripts | 03 |
| [chunk-05-bibliotheque](chunk-05-bibliotheque.md) | `procedes.fdm` remplacé ; Asset Library, essai, planche, méthode ; planche de validation à trois colonnes | 04 |
| [chunk-06-mfs](chunk-06-mfs.md) | MFS : embase de la réplique, bouton TFR (taches), puis les autres pièces FDM ; rendus refaits | 05 |

## Orientation de l'embase et réglages de référence (Lou, 2026-10-27)
- L'embase est imprimée **face avant sur le plateau** (paquet de l'imprimeur FDM, `maquette_grand_format.py`, `facade_embase`,
  `sens = "face"`) : sa face visible porte le grain du PEI, ses **tranches** les cordons et la couture ; le dessus en lignes est
  au dos (vu seulement sur l'éclaté et les vues de dos). Le rendu actuel, lisse sur la face, est faux et sera corrigé dans ce sens.
- **Étalon = profil Snapmaker U1 d'OrcaSlicer, réglages par défaut** (pas le profil de l'imprimeur FDM) ; **buse 0,4 par défaut** pour
  les rendus, 0,2 en option (texte fin).

## Comment on juge (choix de Claude, à valider par Lou au chunk-05)
Une **planche à trois colonnes** par pièce (embase de la réplique, bouton TFR) et par buse : trajets d'OrcaSlicer (G-code tracé) ·
trajets de notre simulation · rendu Cycles en gros plan (dessus, tranche, face plateau). Plus, à côté, les photos de référence de
Lou à la même échelle. Lou valide à l'œil ; les écarts mesurés au chunk-02 sont donnés en chiffres sur la planche.

## Watch-outs (communs)
- Règles du dépôt (`CLAUDE.md`) : `summary.md` partout, données lourdes sur `G:\Blender\Bibliotheque\` (G-code, cartes cuites,
  planches), Blender par `blender_garde.ps1`, commit dans la même commande que le `git add`.
- **Ne pas changer un rendu de MFS sans le vouloir** : ce plan change **volontairement** le look FDM ; seul le chunk-06 touche MFS,
  pièce par pièce, avec avant / après montrés à Lou ; `outils/non_regression.py` sert à prouver que **rien d'autre** ne bouge.
- Télécharger OrcaSlicer = **accord explicite de Lou** (nom du fichier, source officielle, taille) avant tout téléchargement.
- Mémoire : une carte 4096² en float ≈ 0,5 Go (voir `appliquer_traces`) ; une grande façade en buse 0,2 peut demander beaucoup ;
  borner la résolution et prévenir avant un calcul lourd (PC de Lou planté le 2026-09-30).
- Chaque chunk se termine par un aperçu regardé par Claude lui-même avant d'être montré à Lou (règle d'auto-vérification).
