"""Add-on « Material library — Impression FDM » : panneau de réglages d'impression d'une pièce et bouton « Recalculer les
trajets » (barre latérale de la vue 3D, onglet « Material library »). Toute la logique est dans le dépôt material-library
(material_library/matieres/reglages_fdm.py) : cet add-on ne fait que l'enregistrer.
Installation : Préférences > Fichiers > Script Directories : ajouter D:\\Claude\\material-library\\blender\\scripts, redémarrer
Blender, puis Préférences > Add-ons : activer « Material library — Impression FDM »."""
import os
import sys

bl_info = {"name": "Material library — Impression FDM", "author": "Lou (material-library)", "version": (0, 3, 0), "blender": (5, 1, 0),
           "location": "Vue 3D > barre latérale > Material library", "category": "Material",
           "description": "Réglages d'impression FDM d'une pièce (buse, parois, dessus, couture, plateau) et recalcul des trajets"}

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if RACINE not in sys.path: sys.path.insert(0, RACINE)


def register():
    from material_library.matieres import reglages_fdm
    reglages_fdm.enregistrer()


def unregister():
    from material_library.matieres import reglages_fdm
    reglages_fdm.desenregistrer()
