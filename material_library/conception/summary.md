# summary — material_library/conception/

Outils de la méthode de conception d'un boîtier à façade ([methode/conception_boitier.md](../../methode/conception_boitier.md)),
repris du F-COM2 (MFS) et rendus génériques. Repère : x à droite, y vers l'arrière (0 = face avant), z en haut, mm.

| Fichier | Rôle | Dépend de | Étapes de la méthode |
|---|---|---|---|
| __init__.py | marque le sous-paquet | — | — |
| panneau.py | normes de pupitre (crans de 3/8 in, largeur 5,75 in : **estimées**), panneaux relevés (statut « fiche »), règles de dessin (marges, cloisons, capitales), empilage type ; `Panneau` (dessin à plat), `verifier()` (contrôle du dessin avant la 3D), `chambres()` et `jours_embase()` (lumière), `taille(crans)` | Python seul | 1, 2, 4, 5 |
| caisson.py | caisson creux au contour de la façade : `rayon_colonne()` (colonne d'insert bornée, ≥ 2 mm autour de l'insert), `construire()` (coque, colonnes et logements des inserts M4, inserts M3 au dos, rainures du clipsage), table des inserts posés par JLC | `material_library.aretes`, `supports` | 2, 4, 6 |
| supports.py | supports de bureau clipsés : copie de `MFS/boitier/scripts/supports.py` (champ, contour, maillage régulier, repère incliné) + `SUPPORT_PANNEAU`, `POSE`, `CLIPSAGE`, `queue_aronde()`, `profil_rainure()`, `construire()` (supports + patins + pose de la racine) | numpy, bpy / bmesh pour `construire` | 6 |
| controles.py | contrôles 3D génériques sur des noms / préfixes : `trous()`, `collisions()`, `parois()`, `volume_cm3()` (triangles de Blender : pas de fausse collision sur les faces concaves des booléens) | bpy | 5, 7, 9 |
| chiffrage.py | prix relevés en 2026-10 (SLA JLC, PLA de l'imprimeur FDM, inserts, port), `sla_jlc()`, `pla_imprimeur()`, `inserts_jlc()`, `port_jlc()`, `tableau()` « l'argent là où ça se voit » | Python seul | 3, 9 |

## Historique
- 2026-10-27 : création du sous-paquet (chunk-01).
- 2026-10-27 : chunk-07 — panneau.py, caisson.py, supports.py (repris de MFS ; MFS garde le sien jusqu'au chunk-09), controles.py
  (repris de `controle_trous` / `controle_collisions` de `maquette_grand_format.py`, génériques ; contrôle des parois neuf),
  chiffrage.py ; essayés sur le panneau gabarit (`methode/essai/`).
