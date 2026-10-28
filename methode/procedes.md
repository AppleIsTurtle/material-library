# Procédés de fabrication — quel procédé pour quelle pièce, et son look

Outils : [`material_library/matieres/procedes.py`](../material_library/matieres/procedes.py) (looks),
[`material_library/impression/`](../material_library/impression/summary.md) (encre, décalques, tranchage simulé, lettres imprimées).
Planche : [`outils/planches/planche_procedes.py`](../outils/planches/planche_procedes.py). La matière vient du catalogue
([matieres.md](matieres.md)) ; le procédé ajoute ce que la fabrication laisse.

```python
from material_library.matieres import procedes as PR, reglages_fdm as RF
RF.imprimer(ob, matiere="pla_noir", buse=0.4, plateau="-Y")          # FDM : vrais trajets de la buse (reglages_fdm, panneau)
PR.poser(ob, PR.fdm("pla_noir", buse=0.4, axe="Y", plateau="-Y"))   # FDM sans trajets : couches procédurales le long de y
PR.poser(ob, PR.sla("sla_jlc_black", "poncee_huilee"))
PR.poser(ob, PR.mjf("nylon_pa12_noir"))
PR.poser(ob, PR.acrylique_laser("peinture_fs36118", masque=np.load("lettres_exact.npz")))
PR.poser(ob, PR.metal("alu_anodise_gris_fonce"))
```
**L'orientation d'impression est un paramètre de la pièce** (axe des couches, face sur le plateau) : elle décide où se voient
les couches et le grain du plateau.

## Quel procédé pour quelle pièce (règle de Lou, F-COM2, 2026-10-26 / 27)
| Pièce | Procédé | Pourquoi |
|---|---|---|
| Petites pièces faciles à imprimer (cadres, entretoises, boutons, embase) | **FDM chez l'imprimeur FDM** (Snapmaker U1, PLA) | « toutes les pièces assez petites et faciles à imprimer, on les fait chez lui » ; matière ≈ 0,15–0,20 € par façade |
| Pièce visible, nette, lisse (caisson, supports) | **SLA JLC Black poncée huilée** (JLC3DP) | aspect « injecté », ≈ 13 $ caisson + 2 supports (estimé) |
| Plaque plate à inscriptions rétroéclairées | **acrylique découpé au laser, peint « jour / nuit »** | lettres gravées jusqu'à la sous-couche, rétroéclairage |
| Pièce mécanique robuste, grain mat | MJF PA12 (JLC3DP) | HDT 175 °C ; mais ≈ 2 × le prix de la résine |
| Façade « pro » sans rétroéclairage | alu 6061 usiné, sablé anodisé + marquage laser (JLCCNC) | ≈ 10–30 $ la pièce (estimé, devis manuel) |
« L'argent là où ça se voit » : la pièce qu'on regarde mérite le procédé cher, le reste va chez l'imprimeur FDM.

## Limites de conception
**FDM, buse 0,4** (profil U1 d'OrcaSlicer : couches 0,2, cordons 0,42 / 0,45, 2 parois) — buse 0,2 : couches 0,1, cordons
0,22, 4 parois ([fdm_trajets.md](fdm_trajets.md)) :
- parois ≥ 0,8 (deux cordons) ; cloisons ≥ 1,2 ; un trait plus fin que 0,55 × cordon (0,25 en buse 0,4) n'est pas tracé ;
- coins de lettres arrondis par le cordon (pas plus vifs qu'un demi-cordon) ; texte en buse 0,4 : capitales ≥ 2,8 mm
  (`TXT_CAP` 4,0 du F-COM1) ; en buse 0,2, le texte est net (impressions réelles, Lou 2026-10-26) ;
- nervures d'écrasement (ajustement serré) : **à valider sur une impression d'essai** ;
- les trajets simulés (tranchage.py) sont calés sur OrcaSlicer, profil U1 par défaut ; les lettres simulées (lettres.py) et les
  réglages réels de l'imprimeur FDM restent à confirmer sur une impression d'essai.

**SLA (JLC3DP)** : parois ≥ 2,5 mm sur le caisson ; inserts posés par JLC (M3 à M5, ≈ 0,53 $ l'insert, 3 mm de paroi autour,
portée plane 14 × 14) ; pas au soleil (HDT 54–65 °C) ; JLC Black : pas de peinture possible.

**MJF / SLS** : teinte uniforme (la teinture ne donne pas un noir profond : #1f2022), grain de poudre ; gris naturel : peinture mate seulement.

**Acrylique laser** : plaque plane, coins à petit rayon (R 1,0 / 1,2 sur la réplique) ; découpes chanfreinées ou à congé sur la face
vue ; lettres découvertes jusqu'à la sous-couche blanche (jamais de blanc absolu).

## Coûts relevés (avec leur date)
| Quoi | Prix | Date / source |
|---|---|---|
| JLC3DP : prix matière ≈ volume (cm³) × 1,3 g/cm³ × prix au g ; minimum par pièce | 9600 0,07 $/g (min 0,32) · Grey 0,12 · JLC Black 0,13 (min 1,05) · PA12 0,29 (min 1,05) · SLS 3201PA-F 0,19 · ABS FDM 0,22 (min 3,16) | moteur de devis, 2026-10-26 |
| Caisson creux 50,5 cm³ | 9600 4,6 $ · JLC Black 8,5 $ · PA12 noir 19,0 $ · SLS 12,5 $ | estimation, 2026-10-26 |
| Inserts laiton posés par JLC | ≈ 0,53 $ l'insert | 2026-10-26 |
| Port vers la France | DHL ≈ 27 $/kg (DDP conseillé) ; Global Standard 10–16 $ (≤ 1,5 kg) | 2026-10-26 |
| Filament PLA mat | 10 à 24 €/kg (Bambu Matte recharge 16,99 € ; Polymaker Panchroma ≈ 18–20 €) | 3DJake & co., 2026-10-25 |
| Usinage alu JLCCNC | ≈ 10–30 $ la pièce | estimation, 2026-10-26 |
Source détaillée : MFS `docs/plans/features/boitier/features/grand-format/etude-matieres-jlc.md` et
`docs/plans/features/boitier/etude_filament_facade/`. Les devis réels priment : refaire le relevé avant de chiffrer.

## Chaîne FDM complète (trajets et lettres)
Détail et mesures : [fdm_trajets.md](fdm_trajets.md).
1. **Le plus simple** : dans Blender, panneau **Impression FDM** (vue 3D > Material library) ou `RF.imprimer(ob, matiere=…, buse=…,
   parois=…, motif_dessus=…, couture=…, plateau=…)` : la pièce est tranchée (`impression/tranchage.py`, Python système), sa
   matière refaite par `PR.fdm()` et ses trajets posés par `PR.trajets()` ; fichiers dans `<nom du .blend>_fdm\`.
2. **Pas à pas** (planches) : `python material_library/impression/tranchage.py trajets.npz 0.4 piece.stl --plateau -Y [--set parois=1 …]`,
   puis dans Blender `PR.trajets(PR.poser(o, PR.fdm(…)), "trajets.npz")` sur le même maillage que le STL.
3. Lettres dans la masse : `python material_library/impression/lettres.py lettres.stl lettres.npz 0.4` (ou `exact` pour une gravure
   laser), puis `PR.lettres_imprimees(m, np.load("lettres.npz"))`.
Une matière FDM glissée depuis la bibliothèque n'a que des couches procédurales : « Recalculer les trajets » lui donne les vrais.

## Impressions à l'encre
`impression/encre.py` : une encre réelle s'étale (bords adoucis et gonflés), suit le grain du support, varie d'épaisseur, a des
micro-manques (Lou, 2026-10-26 : « un peu baveuses, pas parfaitement imprimées »). `texte.py` (marquages de composants, police
« points » des jets d'encre industriels), `calques.py` (grandes surfaces : textes, traits, anneaux, aplats), `decalques.py`
(décalque posé à 4 µm de la pièce dans Blender).
