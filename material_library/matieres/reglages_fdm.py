r"""Réglages d'impression FDM sur une pièce, panneau « Impression FDM » et bouton « Recalculer les trajets » (feature fdm-trajets,
chunk-04). Le bouton et les scripts passent par la même fonction :
    from material_library.matieres import reglages_fdm as RF
    RF.imprimer(ob, matiere="pla_noir", buse=0.4, parois=2, motif_dessus="monotone", couture="alignee", plateau="-Z")
    RF.recalculer(ob)                       # avec les réglages déjà posés sur l'objet (ce que fait le bouton)
Les réglages vivent sur l'objet (ob.sp_fdm, enregistrés dans le .blend) ; 0 = valeur par défaut du profil U1 de la buse.
Recalculer : maillage évalué (repère de l'objet) → impression/tranchage.py (Python système) → matière refaite par procedes.fdm()
→ procedes.trajets() sur place. Fichiers (trajets .npz, cartes .exr) dans <dossier du .blend>\<nom du .blend>_fdm\ (le .blend
reste léger) ; .blend pas encore enregistré : G:\Blender\Bibliotheque\fdm\cache\. Pas de mise à jour en direct (choix de Lou)."""
import os
import struct
import subprocess
import time

import bpy
import numpy as np

import material_library as SP
from . import catalogue as CAT
from . import procedes as PR

TRANCHAGE = os.path.join(SP.RACINE, "material_library", "impression", "tranchage.py")
RES_MAX = 8192                                       # côté maximal des cartes (≈ 0,5 Go par image de travail à 4096²)


_MATIERES = [(n, CAT.fiche(n)["titre"], "") for n in CAT.noms("Impression FDM")]   # gardée en mémoire (exigence de Blender)


def _matieres(self, context):
    return _MATIERES


class ReglagesFDM(bpy.types.PropertyGroup):
    matiere: bpy.props.EnumProperty(name="Matière", items=_matieres)
    buse: bpy.props.EnumProperty(name="Buse", items=[("0.4", "0,4 mm", "couches 0,2, cordons 0,42"),
                                                      ("0.2", "0,2 mm", "couches 0,1, cordons 0,22")], default="0.4")
    couche: bpy.props.FloatProperty(name="Couche (mm)", description="0 = celle de la buse", min=0.0, max=0.4, step=1, precision=2)
    parois: bpy.props.IntProperty(name="Parois", description="Tours autour du bord et des trous ; 0 = profil de la buse", min=0, max=8)
    motif_dessus: bpy.props.EnumProperty(name="Dessus", items=[("monotone", "Lignes (monotone)", ""),
                                                                ("concentrique", "Concentrique", "")])
    angle: bpy.props.FloatProperty(name="Angle (°)", default=45.0, min=0.0, max=180.0)
    couture: bpy.props.EnumProperty(name="Couture", items=[("alignee", "Alignée", ""), ("arriere", "Arrière", ""),
                                                            ("aleatoire", "Aléatoire", "")])
    plateau: bpy.props.EnumProperty(name="Face sur le plateau", description="Face de la pièce posée sur le plateau (repère objet)",
                                    items=[(a, a, "") for a in ("-Z", "+Z", "-Y", "+Y", "-X", "+X")])
    translucide: bpy.props.FloatProperty(name="Translucide", min=0.0, max=1.0, description="PLA naturel : 0,45")
    grain: bpy.props.EnumProperty(name="Grain du plateau", items=[("fin", "Fin", "PEI poudré fin"),
                                                              ("granuleux", "Granuleux", "plaque granuleuse du F-COM1 (cellules de 0,35)")])
    resolution: bpy.props.IntProperty(name="Cartes (px)", description="0 = automatique (≥ 5 texels par cordon)", min=0, max=RES_MAX)
    etat: bpy.props.StringProperty(name="Dernier calcul", default="")


def _sortie(ob):
    if bpy.data.filepath:
        d = os.path.join(os.path.dirname(bpy.data.filepath), os.path.splitext(os.path.basename(bpy.data.filepath))[0] + "_fdm")
    else:
        d = os.path.join(SP.DONNEES, "fdm", "cache")
    os.makedirs(d, exist_ok=True)
    return d


def _stl(ob, chemin):
    """Maillage évalué de ob (modificateurs compris), repère de l'objet, en STL binaire."""
    dg = bpy.context.evaluated_depsgraph_get(); ev = ob.evaluated_get(dg); me = ev.to_mesh()
    me.calc_loop_triangles()
    co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    tv = np.empty(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get("vertices", tv)
    tri = co[tv.reshape(-1, 3)]; ev.to_mesh_clear()
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    a = np.zeros(len(tri), dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")])); a["n"] = n; a["v"] = tri.reshape(-1, 9)
    with open(chemin, "wb") as f: f.write(b"\0" * 80 + struct.pack("<I", len(tri)) + a.tobytes())


def trancher_objet(ob, dossier, buse=0.4, plateau="-Z", **reglages):
    """Maillage évalué de ob (repère de l'objet) → STL → impression/tranchage.py (Python système) avec la buse, la face sur le
    plateau et les réglages de tranchage.reglages() (parois=…, motif_dessus=…) : rend le chemin des trajets (.npz) dans `dossier`.
    Pour les scripts qui construisent leurs pièces (maquettes) sans passer par les réglages de l'objet."""
    os.makedirs(dossier, exist_ok=True)
    stl, npz = os.path.join(dossier, f"{ob.name}.stl"), os.path.join(dossier, f"{ob.name}_trajets.npz")
    _stl(ob, stl)
    cmd = [SP.PYTHON_SYSTEME, TRANCHAGE, npz, str(buse), stl, "--plateau", plateau]
    if reglages: cmd += ["--set"] + [f"{k}={v}" for k, v in reglages.items()]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode: raise RuntimeError(f"tranchage.py : {p.stdout[-800:]} {p.stderr[-800:]}")
    return npz


def recalculer(ob):
    """Recalcule les trajets de ob avec ses réglages (ob.sp_fdm) et refait sa matière. Rend l'état (texte du panneau)."""
    enregistrer()
    if ob is None or ob.type != "MESH": raise RuntimeError("choisir une pièce (objet maillage)")
    if ob.library or ob.override_library:
        raise RuntimeError(f"« {ob.name} » est lié d'un asset : recalculer dans l'asset lui-même, pas dans le plan qui le lie")
    r = ob.sp_fdm; t0 = time.time(); d = _sortie(ob); buse = float(r.buse)
    reg = {"motif_dessus": r.motif_dessus, "angle": r.angle, "couture": r.couture}
    if r.couche > 0: reg["couche"] = r.couche
    if r.parois > 0: reg["parois"] = r.parois
    npz = trancher_objet(ob, d, buse, r.plateau, **reg)
    m = PR.fdm(r.matiere, buse=buse, couche=r.couche or None, plateau=r.plateau, translucide=r.translucide, nom=f"FDM_{ob.name}",
               grain=r.grain)
    PR.poser(ob, m)
    PR.trajets(ob, npz, res=r.resolution or None, copie=False, dossier=d)
    with np.load(npz, allow_pickle=True) as t: nc = int(t["couche"].max()) + 1
    res = bpy.data.images[f"SP_hauteur_{ob.name}"].size[0]
    r.etat = (f"{time.strftime('%d/%m %H:%M')} · buse {r.buse} · {r.parois or 'défaut'} parois · {r.motif_dessus} · "
              f"{nc} couches · {res} px · {time.time() - t0:.0f} s")
    return r.etat


def imprimer(ob, **reglages):
    """Pose les réglages (noms des propriétés de ReglagesFDM : matiere, buse=0.4, parois, motif_dessus…) puis recalcule."""
    enregistrer()
    for k, v in reglages.items():
        setattr(ob.sp_fdm, k, str(v) if k == "buse" else v)
    return recalculer(ob)


class SP_OT_fdm_recalculer(bpy.types.Operator):
    bl_idname = "sp.fdm_recalculer"; bl_label = "Recalculer les trajets"
    bl_description = "Trancher la pièce avec ses réglages (comme la U1 de l'imprimeur FDM) et refaire sa matière FDM"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context): return context.active_object is not None and context.active_object.type == "MESH"

    def execute(self, context):
        wm = context.window_manager; wm.progress_begin(0, 1)
        try:
            self.report({"INFO"}, recalculer(context.active_object))
        except RuntimeError as e:
            self.report({"ERROR"}, str(e)); return {"CANCELLED"}
        finally:
            wm.progress_end()
        return {"FINISHED"}


class VIEW3D_PT_sp_fdm(bpy.types.Panel):
    bl_label = "Impression FDM"; bl_space_type = "VIEW_3D"; bl_region_type = "UI"; bl_category = "Material library"

    def draw(self, context):
        ob = context.active_object; L = self.layout
        if ob is None or ob.type != "MESH": L.label(text="Choisir une pièce"); return
        r = ob.sp_fdm
        for p in ("matiere", "buse", "couche", "parois", "motif_dessus", "angle", "couture", "plateau", "grain", "translucide",
                  "resolution"):
            L.prop(r, p)
        L.operator("sp.fdm_recalculer", icon="FILE_REFRESH")
        if r.etat: L.label(text=r.etat, icon="CHECKMARK")
        if ob.library or ob.override_library: L.label(text="Objet lié : recalculer dans l'asset", icon="ERROR")


CLASSES = (ReglagesFDM, SP_OT_fdm_recalculer, VIEW3D_PT_sp_fdm)


def enregistrer():
    """Enregistre les classes une seule fois (add-on ou script)."""
    if hasattr(bpy.types.Object, "sp_fdm") and "sp_fdm" in bpy.types.Object.bl_rna.properties: return
    for c in CLASSES: bpy.utils.register_class(c)
    bpy.types.Object.sp_fdm = bpy.props.PointerProperty(type=ReglagesFDM)


def desenregistrer():
    if "sp_fdm" in bpy.types.Object.bl_rna.properties: del bpy.types.Object.sp_fdm
    for c in reversed(CLASSES):
        if getattr(c, "is_registered", False): bpy.utils.unregister_class(c)
