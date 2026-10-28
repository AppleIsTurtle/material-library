# summary — material_library/matieres/

Matières physiques (chunk-03) et looks par procédé (chunk-04). Méthode : [methode/matieres.md](../../methode/matieres.md).

| Fichier | Rôle | Dépendances |
|---|---|---|
| __init__.py | Marque le sous-paquet | — |
| noeuds.py | Briques de nœuds : matière vidée (jamais une matière liée), bruit, plage, relief, ondulation (grain en vraie hauteur) | bpy |
| couleurs.py | srgb / hexa, écart par canal, pipette (médiane hors reflets et ombres), correction et boucle de compensation d'une base | numpy ; bpy ou Pillow |
| catalogue.py | Fiches des matières (cible, base compensée pour le studio du site, valeurs physiques, grain, Bevel, source, décision) et `construire(nom)` ; visserie → visserie/shading.py | noeuds, couleurs, aretes, visserie.shading |
| reglages_fdm.py | Réglages d'impression FDM sur l'objet (`ob.sp_fdm` : matière, buse, couche, parois, dessus, angle, couture, face sur le plateau, translucide, résolution), `imprimer()` / `recalculer()` (même chemin pour les scripts et le bouton), `trancher_objet()` (maillage → trajets, pour les maquettes), opérateur « Recalculer les trajets », panneau « Impression FDM » (vue 3D > Material library) ; fichiers dans `<.blend>_fdm\` ; objets liés refusés | procedes, catalogue, impression/tranchage.py (Python système) |
| procedes.py | Looks par procédé : fdm (couches, plateau texturé, buse 0,4 / 0,2), couches (matières existantes), **trajets** (vrais trajets de la buse simulés : cordons des dessus / face plateau / tranches, coutures, reflet le long du fil — feature fdm-trajets), lettres_imprimees / lettres_gravees (masques .npz), sla (finitions), mjf, acrylique_laser (jour / nuit), metal | catalogue, noeuds, aretes ; .npz de impression/ |

## Historique
- 2026-10-27 : création (chunk-01).
- 2026-10-27 : noeuds.py, couleurs.py, catalogue.py (chunk-03, repris de photoreal.py, maquette_grand_format.py, carte_pipette.py de MFS).
- 2026-10-27 : procedes.py (chunk-04, repris de photoreal.pla_fdm / couches_fdm et de la maquette du F-COM2).
- 2026-10-28 : reglages_fdm.trancher_objet ; cartes EXR en 16 bits (0.2.1, chunk-06 de fdm-trajets : MFS l'appelle).
- 2026-10-28 : grain du plateau limité par trajets() aux points au contact du plateau (« plateau_contact », Lou : un creux tourné vers le plateau ne le touche pas).
- 2026-10-28 : procedes.fdm à teinte uniforme (Lou : bruit de diffuse trop fort) ; procedes.GRAINS « fin » / « granuleux » (plaque granuleuse du F-COM1), paramètre `grain` de fdm() et plateau_texture(), réglage « Grain du plateau » du panneau (0.2.3).
- 2026-10-28 : procedes._image écrit l'EXR par OpenImageIO (16 bits, ZIP ; Image.save() l'écrivait en 32 bits non compressé) ; trajets : résolution minimale 256 (0.2.2).
- 2026-10-28 : appliquer_traces retiré (remplacé par trajets, fdm-trajets chunk-05).
- 2026-10-28 : reglages_fdm.py ; procedes.trajets : UV « UV_fdm » à part, cartes en EXR (dossier), modification sur place (copie=False) (fdm-trajets, chunk-04).
- 2026-10-28 : procedes.trajets / _cuire / _image, grain du plateau refait sans variation à grande échelle (fdm-trajets, chunk-03).
