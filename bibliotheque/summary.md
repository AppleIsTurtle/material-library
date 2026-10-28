# summary — bibliotheque/

La bibliothèque de matières **générée**, à déclarer dans Blender comme *Asset Library* : 22 matières, 7 pièces de visserie, aperçus et
catalogues. Suivie par git (exception à « données lourdes hors git », Lou, 2026-10-28) pour qu'un clone du dépôt suffise à l'installer.
Un dossier par version de Blender, car Blender 4.4 n'ouvre pas un `.blend` enregistré par la 5.x. Ne jamais retoucher à la main :
régénérer avec [blender/construire_bibliotheque.py](../blender/construire_bibliotheque.py), lancé par **chacun** des deux Blender.
Installation : [README.md](../README.md) ; détails : [methode/matieres.md](../methode/matieres.md) § Bibliothèque dans Blender.

| Fichier / dossier | Rôle | Dépendances |
|---|---|---|
| blender_4.4/bibliotheque_matieres.blend | La bibliothèque pour Blender 4.4 (booléen des vis en *Exact*, la 4.4 n'a pas *Manifold*) | construire_bibliotheque.py lancé par Blender 4.4 |
| blender_4.4/blender_assets.cats.txt | Catalogues de l'Asset Browser (uuid stables) | idem |
| blender_5.1/bibliotheque_matieres.blend | La bibliothèque pour Blender 5.1 | construire_bibliotheque.py lancé par Blender 5.1 |
| blender_5.1/blender_assets.cats.txt | Catalogues de l'Asset Browser (uuid stables) | idem |

## Historique
- 2026-10-28 : création ; les deux fichiers générés en qualité finale (version 0.2.4), déclarés dans les deux Blender de Lou ; l'ancien
  `G:\Blender\Bibliotheque\bibliotheque_matieres.blend` archivé dans `G:\Blender\Bibliotheque\_archives\`.
