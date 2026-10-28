r"""Essai du chunk-04 : chaque procédé habille une plaque dans une scène vide ; vrais trajets FDM (reglages_fdm.imprimer, fdm-trajets) ; lettres sur les .npz de la planche
des procédés (s'ils existent) ; décalque d'encre (texte.py par le Python système).
    blender -b --factory-startup --python outils\essais\essai_procedes.py"""
import os
import sys
import traceback

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import material_library as SP                                 # noqa: E402
from mathutils import Matrix                                # noqa: E402
from material_library import aretes as AR                     # noqa: E402
from material_library.impression import decalques as DEC      # noqa: E402
from material_library.matieres import procedes as PR          # noqa: E402

col = bpy.context.scene.collection
NPZ = os.path.join(SP.DONNEES, "planches", "procedes")


def plaque(nom):
    me = bpy.data.meshes.new(nom); AR.plaque(36, 22, 2.0, 0.0, 4.0, (0.4, 0.4), cz=11).to_mesh(me)
    o = bpy.data.objects.new(nom, me); col.objects.link(o); return o


try:
    for nom, m in (("fdm", PR.fdm("pla_noir", buse=0.4, plateau="-Y")), ("fdm02", PR.fdm("pla_blanc", buse=0.2, axe="Z")),
                   ("sla", PR.sla("sla_jlc_black")), ("sla_9600", PR.sla("resine_9600_blanche", "brute")),
                   ("mjf", PR.mjf("nylon_pa12_noir", tuile=0.1)), ("acrylique", PR.acrylique_laser()),
                   ("metal", PR.metal("alu_anodise_gris_fonce"))):
        PR.poser(plaque(nom), m)
        assert any(n.type == "BEVEL" for n in m.node_tree.nodes), f"{nom} sans Bevel"
        print("OK", nom, m.name, m.get("procede"))
    PR.couches([bpy.data.materials.new("existante")]); print("OK couches (matière existante)")
    from material_library.matieres import reglages_fdm as RF
    o = plaque("trajets"); RF.imprimer(o, matiere="pla_noir", buse=0.4, plateau="-Y", resolution=512)
    m = o.data.materials[0]
    assert "trajets_fdm_relief" in m.node_tree.nodes and m.node_tree.nodes["couches_fdm_relief"].inputs["Strength"].default_value == 0
    print("OK trajets (plaque tranchée pour elle-même) :", o.sp_fdm.etat)
    if os.path.exists(os.path.join(NPZ, "lettres_0.4.npz")):
        PR.lettres_imprimees(m, np.load(os.path.join(NPZ, "lettres_0.4.npz")))
        PR.acrylique_laser(masque=np.load(os.path.join(NPZ, "lettres_exact.npz")), nom="essai_gravure")
        print("OK lettres_imprimees, lettres_gravees")
    else:
        print("(lettres non essayées : lancer d'abord planche_procedes.py etape=stl et lettres.py)")
    d = DEC.decalque(col, None, "essai_marquage", "TM1637|2341A", 1.0, Matrix.Identity(4))
    assert any(n.type == "TEX_IMAGE" and n.image for n in d.data.materials[0].node_tree.nodes)
    print("OK decalque (encre imprimée)")
    print("ESSAI PROCEDES OK")
except Exception:
    traceback.print_exc(); sys.exit(1)
