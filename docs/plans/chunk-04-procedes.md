# Chunk 04 — looks par procédé de fabrication

**Statut : `done`** (2026-10-27 : procedes.py, impression/, doc, essai ; planche validée par Lou, version finale `G:\Blender\Bibliotheque\planches\procedes\planche_procedes.png`) · **Plan : [MASTER.md](MASTER.md)** · dépend du chunk-03

## But
Une pièce prend l'aspect de sa vraie fabrication en une ligne : « imprimée chez l'imprimeur FDM en PLA, buse 0,4, couches de 0,2, face sur
le plateau texturé » ou « SLA JLC Black poncée huilée ».

## Fichiers
- `material_library/matieres/procedes.py` :
  - **FDM** (Snapmaker U1 de l'imprimeur FDM) : couches le long de l'axe d'impression (`pla_fdm` / `couches_fdm`), face sur plateau
    texturé, traces de tranchage simulées (reprend `appliquer_traces` + `simulation_lettres_facade.py`), multi-matière ; buses
    0,4 / 0,2 ;
  - **SLA JLC** : lisse, ou poncée et huilée (grain net) ; résine 9600 translucide dans les bords ;
  - **MJF / SLS** : grain de poudre en relief, teinte uniforme (règle « nylon » de Lou) ;
  - **acrylique** découpé au laser et peint (« jour / nuit » : lettres gravées jusqu'à la sous-couche, rétroéclairage) ;
  - **métaux** : inox naturel, acier oxydé noir, laiton, alu brossé ;
  - **impressions** : encre « un peu baveuse » (`encre.py`), décalques, calques imprimés.
- `methode/procedes.md` : quel procédé pour quelle pièce (petites pièces faciles → l'imprimeur FDM ; visible et net → JLC ; plat →
  laser), limites (parois ≥ 0,8 en buse 0,4, cloisons ≥ 1,2, nervures d'écrasement à valider en FDM), coûts relevés (JLC, filament).

## Fini quand
La planche « une pièce, tous les procédés » est rendue (gros plans des tranches et des faces) et validée par Lou.

## Watch-outs
- L'orientation d'impression décide où se voient les couches : elle fait partie des paramètres, pas une constante.
- Les coûts JLC et filament datent du 2026-10-26 / 27 : les fiches gardent la date.
