# Chunk 05 — le nouveau PLA partout dans la bibliothèque

**Statut : `in-progress`** (2026-10-28 : `appliquer_traces` retiré, essai et planche des procédés sur les trajets simulés,
Asset Library régénérée (ancienne archivée, essai d'ouverture OK), `methode/procedes.md` réécrit, planche de validation
`G:\Blender\Bibliotheque\planches\fdm_trajets\planche_fdm_trajets.png`, version 0.2.0 (tag `v0.2.0`) ; reste : validation de Lou) · **Plan : [plan.md](plan.md)** · dépend du chunk-04

## But
Le nouveau PLA remplace l'ancien `procedes.fdm` dans tout le dépôt, sans double vérité, et la validation de Lou se fait sur la
planche à trois colonnes.

## Contenu
- `procedes.fdm` : nouvelle version (réglages des chunks 02-04) ; les anciens chemins (`_couches` procédural, `appliquer_traces`,
  ancien `tranchage.py`) supprimés ou gardés seulement comme repli documenté (décision prise au chunk-03).
- `blender/construire_bibliotheque.py` : les 4 matières FDM de l'Asset Library (PLA noir 0,4 / 0,2, blanc, naturel) régénérées ;
  une matière glissée à la main sur une pièce sans trajets doit rester correcte (couches seulement) et proposer « recalculer ».
- `outils/essais/essai_procedes.py`, `outils/planches/planche_procedes.py` : mis à jour ; la planche des procédés refaite pour
  le FDM.
- **Planche de validation** `outils/planches/planche_fdm_trajets.py` (nouveau) : pour l'embase et le bouton TFR, buses 0,4 et
  0,2 : trajets d'Orca · nos trajets · rendu gros plan (dessus, tranche, face plateau), écarts chiffrés du chunk-02, photos de
  référence de Lou à côté. Sortie : `G:\Blender\Bibliotheque\planches\fdm_trajets\`.
- `methode/procedes.md` : section FDM réécrite pour l'actuel (réglages, bouton, limites) ; `methode/fdm_trajets.md` complété ;
  fiche du catalogue (PLA) : « procédé : voir procedes.fdm » toujours vraie.
- Version du dépôt : tag git (règle du dépôt), noté pour MFS.

## Fini quand
Lou a validé la planche à trois colonnes ; l'Asset Library est régénérée et s'ouvre ; plus aucun appel à l'ancien chemin dans le
dépôt (`grep`).

## Watch-outs
- Règle « à jour, sans obsolète » : supprimer les anciennes sorties régénérables (anciennes planches FDM) une fois la nouvelle
  validée, réécrire la doc pour qu'elle ne décrive que l'actuel.
- Ce chunk ne touche **pas** MFS.
