# summary — outils/planches/

Planches de contrôle rendues dans le studio du site (hero.blend de MFS ouvert en lecture, jamais enregistré). Rendus et planches
assemblées hors git : `G:\Blender\Bibliotheque\planches\<planche>\`. Lancer Blender via `D:\Claude\MFS\outils\blender_garde.ps1`.

| Fichier | Rôle | Dépendances |
|---|---|---|
| studio.py | Prépare la scène (F-COM1 écarté, collection PLANCHE, GPU OptiX, `quick` = 50 % / 48 échantillons), caméras, rendu | Blender 5.1, hero.blend, material_library |
| assembler.py | Assemble les rendus d'une planche (grille.json écrite par chaque planche_*.py) en une image titrée | Python système + Pillow |
| planche_aretes.py | Planche du chunk-02 : même pièce, arêtes 0 / 0,2 / 0,4 / 0,6 par la géométrie (plaque, coupe à congé) et par le nœud Bevel ; contrôle `aretes_vives` ; option `nc=` (segments des congés) | studio.py, material_library.aretes |
| planche_matieres.py | Planche du chunk-03 : chaque fiche sur boule + plaque ; pipette sur une pastille de face, compensation des fiches à cible (écart ≤ 3) ; relevé releve.json ; option `seul=` | studio.py, catalogue, couleurs, imperfections.uv_mm |
| planche_procedes.py | Planche du chunk-04 : une plaque (« COM 1 », fenêtre) par procédé, face et tranche ; étape `stl` puis simulations (impression/tranchage.py, lettres.py) puis rendu ; colonnes FDM : trajets simulés (tranchage.py lancé tout seul) posés par `procedes.trajets` | studio.py, matieres.procedes |
| planche_fdm_trajets.py | Planche de validation de fdm-trajets (Python système) : embase et TFR, buses 0,4 / 0,2 ; face, dessus, tranche ; OrcaSlicer · notre simulation · rendu, écarts chiffrés, photos de Lou → planches\fdm_trajets\ | outils/fdm (comparer, gcode, planche_orca), rendus de planche_fdm_cordons.py |
| planche_fdm_cordons.py | Planche du chunk-03 de fdm-trajets : embase de la F-COM2 et bouton TFR (STL de MFS), buses 0,4 / 0,2, trajets simulés posés par `procedes.trajets` ; gros plans face (plateau), tranche, dos ; option `cas=` | studio.py, matieres.procedes, impression/tranchage.py (Python système) |

## Historique
- 2026-10-27 : création (chunk-02) : studio.py, assembler.py, planche_aretes.py.
- 2026-10-27 : planche_matieres.py (chunk-03) ; notes sur plusieurs lignes dans assembler.py.
- 2026-10-27 : planche_procedes.py (chunk-04).
- 2026-10-27 : assembler.py pose les images à fond transparent (aperçus d'assets) sur un gris clair (chunk-06).
- 2026-10-28 : planche_fdm_cordons.py (feature fdm-trajets, chunk-03).
- 2026-10-28 : planche_fdm_trajets.py ; planche_procedes.py passe aux trajets simulés (chunk-05).
