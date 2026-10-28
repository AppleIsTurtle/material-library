# Chunk 03 — catalogue des matières

**Statut : `done`** (2026-10-27 : catalogue de 18 fiches, couleurs, doc, essai ; planche validée par Lou, version finale `G:\Blender\Bibliotheque\planches\matieres\planche_matieres.png` ; FS 36118 : Lou garde la base #3b3f45 validée dans MFS — rendu de face du F-COM2 #5f656c — la pastille de la bibliothèque la mesure #646a71) · **Plan : [MASTER.md](MASTER.md)** · dépend des chunks 01, 02

## But
Chaque matière du projet a une fiche et une fonction qui la construit, avec des valeurs physiques mesurées et une base de couleur
compensée pour le studio de rendu.

## Fichiers
- `material_library/matieres/catalogue.py` : une entrée par matière — nom, procédé, base de couleur (et base compensée par studio),
  rugosité, métal, voile, IOR, transmission, grain (pas, amplitude, netteté), rayon de Bevel par défaut, photo de référence,
  source de la mesure, date, décision de Lou.
  Premières entrées (reprises de MFS) : peinture acrylique FS 36118 « jour / nuit » (grain net façon résine huilée), SLA JLC Black
  poncée huilée, résine 9600 blanche, PLA noir FDM (imprimeur FDM), PLA blanc / naturel, nylon PA12 MJF, inox naturel, acier oxydé noir
  usé, laiton des inserts, verre / acrylique fumé, PVC du câble, alu brossé de l'étiquette.
- `material_library/matieres/couleurs.py` : compensation à la pipette (rendu d'une pastille dans le studio, écart à la teinte visée,
  correction de la base) — reprend `carte_pipette.py`.
- `methode/matieres.md` : comment ajouter une matière (photo réelle d'abord, mesures, pipette, gros plan de contrôle) ; règles de
  Lou (teinte uniforme, relief seul pour le grain ; sa teinte prime sur les photos).

## Fini quand
Chaque matière se construit par son nom, une planche (boule + plaque à arêtes arrondies, même éclairage que le studio du site) est
rendue pour toutes, et les teintes rendues tombent sur les cibles (écart ≤ 3 par canal).

## Watch-outs
- Une base compensée dépend du studio (celui du site) : la fiche dit pour quel studio.
- Ne pas confondre le PLA de l'imprimeur FDM (couches) et la résine JLC (lisse ou poncée) : ce sont des procédés (chunk-04).
- Les matières liées depuis un asset ne se modifient pas (`_neuf` refuse les matières liées).
