---
name: material-library
description: Use when designing, modeling, shading or rendering a manufactured part or enclosure in Blender in any of Lou's projects — 3D-printed (FDM, SLA, MJF), laser-cut acrylic, machined metal, screws and inserts, bevels / no sharp edges, physical materials, imperfections, product renders (pièce, boîtier, façade, matière, vis, arêtes, impression 3D, rendu produit, bibliothèque de matières, material-library).
---

# material-library — concevoir et rendre une pièce selon la méthode de Lou

Bibliothèque commune de Lou (dépôt `D:\Claude\material-library`, GitHub AppleIsTurtle/material-library, licence MIT) : matières
physiques mesurées, looks par procédé de fabrication, arêtes sans angle vif, visserie normalisée, imperfections, méthode de
conception d'un boîtier. Du Python exécuté **dans Blender 5.1**, importé par les scripts du projet.

**Version attendue : 0.3.x.** Si `SP.__version__` a une autre majeure.mineure, lire le haut de `material_library/__init__.py` et
`git log` du dépôt pour voir ce qui a changé, et le dire à Lou avant de continuer.

## Quand l'utiliser
Dès qu'un projet crée ou rend dans Blender une pièce qui sera (ou pourrait être) fabriquée : boîtier, façade, bouton, support,
pièce imprimée, plaque découpée, vis. Pas pour : PCB (KiCad), site web, film, Houdini.

## D'abord
1. Lire **`D:\Claude\material-library\AGENTS.md`** : points d'entrée de l'API, exemple minimal testé, pièges (scène en mm,
   Blender 4.4 / 5.1), chemins de la machine. C'est la seule vérité sur l'usage : ne pas recopier l'API dans le projet.
2. Importer, et vérifier la version :
   ```python
   import os, sys
   sys.path.insert(0, os.environ.get("MATERIAL_LIBRARY", r"D:\Claude\material-library"))
   import material_library as SP
   assert SP.__version__.startswith("0.3."), SP.__version__
   ```
3. Noter la version utilisée dans le `VERSIONS.md` du projet (s'il en a un).

## Les étapes
Les documents de `D:\Claude\material-library\methode\` font foi : les lire à l'étape, sans les recopier.
1. **Quelle fabrication ?** Procédé, atelier, matière, orientation d'impression : `methode\procedes.md` (« Quel procédé pour
   quelle pièce », limites de conception, coûts datés). Demander à Lou ce qu'il ne dit pas : qui fabrique, quelle teinte il voit,
   quel budget.
2. **Un boîtier à façade** : suivre les 9 étapes de `methode\conception_boitier.md` (références et normes, taille, matériaux et
   chiffrage, fixations, lumière, supports, contrôles, rendu, revue de faisabilité). Chaque étape se termine par **une décision de
   Lou sur une image ou un tableau chiffré**. Lire aussi ses « Pièges vécus ».
3. **Modéliser par passes validées** : volumes simples → formes secondaires → détails → matières, aperçu rapide à chaque passe.
   Arêtes : `methode\aretes.md` (géométrie ou nœud Bevel, rayons `AR.RAYONS`, lissage après booléen, trous à congé) ; contrôle
   `AR.aretes_vives(ob)` = 0 sur chaque pièce dessinée.
4. **Fixations** : visserie standard du commerce seulement, `methode\fixations_facade.md` ; poser les vis par leur désignation
   (`visserie.pieces`), le passage percé dans la pièce (exemple d'AGENTS.md).
5. **Matières** : procédé connu → `PR.fdm / sla / mjf / acrylique_laser / metal(fiche, …)`, qui partent de la fiche du catalogue
   et ajoutent ce que la fabrication laisse (couches, plateau, ponçage, poudre) ; matière seule (verre, caoutchouc, sol d'un
   studio) → `CAT.construire(fiche)`. `methode\matieres.md` pour les règles, la base compensée à la pipette dans le studio, et
   **comment ajouter une matière** : une matière qui manque s'ajoute au catalogue du dépôt (fiche avec source, mesure, décision
   de Lou), jamais en copie dans le projet.
6. **Réglages du procédé** : buse, axe des couches et face sur le plateau en FDM (un paramètre de la pièce, jamais une
   constante), finition en SLA ; FDM au plus près : trajets réels, `methode\fdm_trajets.md`.
7. **Imperfections** discrètes (`imperfections.appliquer`), UV en mm pour la visserie.
8. **Contrôles** : `conception.controles` (trous, collisions, parois) ; **regarder soi-même** chaque aperçu (et le maillage)
   et corriger avant de le montrer à Lou.
9. **Rendus** : aperçus rapides d'abord (recette à la fin de l'exemple d'AGENTS.md), rendu final seulement après accord de Lou ;
   rendus lourds ou animations : skill `rendu-distant` (ferme PC-B).

## Règles de Lou (dans tout ce qui sort)
- Le **vouvoiement**, en français.
- Aucun nom d'avionneur ni de modèle d'avion dans ce qui est public (site, rendus, textes, dépôt public).
- **Pas d'arête vive** : toujours un léger chanfrein ou arrondi (sauf frontière entre deux matières).
- Matières d'après la **construction réelle** du matériau et des **valeurs mesurées** ; la teinte vue par Lou prime sur les
  photos ; teinte et rugosité uniformes, le grain est en relief seul.
- Modéliser **comme c'est fabriqué** (photos du vrai composant d'abord) ; visserie standard du commerce.
- **Chaque choix chiffré** (coût TTC, port) : l'argent là où ça se voit, rien sur le caché.
- **Proposer avant de coder** ; `summary.md` à jour dans chaque dossier du projet ; jamais écraser un `.blend` retouché par Lou
  sans vérifier (archiver une copie d'abord).
- Blender lourd par le garde-fou mémoire (`D:\Claude\MFS\outils\blender_garde.ps1`, voir AGENTS.md).

## Erreurs connues
Voir « Pièges » dans AGENTS.md (unités, cube de la scène d'usine, 4.4 / 5.1, Python système pour le FDM, cartes
d'imperfections hors git) et « Pièges vécus » dans conception_boitier.md (cotes non vérifiées, parois, lettres trop petites…).
Un bug de la bibliothèque se corrige **dans le dépôt** (règles : `CLAUDE.md` du dépôt, non-régression des projets qui l'utilisent),
pas par un contournement dans le projet ; le dire à Lou s'il touche un rendu déjà validé.
