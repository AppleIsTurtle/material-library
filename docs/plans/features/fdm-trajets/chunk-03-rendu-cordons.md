# Chunk 03 — rendu des cordons (trajets → cartes → shader)

**Statut : `done`** (2026-10-28, validé par Lou : `procedes.trajets`, `impression/cartes.py`, grain du plateau refait, planche
`G:\Blender\Bibliotheque\planches\fdm_cordons\planche_fdm_cordons.png` en qualité finale ; cause des « plaques » du TFR trouvée
(imperfections de MFS, voir chunk-06)) · **Plan : [plan.md](plan.md)** · dépend du chunk-02

## But
Que les trajets simulés se voient comme du vrai fil déposé : cordons à section arrondie qui accrochent la lumière **le long** du
fil (reflet étiré, comme sur les photos 2, 3 et 5 de Lou), creux entre les cordons, couture discrète, dessus lisibles ;
face plateau au grain fin et régulier, **sans taches**.

## Pistes (au choix du chunk, essais à l'appui)
- Cartes cuites en UV, comme `appliquer_traces` le fait déjà (position / normale cuites dans Cycles, puis calcul en numpy) :
  **hauteur** (profil arrondi du cordon, largeur réelle) et **direction du fil** (tangente du trajet) ; la direction pilote
  l'anisotropie du Principled BSDF (Anisotropic + Tangent / rotation) pour le reflet étiré ; légère variation de teinte et de
  brillance d'un cordon à l'autre.
- Relief : Bump / normal map par défaut ; déplacement réel (micro-déplacement) seulement si un gros plan l'exige — à décider sur
  un essai côte à côte, temps de rendu noté.
- Résolution : assez de texels par cordon pour un gros plan (au moins 4 par largeur de cordon), bornée en mémoire ; pièces
  grandes : tuiles UDIM ou textures par face si une seule image ne suffit pas.
- Plateau texturé : reprendre `plateau_texture()` mais vérifier sur une photo de PEI texturé que le grain est **régulier** ;
  chercher l'origine des « plaques » du bouton TFR (carte d'imperfections de MFS ? bruit du plateau à `tuile` 0,35 ? les deux) et
  la supprimer côté bibliothèque ; règle à écrire : sur une pièce FDM, les imperfections d'usage restent fines et éparses.
- Matière : teinte, rugosité et IOR viennent de la fiche du catalogue (`catalogue.py`) comme aujourd'hui ; PLA noir mat, gris
  satiné, blanc, naturel translucide.

## Fichiers
- `material_library/matieres/procedes.py` (fonctions de cuisson et de shader FDM ; l'ancien `_couches` procédural peut rester comme
  repli pour une pièce **sans** trajets calculés, à décider) ; `summary.md`.
- `outils/essais/essai_fdm_cordons.py` (nouveau) : plaque d'essai + embase, gros plans dessus / tranche / plateau.

## Fini quand
Gros plans de l'embase et du bouton TFR (buses 0,4 et 0,2) regardés par Claude, puis montrés à Lou à côté de ses photos ; Lou
dit que ça ressemble à une vraie impression.

## Entrée (depuis le chunk-02, 2026-10-28)
`material_library/impression/tranchage.py` rend des **trajets** au format de `outils/fdm/gcode.py` (couche, z, hauteur, largeur, type,
x0, y0, x1, y1 dans le repère d'impression) + `rotation` (STL → impression) + `reglages` (JSON) ; `T.trancher([triangles…],
T.reglages(0.4, …), plateau="-Y")`. `procedes.appliquer_traces` lit encore l'ancien format (cartes dessus / ponts) : la remplacer
ici ; `outils/planches/planche_procedes.py` et `outils/essais/essai_procedes.py` l'appellent (mis à jour au chunk-05).

## Watch-outs
- Règle « pas d'arête vive » : les arêtes gardent le Bevel de rendu (`aretes.RAYONS["pla"]`).
- Les couleurs restent celles validées (pipette) : le relief ne doit pas éclaircir la teinte moyenne ; contrôler à la pipette.
- Aperçus d'abord (faible échantillonnage), rendus finaux ensuite.
