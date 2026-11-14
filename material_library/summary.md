# summary — material_library/

Paquet Python importé par les scripts Blender des projets (`import material_library as SP`).

| Fichier / dossier | Rôle | Chunk |
|---|---|---|
| __init__.py | Version (`__version__`), racine du dépôt, dossier des données lourdes (`DONNEES`, variable `MATERIAL_LIBRARY_DONNEES`), Python système des calculs lancés depuis Blender (`PYTHON_SYSTEME`, variable `MATERIAL_LIBRARY_PYTHON`, fdm-trajets) | 01 |
| aretes.py | (à venir) biseau appliqué, nœud Bevel, profils arrondis, découpes à congé, lissage | 02 |
| matieres/ | (à venir) catalogue des matières, couleurs compensées, procédés de fabrication | 03, 04 |
| visserie/ | (à venir) normes DIN / ISO, fixations, filets, shading des vis | 05 |
| imperfections/ | (à venir) imperfections PBR, UV dépliés en mm | 05 |
| impression/ | (à venir) encre, décalques, calques imprimés | 04 |
| rendu.py | **Rendu produit, méthode complète** : `studio()` (scène de référence en lecture, Cycles GPU), `piece_fdm()` (soudure STL, normales pondérées, matière FDM, vrais trajets, Bevel PLA), `piece()` (autres procédés), `visserie()` (Bevel des têtes et imperfections, comme `V3_vis_grise` des rendus F-COM), `res_premier_lit` (premier lit à part, plan, ombré à plat, cartes plus fines), `camera()` / `viser()` / `rendre()` ; variable `MATERIAL_LIBRARY_STUDIO` | — |
| conception/ | (à venir) cotes de panneau, caisson, supports, contrôles (trous, collisions) | 07 |

## Historique
- 2026-10-27 : création (chunk-01), sous-paquets vides.
- 2026-10-28 : `PYTHON_SYSTEME` (feature fdm-trajets, chunk-03).
- 2026-10-28 : version 0.2.0 (fdm-trajets, chunk-05).
- 2026-10-28 : version 0.2.1 (trancher_objet, cartes EXR 16 bits).
- 2026-10-28 : version 0.2.2 (cartes EXR vraiment en 16 bits compressé par OpenImageIO : 12,6 Mo → 0,1–0,3 Mo pour le bouton TFR ; résolution minimale 256 pour les petites pièces).
- 2026-10-28 : version 0.2.3 (PLA FDM à teinte uniforme ; grains de plateau « fin » / « granuleux »).
- 2026-10-28 : version 0.3.0 : le dépôt studio-produit devient material-library (paquet `material_library`, add-on `material_library_fdm`) ; les noms de données `SP_*` et la propriété `sp_fdm` restent (compatibilité des scènes).
- 2026-10-28 : version 0.2.4 (bibliothèque de matières suivie par git dans `bibliotheque/`, une par version de Blender ; `aretes.retrancher` passe en booléen Exact sous Blender 4.4, qui n'a pas Manifold).
- 2026-10-28 : version 0.3.1 : `DONNEES` et `PYTHON_SYSTEME` se règlent par variables d'environnement (défauts inchangés) ; `AGENTS.md` et le skill (chunk-08) ; publication : `chiffrage.pla_imprimeur` (l'imprimeur FDM n'est plus nommé).
- 2026-11-13 : version 0.3.4 : `rendu.py` (Lou : un script de rendu ne doit plus pouvoir sauter une étape de la méthode — studio maison trop sombre, PLA sans trajets, arêtes vives) ; grain de plateau « lisse ».
- 2026-11-13 : version 0.3.5 : cordons FDM procéduraux (feature fdm-trajets, chunk-07).
- 2026-11-14 : version 0.3.6 : couches du plateau lisse (fdm-trajets, chunk-08) ; `noeuds.bruit_multi` ; `rendu.piece_fdm(poussiere=)` ; `imperfections.appliquer(seulement="poussiere")`.
- 2026-11-14 : version 0.3.7 : rugosité de base des pièces FDM par `noeuds.bruit_zones` (validée par Lou sur la façade du F-COM3 noir).
