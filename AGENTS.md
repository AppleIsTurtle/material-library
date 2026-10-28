# AGENTS.md — material-library

Guide pour les agents d'IA (Claude Code, Codex, Cursor…). **Travailler SUR le dépôt** (corriger, ajouter une matière, une vis,
une règle) : lire [CLAUDE.md](CLAUDE.md), puis le plan [docs/plans/MASTER.md](docs/plans/MASTER.md). Ce fichier-ci sert à
**utiliser** la bibliothèque depuis un autre projet. Avec Claude Code, le skill global « material-library » (source :
[skill/SKILL.md](skill/SKILL.md)) déroule la méthode et renvoie ici.

## Utiliser depuis un autre projet

Code Python exécuté **dans Blender 5.1** (bpy, bmesh) ; Blender 4.4 marche pour les matières, pas pour le panneau « Impression
FDM ». On l'importe depuis le script Blender du projet, on ne recopie rien dans le projet (une fonction = une vérité : s'il manque
une matière, une vis ou une règle, elle s'ajoute ici).

```python
import os, sys
sys.path.insert(0, os.environ.get("MATERIAL_LIBRARY", r"D:\Claude\material-library"))
import material_library as SP
assert SP.__version__.startswith("0.3."), SP.__version__     # version attendue par le projet, notée dans son VERSIONS.md
```

### Points d'entrée

| Module | Pour quoi | Fonctions |
|---|---|---|
| `matieres.catalogue` (`CAT`) | les matières physiques, une fiche par matière (teinte, rugosité, grain, rayon de Bevel, source, décision) | `CAT.noms(famille=None)`, `CAT.fiche(nom)`, `CAT.construire(nom, **changes)` → `bpy.types.Material` (nom Blender `SP_…`, relançable sans doublon) |
| `matieres.procedes` (`PR`) | le look de la vraie fabrication par-dessus la matière | `PR.poser(ob, m)` ; `PR.fdm("pla_noir", buse=0.4, axe="Z", plateau="-Z")`, `PR.sla("sla_jlc_black", "poncee_huilee")`, `PR.mjf("nylon_pa12_noir")`, `PR.acrylique_laser("peinture_fs36118", masque=None)`, `PR.metal("alu_anodise_gris_fonce")` |
| `matieres.reglages_fdm` | vrais trajets de la buse sur une pièce FDM (Python système requis) | `imprimer(ob, matiere="pla_noir", buse=0.4, plateau="-Z")` |
| `matieres.couleurs` | conversions, pipette, base compensée pour un studio | `srgb(hexa)`, `hexa(lin)`, `ecart(h1, h2)`, `compenser(base, cible, rendre_et_mesurer)` |
| `aretes` (`AR`) | aucune arête vive : géométrie et rendu | `AR.plaque(w, h, r, y0, y1, (av, ar))` → bmesh, `AR.coupe(...)`, `AR.retrancher(cible, outils)`, `AR.lisser(ob)`, `AR.adoucir(ob, largeur)`, `AR.bevel_rendu(m, rayon)`, `AR.aretes_douces(mats)`, `AR.aretes_vives(ob)` (contrôle), `AR.RAYONS` |
| `visserie.pieces` (`VP`) | vis, écrous, rondelles, inserts du commerce par leur désignation | `VP.vis("M3 x 8 ISO 7045 inox A2", x, z, y_appui)`, `VP.ecrou("M3 ISO 4032 inox", …)`, `VP.rondelle("M3 DIN 125", …)`, `VP.insert("M3 INSERT laiton", …)`, `VP.piece(designation, …)` ; normes : vis à tête cylindrique fendue DIN 84 / ISO 1207, bombée cruciforme ISO 7045, fraisée cruciforme ISO 7046 / DIN 965, cylindrique six pans creux ISO 4762 / DIN 912 ; écrou ISO 4032 / DIN 934 ; rondelle DIN 125 ; matières : inox (A2, A4), oxyde (noir), laiton |
| `imperfections` | poussière, frottements, rayures (PBR) sans toucher aux valeurs physiques | `imperfections.imperfections.appliquer(objets, force=1.0)`, `imperfections.uv_mm.uv_plan_mm(ob)` (UV en mm) |
| `conception` | méthode de conception d'un boîtier à façade | `panneau` (Python seul : `taille`, `Panneau`, `verifier`), `caisson.construire`, `supports.construire`, `controles` (`trous`, `collisions`, `parois`, `volume_cm3`), `chiffrage` (`tableau`, prix datés) |
| `impression` | lettres imprimées ou gravées, encre, décalques, tranchage | voir [material_library/impression/summary.md](material_library/impression/summary.md) |

Matières du catalogue (0.3) : `peinture_fs36118`, `sla_jlc_black`, `sla_jlc_grey`, `resine_9600_blanche`, `pla_noir`, `pla_blanc`,
`pla_naturel`, `nylon_pa12_noir`, `nylon_pa12s_noir`, `sls_3201pa_f`, `inox_a2`, `acier_oxyde_noir`, `laiton`,
`alu_anodise_gris_fonce`, `alu_brosse`, `acrylique_fume`, `bumpon_noir`, `pvc_noir` (liste à jour : `CAT.noms()`).

Repère des fonctions : **mm**, x à droite, z en haut, y en profondeur (0 = face avant, -y vers l'utilisateur ; la tête d'une vis
est du côté -y).

### Exemple minimal (testé sous Blender 5.1.2, version 0.3.1)

`piece.py` : une plaque de 40 × 25 × 4 en PLA noir, coins R 3, arêtes arrondies, percée d'un passage de vis M3 arrondi des
deux côtés, une vis M3 bombée posée dedans ; contrôles ; aperçu rapide sur demande.

```python
import os, sys
import bmesh, bpy
from mathutils import Vector

sys.path.insert(0, os.environ.get("MATERIAL_LIBRARY", r"D:\Claude\material-library"))
import material_library as SP
from material_library import aretes as AR
from material_library.conception import controles as CT
from material_library.matieres import catalogue as CAT, procedes as PR
from material_library.visserie import pieces as VP

assert SP.__version__.startswith("0.3."), SP.__version__
ICI = os.path.dirname(os.path.abspath(__file__))

bpy.ops.wm.read_factory_settings(use_empty=True)        # sans le cube, la caméra et la lampe par défaut
sc = bpy.context.scene                                   # scène en mm : 1 unité = 1 mm
sc.unit_settings.system = "METRIC"; sc.unit_settings.scale_length = 0.001; sc.unit_settings.length_unit = "MILLIMETERS"

# plaque 40 × 25, épaisse de 4 (y de 0 à 4, face avant vers -y), coins R3, arêtes avant / arrière arrondies 0,6
bm = AR.plaque(40, 25, 3.0, 0.0, 4.0, (0.6, 0.6), cz=12.5)
me = bpy.data.meshes.new("plaque"); bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new("plaque", me); sc.collection.objects.link(ob)
AR.lisser(ob)

# passage Ø 3,4 pour une M3 en (x 14, z 8), congé 0,4 : coupe() n'arrondit que la face y_face, le dos se fait avec l'outil retourné
avant = AR.coupe(AR.contour_cercle(1.7), -1.0, 5.0, conge=0.4, y_face=0.0, cx=14, cz=8)
dos = AR.coupe(AR.contour_cercle(1.7), -1.0, 5.0, conge=0.4, y_face=0.0, cx=14, cz=8)
for v in dos.verts: v.co.y = 4.0 - v.co.y               # miroir : face y = 0 → face y = 4
bmesh.ops.reverse_faces(dos, faces=dos.faces); bmesh.ops.recalc_face_normals(dos, faces=dos.faces)
AR.retrancher(ob, [avant, dos])

# matière : procédé connu → PR.fdm / PR.sla / PR.mjf / PR.acrylique_laser / PR.metal ; matière seule → CAT.construire
PR.poser(ob, PR.fdm("pla_noir", buse=0.4, axe="Z", plateau="-Z"))

# vis : tête du côté -y, posée sur le plan y_appui, tige vers +y (longueur sous tête, comme le commerce)
vis = VP.vis("M3 x 6 ISO 7045 inox A2", x=14, z=8, y_appui=0.0)

print("arêtes vives :", len(AR.aretes_vives(ob)))        # 0 attendu (pièce dessinée ; la visserie en compte, c'est normal)
mauvaises, voulues = CT.collisions(noms=[ob.name] + [o.name for o in vis],
                                   meme_piece=lambda a, b: a.startswith("SP_VIS") and b.startswith("SP_VIS"))
print("OK", SP.__version__, ob.name, ob.active_material.name, [o.name for o in vis])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ICI, "piece.blend"))

if "apercu" in sys.argv:                                 # aperçu rapide : sol (plan xy, z en haut), deux lampes, caméra 3/4
    sol = bpy.data.objects.new("sol", bpy.data.meshes.new("sol")); sc.collection.objects.link(sol)
    b = bmesh.new(); bmesh.ops.create_grid(b, x_segments=1, y_segments=1, size=300); b.to_mesh(sol.data); b.free()
    sol.data.materials.append(CAT.construire("sla_jlc_grey"))
    w = bpy.data.worlds.new("fond"); sc.world = w                     # Blender 5.1 : le monde neuf a déjà ses nœuds
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.6, 0.62, 0.66, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.6
    def viser(o, loc, cible=Vector((0, 2, 12))):
        sc.collection.objects.link(o); o.location = loc
        o.rotation_euler = (cible - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    for nom, loc, watts in (("cle", (-120, -150, 130), 40000), ("contre", (150, -60, 80), 15000)):   # en mm : ~200 mm de la pièce
        l = bpy.data.lights.new(nom, "AREA"); l.energy = watts; l.size = 120; viser(bpy.data.objects.new(nom, l), loc)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); cam.data.lens = 85; viser(cam, (45, -140, 60)); sc.camera = cam
    sc.render.engine = "CYCLES"; sc.cycles.samples = 64; sc.render.resolution_x, sc.render.resolution_y = 960, 640
    sc.render.filepath = os.path.join(ICI, "piece_apercu.png"); bpy.ops.render.render(write_still=True)
```

Lancer : `blender -b --factory-startup --python piece.py` (chez Lou : `F:\Blender\5.1\blender.exe`), avec `-- apercu` à la fin
pour l'image. Sortie attendue : `arêtes vives : 0`, `CONTROLE COLLISIONS : 0 collision(s) à corriger…` puis
`OK 0.3.1 plaque SP_PLA_noir_FDM… ['SP_VIS', 'SP_VIS_filet', 'SP_VIS_ame']`. Regarder l'aperçu soi-même avant de le montrer.

### Pièges

- **Unités** : toutes les matières et fonctions sont en **mm**. Une scène en mètres (défaut de Blender) rend le grain et les couches
  FDM 1 000 fois trop gros : `scale_length = 0.001`, longueurs en millimètres, 1 unité = 1 mm.
- **Scène d'usine** : `--factory-startup` garde le cube, la caméra et la lampe par défaut ; partir de
  `bpy.ops.wm.read_factory_settings(use_empty=True)`.
- **Versions de Blender** : Blender 4.4 n'ouvre pas les `.blend` de la 5.x ; la bibliothèque de matières existe pour les deux
  (`bibliotheque/blender_4.4/`, `bibliotheque/blender_5.1/`) ; les booléens passent en Exact sous 4.4 (pas de Manifold).
- **`construire` est relançable** : il reprend la matière du même nom au lieu d'en créer une copie ; pour une variante, passer
  `matiere="SP_mon_nom"` et le champ changé (`base="#…"`).
- **Matières liées** (Link d'une autre scène) : non modifiables, `aretes_douces` les saute.
- **Contrôles** : `AR.aretes_vives` vise les pièces dessinées ; sur une vis (filet, empreinte) il en trouve des centaines, c'est
  normal. `AR.coupe` n'arrondit que la face `y_face` : pour le dos d'un trou visible, l'outil retourné de l'exemple.
  `CT.collisions` renvoie `(collisions, contacts voulus)` et voit les trois objets d'une vis (`SP_VIS`, `_filet`, `_ame`) comme
  des pièces distinctes : lui passer `meme_piece` comme dans l'exemple.
- **Lampes en mm** : la puissance se compte en unités de la scène ; à ~200 mm d'une petite pièce, quelques dizaines de milliers
  de watts (valeurs de l'aperçu de l'exemple), avec un fond gris qui éclaire.
- **Trajets FDM, tranchage, lettres** : lancent le Python système (numpy, scipy, shapely, Pillow : `SP.PYTHON_SYSTEME`) ; celui de
  Blender n'a ni scipy ni shapely.
- **Mémoire** : un rendu Cycles lourd ou un booléen sur des copies presque confondues peut saturer le PC ; chez Lou, lancer
  Blender par le garde-fou `D:\Claude\MFS\outils\blender_garde.ps1 -ArgLine '…' -Log <fichier>`.

### Chemins de la machine et données hors git

| Quoi | Défaut (PC de Lou) | Ailleurs |
|---|---|---|
| le dépôt | `D:\Claude\material-library` | variable `MATERIAL_LIBRARY` lue par vos scripts (convention de l'exemple ci-dessus) |
| données lourdes (`SP.DONNEES`) : cartes d'imperfections, planches, caches FDM | `G:\Blender\Bibliotheque` | variable `MATERIAL_LIBRARY_DONNEES` |
| Python système (`SP.PYTHON_SYSTEME`) | `python` du PATH | variable `MATERIAL_LIBRARY_PYTHON` |
| Blender | `F:\Blender\5.1\blender.exe` (4.4 : `F:\Blender\blender.exe`) | celui de la machine |

**Cartes d'imperfections** (`<DONNEES>\imperfections\` : `fond`, `frottements`, `doigts`, `micro_rayures`, `rayures`,
`poussiere`, `salissure`, PNG 8 bits 2K, 22 Mo) : tirées de packs de textures du commerce (Megascans, ATOM…), elles ne sont
**pas** dans le dépôt, dont la licence MIT ne peut pas les couvrir. Sans elles, `imperfections.appliquer` garde ses bruits procéduraux seuls (même réglage, moins
de variété). Sur une autre machine : copier le dossier depuis le PC de Lou, ou y mettre ses propres cartes en niveaux de gris
sous les mêmes noms.
