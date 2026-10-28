# Chunk 05 — visserie standard

**Statut : `done`** (2026-10-27, planche validée par Lou) · **Plan : [MASTER.md](MASTER.md)** · dépend des chunks 02, 03

## But
Toute vis, écrou, insert ou rondelle du commerce se crée par sa désignation normalisée (« M4 × 8 DIN 84 inox A2 ») avec sa vraie
géométrie et son vrai shading ; les fixations de façade suivent la règle du projet.

## Fichiers
- `material_library/visserie/normes.py` : tables DIN / ISO (têtes cylindriques fendues DIN 84, bombées ISO 7045, fraisées ISO 7046 /
  DIN 965, BTR ISO 4762, écrous ISO 4032, rondelles DIN 125, inserts laiton) : diamètres et hauteurs de tête, empreintes, pas.
- `material_library/visserie/fixations.py` : déplacé de `boitier/scripts/fixations.py` (attaches en collerette, petites vis à fleur,
  fraisages et encoches à congé) et rendu paramétrable par la norme.
- `material_library/visserie/filets.py` : filets, écrous, taraudages (repris de `visserie_photoreal.py` et de `tige()` / `ecrou()`).
- `material_library/visserie/shading.py` : inox naturel, acier oxydé noir usé (d'après photo), têtes peintes ; imperfections sur
  UV dépliés en mm (`uv_plan_mm`), nœud Bevel de la tête.
- `material_library/imperfections/` : `imperfections.py` (cartes de `G:\Blender\MFS\imperfections\`, à déplacer vers les données
  communes) et `uv_mm.py`.
- `methode/fixations_facade.md` : déplacé de MFS (règle des fixations standard), complété par « comment choisir une vis »
  (disponibilité chez plusieurs vendeurs, prix relevés).

## Fini quand
Une planche de visserie (chaque norme en M3 / M4, inox et oxydé) est rendue en gros plan et validée, et la maquette du F-COM2 peut
remplacer ses vis par ces fonctions sans changer ses dumps au-delà des noms de matières (vérifié au chunk-09).

## Watch-outs
- Garder les noms d'objets que les contrôles de collision attendent (`GF_VIS_*`, `GF_ECROU_*`…) : le préfixe est un paramètre.
- Une tête de M2,5 sur un trou de M3 (transpondeur) est encore « à trancher » : ne pas figer.

## Réalisé (2026-10-27)
- `visserie/normes.py` (tables et sources), `fixations.py` (repris de MFS, paramétré : `attache_cotes()`, `fleur_cotes()`, `tete()`
  pour DIN 84 / ISO 7045 / ISO 7046 / ISO 4762), `filets.py` (filet ISO, tige, écrou, rondelle, insert ; `sortie` = filet qui
  s'efface sur la pointe, 0 par défaut comme MFS), `shading.py`, et **`pieces.py`** (ajouté : désignation → objets habillés, noms
  par `prefixe`) ; `imperfections/imperfections.py` et `uv_mm.py` ; `methode/fixations_facade.md` (+ choix d'une vis, prix relevés).
- Non-régression : collerette, tête et fente DIN 84, trou en U (via `aretes.coupe` / `encoche_u`), vis à fleur et empreinte,
  fraisage, tige M3 / M4, écrou M3 = maillages de MFS à l'identique (15 pièces, écart 0).
- Planche : `outils/planches/planche_visserie.py` → `G:\Blender\Bibliotheque\planches\visserie\planche_visserie_quick.png`
  (aperçu 48 échantillons), validée par Lou le 2026-10-27.
- Écart voulu avec MFS (à revoir à l'œil au chunk-09) : l'usure claire de l'acier oxydé suit un masque d'arête par nœud Bevel au
  lieu de la Pointiness (qui tachait toute la surface d'un écrou peu dense).
- Reste « à trancher » : tête de M2,5 sur un trou de M3 (transpondeur) ; non figé.
