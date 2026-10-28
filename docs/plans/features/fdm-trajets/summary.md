# summary — docs/plans/features/fdm-trajets/

Feature « PLA FDM d'après les vrais trajets de la buse » (Lou, 2026-10-27) : étude d'OrcaSlicer (profil Snapmaker U1), notre
simulation calibrée sur lui, rendu des cordons, réglages sur la pièce + bouton « recalculer les trajets », remplacement de
`procedes.fdm` dans la bibliothèque, puis MFS (embase de la F-COM2 réplique, bouton TFR du F-COM1).

| Fichier | Rôle |
|---|---|
| plan.md | Plan de la feature (demande, décisions de Lou, point de départ, objectif, périmètre, chunks, critère de validation) |
| chunk-01-etude-orca.md | Installer OrcaSlicer, trancher l'embase et le bouton TFR, lire le G-code, documenter les vrais trajets |
| chunk-02-simulation.md | Réécrire `impression/tranchage.py` (orientation, réglages, tous les dessus), comparé au G-code |
| chunk-03-rendu-cordons.md | Trajets → cartes (hauteur, direction du fil) → shader ; plateau sans taches |
| chunk-04-reglages-blender.md | Réglages sur l'objet, panneau « Impression FDM », bouton « recalculer », fonction pour les scripts |
| chunk-05-bibliotheque.md | Nouveau `procedes.fdm` partout dans le dépôt ; planche de validation à trois colonnes |
| chunk-06-mfs.md | MFS : embase de la réplique, bouton TFR, puis les autres pièces FDM |

Données hors git : `G:\Blender\Bibliotheque\fdm\` (`references\` : les 5 photos de Lou, copiées le 2026-10-27).

## Historique
- 2026-10-27 : création (plan et 6 chunks `pending`).
- 2026-10-28 : chunks 01 (étude d'OrcaSlicer) et 02 (simulation calée) faits.
- 2026-10-28 : chunk-03 (rendu des cordons) validé par Lou ; chunk-04 (réglages, bouton) écrit et essayé.
- 2026-10-28 : chunk-05 : nouveau FDM partout dans la bibliothèque, planche de validation, version 0.2.0.
