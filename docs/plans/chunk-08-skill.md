# Chunk 08 — skill Claude global « material-library »

**Statut : `done`** (2026-10-28) · **Plan : [MASTER.md](MASTER.md)** · dépend du chunk-07

## Fait (2026-10-28)
- `skill/SKILL.md`, installé par jonction dans `~/.claude/skills/material-library/` (voir [skill/summary.md](../../skill/summary.md)) ;
  il renvoie à [AGENTS.md](../../AGENTS.md) (points d'entrée, exemple testé sous Blender 5.1.2, pièges, chemins de la machine).
- Version 0.3.1 : `DONNEES` et `PYTHON_SYSTEME` réglables par `MATERIAL_LIBRARY_DONNEES` / `MATERIAL_LIBRARY_PYTHON` (défauts
  inchangés : mêmes valeurs qu'en 0.3.0, essais matières / arêtes / procédés OK, non-régression de la scène d'exemple : 0 écart).
- Test : un agent Sonnet neuf, dans un dossier vide, avec le seul skill, a fait une cale MJF percée avec sa vis ISO 4762 et son
  aperçu (0 arête vive, 0 collision). Ses remarques ont été reprises dans le skill et AGENTS.md (liens absolus, choix
  `PR.<procédé>` / `CAT.construire`, dos d'un trou à congé, faux positifs des contrôles sur la visserie, recette d'aperçu).
- Reste à proposer à Lou : un paramètre `coupe(..., conge_dos=)` dans `aretes.py` (aujourd'hui : outil retourné à la main) ; le
  garde-fou mémoire `blender_garde.ps1` vit encore dans MFS.

## But
Dans n'importe quel projet, Claude sait concevoir et rendre une pièce selon la méthode de Lou : il charge le skill, importe la
bibliothèque et suit les étapes, en posant les bonnes questions au bon moment.

## Fichiers
- `skill/SKILL.md` (copié ou lié dans `~/.claude/skills/material-library/`) : quand l'utiliser, comment importer le dépôt, les
  étapes (méthode de conception, matières, procédés, vis, arêtes, imperfections, aperçus avant rendus finaux, ferme PC-B),
  les règles de Lou (vouvoiement, pas d'arête vive, matières mesurées, aperçus d'abord, chiffrage) et les erreurs connues.
- `skill/summary.md`.

## Fini quand
Une session neuve, dans un autre dossier que MFS, conçoit une petite pièce d'essai en suivant le skill sans aide.

## Watch-outs
- Le skill renvoie aux documents de `methode/` au lieu de les recopier (une seule vérité).
- Penser à la mise à jour : le skill indique la version du dépôt qu'il attend.
