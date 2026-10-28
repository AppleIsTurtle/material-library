# summary — methode/essai/

Essai de la méthode de conception ([../conception_boitier.md](../conception_boitier.md)) sur un **panneau gabarit** de 5 crans
(145,67 × 47,24 : une fenêtre d'afficheur, un bouton, deux inscriptions éclairées, quatre attaches sur les côtés, deux petites
vis traversantes), avec les seuls outils de `material_library.conception` et `material_library.aretes`, sans code du F-COM2.

| Fichier | Rôle |
|---|---|
| essai_panneau_gabarit.py | le script de l'essai (scène vide, Blender 5.1 en arrière-plan par `blender_garde.ps1`) : étapes 1 à 9, asset d'essai `G:\Blender\Bibliotheque\essais\panneau_gabarit.blend`, aperçus |
| journal_essai.txt | sortie de l'essai : chaque étape et son contrôle |
| chiffrage_gabarit.md | tableau « l'argent là où ça se voit » écrit par l'essai |
| apercu_hero.jpg, apercu_face.jpg, apercu_dos.jpg, apercu_nuit.jpg | aperçus Cycles 48 échantillons, studio neutre d'essai (posé à 15° sur ses supports ; nuit : inscriptions rétroéclairées) |

## Résultats (2026-10-27)
- Dessin à plat : 0 erreur, 4 remarques (attaches à 1,35 du bord → trous ouverts en U).
- Colonnes d'insert : R 5,70, 2,90 de matière autour de l'insert M4 ; la boîte à lumière s'arrête à x ± 60,33.
- Lumière : **sans jours dans l'embase, 2 chambres bouchées sur 2** (le piège du F-COM2 est attrapé) ; avec les jours, 0.
- Trous : 0 bouché (vis à travers plaque, embase, boîte à lumière, carte ; attaches à travers l'embase).
- Collisions : 0 sur 37 pièces (4 contacts voulus : inserts emmanchés, patins dans leurs poches, LED et bouton tactile sur la carte).
- Parois : 0 sous 1,2 (boîte à lumière), 0 sous 0,8 (collerettes), 0 sous 1,0 (caisson).
- Chiffrage : 24,80–37,50 € par boîtier pour le boîtier seul (sans carte ni lest ni emballage) ; la plaque « jour / nuit » reste
  le prix inconnu.
- Vu sur les aperçus : les supports du F-COM2 (dessinés pour 66 mm de haut) paraissent massifs sous un panneau de 47 mm :
  leurs cotes (`supports.SUPPORT_PANNEAU`) seraient à réduire pour un panneau bas.

## Historique
- 2026-10-27 : création (chunk-07).
