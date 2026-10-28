r"""Essai du chunk-03 : chaque fiche du catalogue se construit par son nom dans une scène vide, et les conversions de couleurs
tiennent l'aller-retour.
    blender -b --factory-startup --python outils\essais\essai_matieres.py"""
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from material_library.matieres import catalogue as CAT      # noqa: E402
from material_library.matieres import couleurs as CO        # noqa: E402

try:
    for h in ("#000000", "#5c6169", "#3b3f45", "#ffffff", "#c9c7c1"):
        assert CO.hexa(CO.srgb(h)) == h, h
    assert CO.ecart("#5C6169", "#5f646c") == 3
    print("OK couleurs (srgb ↔ hexa, ecart)")
    for nom in CAT.CATALOGUE:
        m = CAT.construire(nom)
        assert m.name == CAT.fiche(nom)["matiere"] and m["material_library"] == nom, nom
        if CAT.fiche(nom).get("bevel"):
            assert any(n.type == "BEVEL" for n in m.node_tree.nodes), f"{nom} sans Bevel"
        print("OK", nom, "→", m.name)
    m2 = CAT.construire("pla_noir", base="#202022")       # reconstruite : même matière, pas de doublon
    assert len([m for m in __import__("bpy").data.materials if m.name.startswith("SP_PLA_noir")]) == 1
    print("ESSAI MATIERES OK")
except Exception:
    traceback.print_exc(); sys.exit(1)
