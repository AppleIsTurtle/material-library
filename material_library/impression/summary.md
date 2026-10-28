# summary — material_library/impression/

Impressions (chunk-04) : encre réelle, décalques, grandes surfaces imprimées, et simulations d'impression FDM (tranchage, lettres)
dont les .npz sont lus par `matieres/procedes.py`. Méthode : [methode/procedes.md](../../methode/procedes.md).

| Fichier | Rôle | Dépendances |
|---|---|---|
| __init__.py | Marque le sous-paquet | — |
| encre.py | Masque net → encre imprimée (étalement, bord irrégulier, épaisseur qui varie, micro-manques) | Pillow, numpy |
| texte.py | Marquage d'un composant (lignes de texte, police « points » 5 × 7 des jets d'encre) en image d'encre, 200 px/mm | encre.py |
| calques.py | Grande surface (façade, masque) : textes, traits, anneaux, aplats en mm → image d'encre (L ou RGB) | encre.py |
| decalques.py | Dans Blender : décalque d'encre posé sur une pièce (plan à 4 µm, encre mate + transparent) ; lance texte.py avec le Python de KiCad ou le Python système | bpy, matieres.couleurs, texte.py |
| tranchage.py | Simulation du tranchage FDM (U1 de l'imprimeur FDM, buse 0,4 / 0,2) **calée sur OrcaSlicer** (profil U1) : n'importe quelle orientation (`plateau`), réglages (`reglages()` : parois, motif et angle du dessus, couture…) → **trajets** au format de `outils/fdm/gcode.py` (parois, dessus, face plateau, plein, ponts, coutures) ; règles : [methode/fdm_trajets.md](../../methode/fdm_trajets.md) | Python système : numpy, shapely |
| cartes.py | Cartes de rendu des cordons (Python système, lancé par `procedes.trajets`) : hauteur (dessus, face plateau, dessous, coutures) et direction du fil, texel par texel, depuis la cuisson P / N et les trajets | numpy, scipy, Pillow |
| lettres.py | Premier calque de lettres imprimées dans la masse (cordon, traits fins, bord qui ondule, mélange), ou masque exact (gravure laser) → .npz pour `procedes.lettres_imprimees` / `lettres_gravees` | Python système : numpy, scipy, shapely, Pillow |

## Historique
- 2026-10-27 : création (chunk-01).
- 2026-10-27 : repris de MFS (encre.py, impression_texte.py → texte.py, impression_calques.py → calques.py, impression.py →
  decalques.py, simulation_impression_facade.py → tranchage.py, simulation_lettres_facade.py → lettres.py), STL en arguments (chunk-04).
- 2026-10-28 : tranchage.py réécrit, calé sur OrcaSlicer (feature fdm-trajets, chunk-02) ; `procedes.appliquer_traces` lit encore l'ancien format jusqu'au chunk-03.
- 2026-10-28 : cartes.py ; tranchage.py écrit aussi origine, tops et hauteurs des couches (chunk-03).
