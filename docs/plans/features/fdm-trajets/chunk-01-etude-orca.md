# Chunk 01 — étude des vrais trajets (OrcaSlicer, profil Snapmaker U1)

**Statut : `done`** (2026-10-27 : OrcaSlicer 2.4.2 portable installé avec l'accord de Lou, outils `outils/fdm/`, planche
`G:\Blender\Bibliotheque\fdm\orca\planche_orca.png` vue et validée par Lou le 2026-10-28, [methode/fdm_trajets.md](../../../../methode/fdm_trajets.md) ;
point ouvert : multi-matière par .3mf à parties) · **Plan : [plan.md](plan.md)**

## But
Savoir exactement ce que la U1 de l'imprimeur FDM fait avec une pièce, couche par couche, avant d'écrire notre simulation : ordre et
nombre des tours, largeurs réelles des cordons (contour extérieur, contours intérieurs, dessus — elles diffèrent), recouvrement,
couture, motif et angle du dessus, demi-tours, remplissage des petits espaces (« gap fill »), nombre de couches de dessus, première
couche. Le résultat est un document de compréhension et des images de trajets réels qui servent d'étalon aux chunks suivants.

## Étapes
1. **Références** : les 5 photos de Lou (2026-10-27) sont déjà dans `G:\Blender\Bibliotheque\fdm\references\` (`1.webp`,
   `2.webp`, `3.webp`, `4.png`, `5.webp`) ; écrire la fiche `references.md` : ce que montre chacune (1 : dessus en lignes
   + creusement + surplomb affaissé, PLA noir ; 2 : flancs à couches nettes, noir mat ; 3 : PLA gris satiné, couches qui
   brillent, trous ; 4 : premières couches vues de dessus, contours concentriques autour des trous, fil ; 5 : noir mat, couches
   fines en relief).
2. **Installer OrcaSlicer** : version stable officielle (GitHub `SoftFever/OrcaSlicer`, release Windows), après **accord de Lou**
   (nom du fichier, source, taille). Étalon choisi par Lou : **profil Snapmaker U1 d'OrcaSlicer, réglages par défaut**, PLA,
   buse 0,4 (0,2 en plus) ; s'il manque : profil Snapmaker Orca, sinon machine générique aux mêmes réglages — le dire à Lou.
   Noter le profil exact et sa version. Usage en ligne de commande (`--slice`,
   `--load-settings`) si possible, pour que les chunks suivants le relancent eux-mêmes.
3. **Pièces tranchées** : l'embase de la F-COM2 réplique (`D:\Claude\MFS\boitier\f-com\commun\stl_par_couleur\f-com2_facade_embase_v0\f-com2_facade_embase_v0__noir.stl`
   — orientation : voir « Orientation de l'embase » dans [plan.md](plan.md)) et le bouton TFR du F-COM1 (STL multi-matière dans
   `boitier/f-com/f-com1/stl/`, posé face sur le plateau). Buses 0,4 et 0,2 ;
   1 et 2 contours ; motifs du dessus proposés par Orca (au moins monotone, monotone ligne, concentrique) ; couture alignée /
   arrière / la plus proche.
4. **Lire le G-code** : `outils/fdm/gcode.py` (nouveau, Python système) : G-code → trajets par couche, typés d'après les
   commentaires d'Orca (`;TYPE:Outer wall`, `Inner wall`, `Top surface`, `Bridge`, `Gap infill`…), avec largeur (`;WIDTH:`) et
   hauteur (`;HEIGHT:`) ; tracé de chaque couche (une couleur par type) en PNG.
5. **Document** `methode/fdm_trajets.md` : ce qui se passe réellement, chiffré (largeurs, recouvrements, angles, couture, ordre,
   écarts entre buses), avec les images ; liste des règles que notre simulation doit reproduire, par ordre d'importance visuelle.

## Fichiers
- `outils/fdm/gcode.py`, `outils/fdm/summary.md` (nouveaux) ; `methode/fdm_trajets.md` (nouveau) ; `methode/summary.md`.
- Hors git : `G:\Blender\Bibliotheque\fdm\references\`, `G:\Blender\Bibliotheque\fdm\orca\<pièce>_<buse>_<réglage>\` (projet
  `.3mf`, G-code, PNG des couches).

## Fini quand
Lou a vu une planche des vrais trajets (embase + bouton TFR, buse 0,4 et 0,2, dessus et une couche courante) et
`methode/fdm_trajets.md` décrit ce qu'il faut simuler.

## Watch-outs
- Aucun téléchargement sans accord explicite ; installeur pris uniquement sur la page de release officielle.
- Les commentaires de type du G-code varient selon la version d'Orca : noter la version, écrire le lecteur pour elle.
- Ne pas modifier les STL de MFS : les lire seulement.
