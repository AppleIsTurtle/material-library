r"""Essai du chunk-04 de fdm-trajets : add-on enregistré, imprimer() par script et bouton « Recalculer les trajets » donnent les
mêmes cartes ; changer buse et parois change le résultat ; UV existantes et UV actives gardées ; fichiers à côté du .blend ;
objet lié refusé.
    blender -b --factory-startup --python outils\essais\essai_reglages_fdm.py      (via D:\Claude\MFS\outils\blender_garde.ps1)"""
import importlib.util
import os
import sys
import traceback

import bpy
import numpy as np

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, RACINE)
import material_library as SP                                 # noqa: E402

STL = r"D:\Claude\MFS\boitier\f-com\f-com1\stl\f-com1_A2_bouton_TFR_v5__noir.stl"
DOSSIER = os.path.join(SP.DONNEES, "fdm", "essai"); os.makedirs(DOSSIER, exist_ok=True)


def pixels(nom):
    img = bpy.data.images[nom]; a = np.empty(img.size[0] * img.size[1] * 4, np.float32); img.pixels.foreach_get(a)
    return a.reshape(img.size[1], img.size[0], 4)[..., :3]


def importer(nom):
    avant = set(bpy.data.objects); bpy.ops.wm.stl_import(filepath=STL, global_scale=1.0)
    o = (set(bpy.data.objects) - avant).pop(); o.name = nom; return o


try:
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    bpy.context.scene.render.engine = "CYCLES"; bpy.context.scene.cycles.device = "CPU"
    spec = importlib.util.spec_from_file_location("material_library_fdm", os.path.join(RACINE, "blender", "scripts", "addons",
                                                                                     "material_library_fdm", "__init__.py"))
    addon = importlib.util.module_from_spec(spec); spec.loader.exec_module(addon); addon.register()
    from material_library.matieres import reglages_fdm as RF
    assert hasattr(bpy.types, "VIEW3D_PT_sp_fdm") and hasattr(bpy.types.Object, "sp_fdm"); print("OK add-on enregistré")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(DOSSIER, "essai_reglages.blend"))

    a = importer("TFR_script"); a.data.uv_layers.new(name="UV_mm"); a.data.uv_layers.active = a.data.uv_layers["UV_mm"]
    uv0 = np.empty(len(a.data.loops) * 2, np.float32); a.data.uv_layers["UV_mm"].data.foreach_get("uv", uv0)
    print("script :", RF.imprimer(a, matiere="pla_noir", buse=0.4, plateau="-Z"))
    uv1 = np.empty(len(a.data.loops) * 2, np.float32); a.data.uv_layers["UV_mm"].data.foreach_get("uv", uv1)
    assert np.array_equal(uv0, uv1) and a.data.uv_layers.active.name == "UV_mm", "UV existantes ou UV active modifiées"
    print("OK UV existantes et UV active gardées (UV_fdm à part)")

    b = importer("TFR_bouton")
    for x in bpy.context.view_layer.objects: x.select_set(False)
    b.select_set(True); bpy.context.view_layer.objects.active = b
    b.sp_fdm.matiere = "pla_noir"; b.sp_fdm.buse = "0.4"; b.sp_fdm.plateau = "-Z"
    assert bpy.ops.sp.fdm_recalculer() == {"FINISHED"}; print("bouton :", b.sp_fdm.etat)
    ha, hb = pixels("SP_hauteur_TFR_script"), pixels("SP_hauteur_TFR_bouton")
    fa, fb = pixels("SP_fil_TFR_script"), pixels("SP_fil_TFR_bouton")
    e = max(float(np.abs(ha - hb).max()), float(np.abs(fa - fb).max()))
    assert e < 1e-5, f"script et bouton diffèrent : {e}"; print(f"OK script = bouton (écart max {e:.1e})")
    assert "plateau_contact" in b.data.materials[0].node_tree.nodes, "grain du plateau non limité aux zones de contact"
    print("OK grain du plateau limité aux points au contact (z ≤ 0,03 mm)")

    d = os.path.join(DOSSIER, "essai_reglages_fdm")
    for f in ("TFR_bouton_trajets.npz", "TFR_bouton_hauteur.exr", "TFR_bouton_fil.exr"):
        assert os.path.exists(os.path.join(d, f)), f"absent : {f}"
    print("OK fichiers dans", d)

    b.sp_fdm.buse = "0.2"; b.sp_fdm.parois = 1
    assert bpy.ops.sp.fdm_recalculer() == {"FINISHED"}; print("bouton (0,2, 1 paroi) :", b.sp_fdm.etat)
    with np.load(os.path.join(d, "TFR_bouton_trajets.npz"), allow_pickle=True) as t:
        nc = int(t["couche"].max()) + 1; nb_int = int((t["type"] == 1).sum())
    assert nc == 84, nc
    hc = pixels("SP_hauteur_TFR_bouton")                      # buse 0,2 : cordons 2 fois plus fins → cartes plus grandes
    assert hc.shape != hb.shape or float(np.abs(hc - hb).max()) > 1e-3, "le changement de buse n'a rien changé"
    assert len(bpy.data.objects["TFR_bouton"].data.materials) == 1 and "trajets_fdm_relief" in b.data.materials[0].node_tree.nodes
    nb_bump = sum(n.name.startswith("trajets_fdm_relief") for n in b.data.materials[0].node_tree.nodes)
    assert nb_bump == 1, f"{nb_bump} reliefs de trajets : la matière s'empile au recalcul"
    print(f"OK buse 0,2 + 1 paroi : {nc} couches, {nb_int} segments de paroi intérieure (cordons centraux), matière refaite")

    bpy.ops.wm.save_mainfile()
    bpy.ops.wm.read_homefile(use_empty=True); addon.register()
    with bpy.data.libraries.load(os.path.join(DOSSIER, "essai_reglages.blend"), link=True) as (src, dst): dst.objects = ["TFR_bouton"]
    lie = dst.objects[0]; bpy.context.scene.collection.objects.link(lie)
    try:
        RF.recalculer(lie); raise AssertionError("objet lié accepté")
    except RuntimeError as err:
        assert "lié" in str(err); print("OK objet lié refusé :", err)
    print("ESSAI REGLAGES FDM OK")
except Exception:
    traceback.print_exc(); sys.exit(1)
