# summary — material_library/imperfections/

Imperfections de surface (poussière, frottements, micro-rayures, traces de doigts) ajoutées aux matières, et UV dépliés en mm pour
les lire sans déformation. Cartes d'images (hors git) : `G:\Blender\Bibliotheque\imperfections\` (`material_library.DONNEES`),
copiées de `G:\Blender\MFS\imperfections\` le 2026-10-27 (celles de MFS restent en place et servent de secours).

| Fichier | Rôle | Dépendances |
|---|---|---|
| __init__.py | Marque le sous-paquet | — |
| imperfections.py | `appliquer(objets, force, sans)` : imperfections PBR ajoutées à chaque matière (projection en boîte, coordonnées objet en mm) ; `carte_uv()` : une carte lue sur UV en mm (utilisée par visserie/shading.py) ; `CARTES`, `TUILE` | bpy, `material_library.DONNEES`, `matieres.couleurs.srgb` |
| uv_mm.py | `uv_plan_mm(objet)` : UV à l'échelle réelle (mm), chaque face à plat sur son plan, faces coplanaires continues | mathutils |

## Historique
- 2026-10-27 : création (chunk-01).
- 2026-10-27 : chunk-05 — imperfections.py (repris de MFS `boitier/scripts/imperfections.py`, chemins des données communes,
  `carte_uv`), uv_mm.py (`uv_plan_mm` de `maquette_grand_format.py`).
