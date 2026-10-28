# summary — skill/

Source du skill Claude global « material-library » (chunk-08) : dans n'importe quel projet, Claude sait concevoir et rendre une
pièce selon la méthode de Lou en s'appuyant sur ce dépôt.

| Fichier | Rôle | Dépendances |
|---|---|---|
| SKILL.md | Le skill : quand l'utiliser, import et version attendue (0.3.x), étapes (renvoient à `methode/*.md`), règles de Lou, erreurs connues ; renvoie à `AGENTS.md` pour l'API, l'exemple et les pièges | `AGENTS.md`, `methode/` |

## Installation (PC de Lou)
Jonction (lien de dossier, sans droits d'administrateur) : `%USERPROFILE%\.claude\skills\material-library` → ce dossier, faite
le 2026-10-28 par
`New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\material-library" -Target "D:\Claude\material-library\skill"`.
Le skill suit donc le dépôt (un `git pull` le met à jour) ; ce `summary.md` est visible dans le dossier du skill, sans effet. Sur
une autre machine : la même commande avec le chemin du clone, ou copier `SKILL.md` dans `~/.claude/skills/material-library/`.

## Historique
- 2026-10-27 : création (vide).
- 2026-10-28 : SKILL.md (chunk-08), installé par jonction.
