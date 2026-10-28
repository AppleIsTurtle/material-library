# Chunk 06 — le .blend « bibliothèque de matières » (Asset Library)

**Statut : `done`** (2026-10-27 : `G:\Blender\Bibliotheque\bibliotheque_matieres.blend` généré en qualité finale, 22 matières et 7 pièces de visserie ; ouverture, aperçus, catalogues et rendu d'une matière ajoutée dans le studio vérifiés (écart 0) ; aperçus validés par Lou) · **Plan : [MASTER.md](MASTER.md)** · dépend des chunks 03, 04, 05

## But
Lou ouvre l'*Asset Browser* de Blender et glisse n'importe quelle matière du projet (ou une vis toute faite) dans sa scène.

## Fichiers
- `blender/construire_bibliotheque.py` : construit `bibliotheque_matieres.blend` (emplacement à confirmer :
  `G:\Blender\Bibliotheque\`) à partir du catalogue : une matière par entrée, marquée comme asset, rangée dans des catalogues
  (Résines, Impression FDM, Métaux, Peintures, Verres…), avec aperçu rendu (boule ou plaque) et description (procédé, fiche) ;
  quelques vis et rondelles toutes faites ; images packées.
- `blender/summary.md`, `methode/matieres.md` (comment déclarer la bibliothèque dans Blender : Préférences → Fichiers → Asset
  Libraries ; à faire par Lou, ou par script s'il le demande).

## Fini quand
La bibliothèque s'ouvre dans Blender 5.1, chaque asset a son aperçu, et une matière glissée dans une scène neuve rend comme dans
la planche du chunk-03.

## Watch-outs
- Le `.blend` est généré : jamais retouché à la main (les retouches de Lou vont dans le catalogue) ; archive avant chaque
  régénération, comme les assets de MFS.
- Une matière glissée est **ajoutée** (copie) par défaut : la doc explique *Link* / *Append*.
- Les cartes d'imperfections doivent être packées ou sur un chemin commun.
