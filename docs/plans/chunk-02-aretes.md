# Chunk 02 — arêtes : biseaux, Bevel, congés, lissage

**Statut : `done`** (2026-10-27 : code, essai, doc ; planche d'arêtes validée par Lou, version finale `G:\Blender\Bibliotheque\planches\aretes\planche_aretes.png`) · **Plan : [MASTER.md](MASTER.md)** · dépend du chunk-01

## But
Une règle écrite et des outils communs pour qu'aucune pièce n'ait d'arête vive (règle de Lou), sans bricolage pièce par pièce.

## Fichiers
- `material_library/aretes.py`, repris de MFS (`maquette_grand_format.py`, `photoreal.py`) et généralisé :
  `adoucir(ob, largeur)` (biseau appliqué + normales durcies et pondérées), `bevel_rendu(matiere, rayon)` (nœud Bevel sous le
  relief), `profil_arrondi`, `plaque` (rectangle arrondi épais à arêtes arrondies), `coupe(…, conge=…)` (découpe à congé arrondi
  sur la face visible, comme `fixations.trou_attache`), `lisser(ob, angle=35)`.
- `methode/aretes.md` : la règle — biseau géométrique pour ce qui se voit en silhouette ou se fabrique (rayons d'outil, congés
  d'impression) ; nœud Bevel pour adoucir au rendu ; rayons par défaut par matière (acrylique 0,4, PLA 0,3, vis 0,2, résine…) ;
  quand un maillage doit être une seule surface (topologie régulière, boucles de maintien) ; exceptions (frontières multi-matière).
- Exemples de contrôle : planche d'arêtes (même pièce, rayons 0 / 0,2 / 0,4 / 0,6, rendus en gros plan).

## Fini quand
Les fonctions marchent seules dans une scène vide et la planche d'arêtes est rendue et validée par Lou.

## Watch-outs
- Le nœud Bevel ne marche qu'en Cycles ; il ne change ni le volume ni les STL.
- Les booléens laissent des triangles longs : toujours lisser par angle puis normales pondérées (traînées en étoile vues le
  2026-10-27 sur un dessus en éventail : préférer une face plane unique).
- Un congé sur une encoche ouverte doit garder un contour sans croisement (rayon d'entrée ≥ congé) : bug vu le 2026-10-27.
