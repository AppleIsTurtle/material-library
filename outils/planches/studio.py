r"""Studio des planches de contrôle : la scène du site (hero.blend, studio et éclairage de tous les rendus de MFS) ouverte EN LECTURE
— jamais enregistrée —, le F-COM1 lié écarté hors champ ; caméras et rendu Cycles sur GPU.
    blender -b G:\Blender\MFS\plans_fixes\site\hero.blend --python outils\planches\planche_<x>.py -- [quick]
    (lancer via D:\Claude\MFS\outils\blender_garde.ps1)
Rendus dans G:\Blender\Bibliotheque\planches\<planche>\ (hors git) ; assemblage : assembler.py (Python système + Pillow)."""
import math
import os
import sys

import bpy
from mathutils import Vector

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, RACINE)
import material_library as SP                          # noqa: E402

HERO = r"G:\Blender\MFS\plans_fixes\site\hero.blend"
ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
QUICK = "quick" in ARGV


def preparer(planche, res=(1200, 900), echantillons=256):
    """Scène prête : F-COM1 écarté, collection PLANCHE, GPU ; renvoie (scène, collection, dossier de sortie)."""
    if os.path.normcase(bpy.data.filepath) != os.path.normcase(HERO):
        raise RuntimeError(f"ouvrir {HERO} (en lecture) avant ce script, pas {bpy.data.filepath!r}")
    sc = bpy.context.scene
    bpy.data.objects["F-COM1"].location = (0, 0, -5000)     # écarté plutôt qu'exclu (comme maquette_grand_format.couche_fcom1)
    col = bpy.data.collections.new("PLANCHE"); sc.collection.children.link(col)
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"; prefs.get_devices()
    for d in prefs.devices: d.use = d.type == "OPTIX"
    sc.cycles.device = "GPU"; sc.render.engine = "CYCLES"
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 50 if QUICK else 100
    sc.cycles.samples = 48 if QUICK else echantillons
    sc.render.film_transparent = False
    sortie = os.path.join(SP.DONNEES, "planches", planche)
    os.makedirs(sortie, exist_ok=True)
    return sc, col, sortie


def camera(col, nom, loc, cible, lens, fstop=8.0):
    cd = bpy.data.cameras.new(nom); cd.lens = lens; cd.sensor_width = 36; cd.clip_start = 1.0; cd.clip_end = 20000.0   # mm
    cd.dof.use_dof = True; cd.dof.aperture_fstop = fstop
    o = bpy.data.objects.new(nom, cd); col.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(cible) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    cd.dof.focus_distance = (Vector(cible) - Vector(loc)).length
    return o


def montrer(objets, tous):
    """Seuls `objets` sont rendus parmi `tous`."""
    for o in tous: o.hide_render = o not in objets


def rendre(sc, cam, chemin):
    sc.camera = cam
    if QUICK: chemin = chemin.replace(".png", "_quick.png")
    sc.render.filepath = chemin
    bpy.ops.render.render(write_still=True)
    print("RENDU", chemin, flush=True)
    return chemin
