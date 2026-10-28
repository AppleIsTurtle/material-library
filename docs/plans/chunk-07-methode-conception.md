# Chunk 07 — méthode de conception d'un boîtier

**Statut : `done`** (2026-10-27 : méthode et essai relus et validés par Lou) · **Plan : [MASTER.md](MASTER.md)** · dépend des chunks 02, 05

## But
Concevoir un nouveau panneau (F-COM, transpondeur, suivants, autres projets) en héritant de la démarche du F-COM2 : on part de
règles et d'outils, on ne refait pas les mêmes allers-retours.

## Fichiers
- `methode/conception_boitier.md`, la méthode en étapes, chacune avec ce qu'on décide, comment on le vérifie, ce que ça coûte :
  1. **références** : photos du vrai panneau, relevé de cotes, normes (largeurs de panneau, hauteurs, entraxes des attaches,
     inscriptions) ; aucun nom d'avionneur ni de modèle d'avion dans ce qui est public ;
  2. **taille et architecture** : façade (plaque + embase), boîte à lumière, carte, caisson, supports ; empilage en y ;
  3. **matériaux et lieu de fabrication** : visible ou caché, l'imprimeur FDM / JLC / atelier laser, coût par boîtier (« l'argent là où
     ça se voit ») ;
  4. **fixations** : standard du projet (attaches, petites vis), places, colonnes d'inserts (≥ 2 mm autour, jamais hors du flanc),
     marges aux lettres (≥ 0,8) ;
  5. **lumière** : chambres, jours dans l'embase, LED derrière chaque inscription ;
  6. **supports** et pose (clipsés, 15°), lest ;
  7. **contrôles automatiques** : trous bouchés, collisions, parois minimales ;
  8. **rendu** : asset → plans fixes → aperçus → rendus finaux sur PC-B ;
  9. **revue de faisabilité et chiffrage**.
- `material_library/conception/` : `panneau.py` (cotes et normes de panneau), `caisson.py`, `supports.py` (déplacé de MFS),
  `controles.py` (contrôle des trous et des collisions, repris de la maquette, générique sur des préfixes de noms).
- Retour d'expérience F-COM2 (ce qui a coûté des allers-retours : vis Dzus puis standard, colonnes qui ressortaient, jours
  oubliés, arêtes vives) écrit comme liste de pièges.

## Fini quand
La méthode est relue par Lou, et un panneau d'essai (gabarit simple) passe par les étapes 1 à 8 avec les outils, sans code
propre au F-COM2.

## Watch-outs
- Ne pas figer une norme non vérifiée : les cotes relevées sur photo restent marquées « estimées ».
- Les contrôles actuels sont écrits pour les noms `GF_*` : les rendre génériques sans casser MFS.

## Journal
- 2026-10-27 : `methode/conception_boitier.md` (9 étapes : décision, vérification, coût ; 27 pièges vécus) ;
  `material_library/conception/` : `panneau.py` (normes de pupitre déduites des deux panneaux relevés, toutes **estimées** ;
  vérification du dessin à plat ; chambres et jours de lumière), `caisson.py`, `supports.py` (copie de MFS + clipsage et
  `construire`), `controles.py` (trous, collisions, parois, volumes : sur des préfixes de noms), `chiffrage.py` (en plus du plan :
  les prix relevés et le tableau « l'argent là où ça se voit » servent aux étapes 3 et 9). MFS n'est pas touché : sa maquette
  garde ses contrôles `GF_*` et son `supports.py` jusqu'au chunk-09.
- 2026-10-27 : essai `methode/essai/` sur un panneau gabarit de 5 crans : 0 erreur de dessin, 0 trou bouché, 0 collision
  (37 pièces), 0 paroi mince ; le contrôle de lumière trouve les jours oubliés (2 chambres bouchées sans jours, 0 avec). Corrigé
  en chemin : faces concaves des booléens triangulées en éventail par `BVHTree.FromPolygons` (fausses collisions) → triangles de
  Blender. Aperçus : `methode/essai/apercu_*.jpg`.
- 2026-10-27 : Lou valide la méthode et l'essai → `done`.
