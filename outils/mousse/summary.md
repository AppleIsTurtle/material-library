# summary — outils/mousse/

Référence et calibrage de la mousse PE. Méthode : [methode/mousses.md](../../methode/mousses.md). Images écrites par défaut dans
`<DONNEES>\planches\mousse\` (hors git).

| Fichier | Rôle | Dépendances |
|---|---|---|
| geometrie_reference.py | Mousse en vraie géométrie (Geometry Nodes, grille SDF), par étapes de fabrication : bulles, scie à ruban, jet d'eau, collage ; mesures par rayons | Blender 5.1 |
| calibrer.py | Mesure `mousse.hauteur` sur une coupe plane et cherche les réglages qui retrouvent les mesures de la géométrie | Blender 5.1, matieres.mousse |
| comparer.py | Même bloc, mêmes cadrages que la géométrie, avec la matière calibrée | Blender 5.1, matieres.catalogue, matieres.mousse |

## Historique
- 2026-11-01 : création (repris du projet F-COM, calage mousse).
