"""material-library : bibliothèque commune de Lou (matières, procédés, arêtes, visserie, imperfections, conception).
Code exécuté dans Blender ; les sous-modules importent bpy / bmesh eux-mêmes. Plan : docs/plans/MASTER.md."""
import os

__version__ = "0.3.1"                       # 0.2 : FDM d'après les vrais trajets (fdm-trajets) ; .1 : trancher_objet ; .2 : EXR 16 bits ZIP (OpenImageIO), cartes ≥ 256 ; .3 : PLA à teinte uniforme, grains de plateau, grain au seul contact ; .4 : bibliothèque de matières dans le dépôt, Blender 4.4 et 5.1 ; 0.3 : renommé material-library (paquet material_library) ; .1 : variables d'environnement, AGENTS.md, skill
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# données lourdes hors git : cartes d'images, planches, archives (la bibliothèque de matières est dans bibliotheque/) ; ailleurs que
# sur le PC de Lou : variable d'environnement MATERIAL_LIBRARY_DONNEES
DONNEES = os.environ.get("MATERIAL_LIBRARY_DONNEES") or r"G:\Blender\Bibliotheque"
# Python système (numpy, scipy, shapely, Pillow) pour les calculs lancés depuis Blender (cartes FDM, tranchage) : celui de Blender
# n'a ni scipy ni shapely ; MATERIAL_LIBRARY_PYTHON pour en imposer un
import shutil as _shutil
PYTHON_SYSTEME = (os.environ.get("MATERIAL_LIBRARY_PYTHON") or _shutil.which("python") or
                  os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WindowsApps", "python.exe"))
