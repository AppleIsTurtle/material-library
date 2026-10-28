# summary — methode/

Méthode écrite (arêtes, matières, procédés, fixations, conception d'un boîtier). Chaque chunk y ajoute son document.

| Fichier / dossier | Rôle | Dépend de |
|---|---|---|
| aretes.md | Règle « aucune arête vive » : géométrie ou nœud Bevel, rayons par matière, lissage après booléen, congés et encoches, exceptions, contrôle | material_library/aretes.py, outils/planches/planche_aretes.py |
| matieres.md | Catalogue des matières : règles de Lou, champs d'une fiche, ajouter une matière, bases compensées (studio et vue de mesure), bibliothèque dans Blender (déclaration, Append / Link, unités) | material_library/matieres/, outils/planches/planche_matieres.py |
| procedes.md | Quel procédé pour quelle pièce, limites de conception (FDM, SLA, MJF, acrylique), coûts relevés et datés, chaîne FDM (traces, lettres), encre | material_library/matieres/procedes.py, material_library/impression/ |
| conception_boitier.md | **méthode de conception d'un boîtier à façade** en 9 étapes (références et normes, taille et architecture, matériaux et chiffrage, fixations, lumière, supports, contrôles, rendu, revue de faisabilité) : ce qu'on décide, comment on le vérifie, ce que ça coûte ; liste des 27 pièges vécus sur le F-COM2 et le transpondeur | `material_library/conception/`, `material_library/aretes.py`, `fixations_facade.md` |
| fixations_facade.md | Règle des fixations de façade (attaches M4 DIN 84 en collerette, petites vis M3 ISO 7046 à fleur), rendu, « comment choisir une vis », prix relevés | material_library/visserie/, outils/planches/planche_visserie.py |
| fdm_trajets.md | Trajets réels d'une impression FDM (U1, PLA, profil par défaut d'OrcaSlicer) : réglages, règles mesurées dans le G-code (pas d'écrasement, parois, dessus, couture), ce que ça veut dire pour les rendus, limites | outils/fdm/ |
| essai/ | essai de la méthode sur un panneau gabarit (script, journal, chiffrage, aperçus) : [essai/summary.md](essai/summary.md) | `material_library/conception/` |

## Historique
- 2026-10-27 : création (vide).
- 2026-10-27 : aretes.md (chunk-02), matieres.md (chunk-03).
- 2026-10-27 : conception_boitier.md et essai/ (chunk-07).
- 2026-10-27 : fixations_facade.md déplacé de MFS (`docs/methodes/fixations_facade.md`, chunk-05) et complété (choix d'une vis, prix).
- 2026-10-27 : procedes.md (chunk-04).
- 2026-10-27 : matieres.md § Bibliothèque dans Blender (chunk-06).
- 2026-10-27 : fdm_trajets.md (feature fdm-trajets, chunk-01).
