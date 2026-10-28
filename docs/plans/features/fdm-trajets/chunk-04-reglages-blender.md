# Chunk 04 — réglages sur la pièce et bouton « recalculer les trajets »

**Statut : `in-progress`** (2026-10-28 : `matieres/reglages_fdm.py`, add-on `blender/scripts/addons/material_library_fdm/`, essai
`outils/essais/essai_reglages_fdm.py` passé (script = bouton, écart 0) ; reste : l'essai de Lou dans son Blender) · **Plan : [plan.md](plan.md)** · dépend du chunk-03

## But
Lou règle l'impression d'une pièce dans Blender, Claude fait la même chose par script, et les deux passent par **la même
fonction**. Pas de mise à jour en direct : on règle, puis « recalculer les trajets » (quelques secondes à quelques dizaines de
secondes selon la pièce).

## Contenu
- **Réglages stockés sur l'objet** (propriétés, visibles et modifiables dans Blender) : matière (fiche du catalogue), buse,
  hauteur de couche, nombre de contours, motif et angle du dessus, couture, face sur le plateau / axe de montée, résolution des
  cartes. Valeurs par défaut = celles d'Orca relevées au chunk-01 pour la buse choisie.
- **Panneau « Impression FDM »** (barre latérale de la vue 3D ou propriétés de l'objet) : ces réglages + bouton
  **« Recalculer les trajets »** + état (dernier calcul, réglages utilisés, durée).
- **Fonction Python** équivalente pour les scripts, par ex. `PR.imprimer(ob, matiere="pla_noir", buse=0.4, contours=2, …)` :
  écrit les réglages sur l'objet puis lance le même calcul que le bouton (nom définitif au choix du chunk).
- **Le calcul** : exporte le maillage évalué de l'objet (repère objet), lance la simulation du chunk-02 avec le **Python
  système** (scipy / shapely absents du Python de Blender), puis cuit les cartes et pose la matière (chunk-03). Les cartes sont
  enregistrées en fichiers à côté du `.blend` de la scène (dossier à fixer), pas seulement empaquetées, pour garder les `.blend`
  légers.
- **Installation** : le panneau est livré comme add-on / extension Blender déclaré par le dépôt (comme l'Asset Library du
  chunk-06 du MASTER), activable sur le PC de Lou ; noter la procédure dans `README.md`.

## Fichiers
- `material_library/matieres/procedes.py` (fonction pour les scripts) ; nouveau module du panneau (emplacement au choix,
  par ex. `blender/addon_impression_fdm/`) ; `README.md` ; `summary.md` des dossiers touchés.

## Fini quand
Dans le Blender de Lou : sur l'embase, changer la buse de 0,4 à 0,2 et le nombre de contours, cliquer « recalculer », voir le
résultat ; la même chose par script donne exactement les mêmes cartes (comparaison d'images).

## Watch-outs
- Le chemin du Python système doit être trouvé de façon fiable (réglage de l'add-on, avec une valeur par défaut vérifiée sur le PC
  de Lou) ; message clair si scipy / shapely manquent.
- Objet lié (library override, plans fixes de MFS) : le calcul se fait dans l'**asset**, pas dans le plan qui le lie ; le
  panneau le dit au lieu d'échouer.
- Ne jamais bloquer Blender sans retour : afficher la progression, et refuser une résolution qui dépasse la mémoire prévue.
