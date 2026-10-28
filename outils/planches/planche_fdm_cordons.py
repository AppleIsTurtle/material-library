r"""Planche des cordons FDM (feature fdm-trajets, chunk-03) : embase de la F-COM2 et bouton TFR du F-COM1, buses 0,4 et 0,2,
habillés de leurs trajets simulés (impression/tranchage.py → procedes.trajets) ; gros plans de la face (posée sur le plateau),
de la tranche (couches, couture) et du dos (dessus en lignes), dans le studio du site.
    blender -b G:\Blender\MFS\plans_fixes\site\hero.blend --python outils\planches\planche_fdm_cordons.py -- [quick] [cas=embase_04,…]
    (lancer via D:\Claude\MFS\outils\blender_garde.ps1)
Les STL sont lus dans MFS (orientés pour l'impression : z vers le haut, face sur le plateau à z = 0), tranchés une fois par le
Python système (trajets_<cas>.npz dans la sortie), puis dressés comme dans un produit (face vers −y)."""
import math
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import studio as ST                                   # noqa: E402
import bpy                                            # noqa: E402
from mathutils import Matrix, Vector                  # noqa: E402
import material_library as SP                           # noqa: E402
from material_library.matieres import procedes as PR    # noqa: E402

MFS = r"D:\Claude\MFS\boitier\f-com"
EMBASE = [os.path.join(MFS, r"commun\stl_par_couleur\f-com2_facade_embase_v0\f-com2_facade_embase_v0__noir.stl")]
TFR = [os.path.join(MFS, rf"f-com1\stl\f-com1_A2_bouton_TFR_v5__{c}.stl") for c in ("noir", "blanc", "naturel")]
MATIERE = {"noir": "pla_noir", "blanc": "pla_blanc", "naturel": "pla_naturel"}
CAS = {"embase_04": (EMBASE, 0.4), "embase_02": (EMBASE, 0.2), "tfr_04": (TFR, 0.4), "tfr_02": (TFR, 0.2)}
choix = next((a[4:].split(",") for a in ST.ARGV if a.startswith("cas=")), list(CAS))
sc, col, SORTIE = ST.preparer("fdm_cordons", res=(1200, 900))
TRANCHAGE = os.path.join(SP.RACINE, "material_library", "impression", "tranchage.py")


def charger(cas):
    stls, buse = CAS[cas]
    npz = os.path.join(SORTIE, f"trajets_{cas}.npz")
    if not os.path.exists(npz):
        r = subprocess.run([SP.PYTHON_SYSTEME, TRANCHAGE, npz, str(buse)] + stls, capture_output=True, text=True)
        if r.returncode: raise RuntimeError(r.stdout[-1500:] + r.stderr[-1500:])
        print(r.stdout.strip(), flush=True)
    objs = []
    for p in stls:
        avant = set(bpy.data.objects)
        bpy.ops.wm.stl_import(filepath=p, global_scale=1.0)
        o = (set(bpy.data.objects) - avant).pop(); o.name = f"FDM_{cas}_{os.path.basename(p)[:-4].split('__')[-1]}"
        for c in list(o.users_collection): c.objects.unlink(o)
        col.objects.link(o)
        coul = os.path.basename(p)[:-4].split("__")[-1]
        PR.poser(o, PR.fdm(MATIERE.get(coul, "pla_noir"), buse=buse, plateau="-Z", translucide=0.45 if coul == "naturel" else 0.0,
                           nom=f"FDM_{cas}_{coul}"))
        for f in o.data.polygons: f.use_smooth = False
        PR.trajets(o, npz)
        objs.append(o)
    # dressé comme un produit : face (posée sur le plateau, −z) vers −y, posé sur le sol, centré en x
    R = Matrix.Rotation(math.radians(-90), 4, "X")
    pts = [R @ v.co for o in objs for v in o.data.vertices]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    T = Matrix.Translation((-(lo.x + hi.x) / 2, -lo.y, -lo.z))
    for o in objs: o.matrix_world = T @ R
    return objs, hi - lo


pieces, tailles = {}, {}
for cas in choix:
    pieces[cas], tailles[cas] = charger(cas)
tous = [o for v in pieces.values() for o in v]
for cas in choix:
    L, E, H = tailles[cas]                                    # largeur (x), épaisseur (y, face à y = 0), hauteur (z)
    petit = L < 30
    cx, cz = (L / 2 - (3.0 if petit else 22.0)), H / 2         # près du bord droit : un trou, une fenêtre, l'arête
    d = 45.0 if petit else 140.0; lens = 200 if petit else 100
    dt = 45.0 if petit else 40.0                               # tranche : champ ≈ 5 mm (TFR), ≈ 9 mm (embase)
    cams = {"face": ST.camera(col, f"CAM_{cas}_face", (cx - 0.4 * d, -d, cz + 0.3 * d), (cx, 0.0, cz), lens, 11.0),
            "tranche": ST.camera(col, f"CAM_{cas}_tranche", (L / 2 + 0.6 * dt, -0.45 * dt, cz + 0.15 * dt), (L / 2, E / 2, cz),
                                 lens, 16.0),
            "dos": ST.camera(col, f"CAM_{cas}_dos", (cx - 0.4 * d, E + d, cz + 0.3 * d), (cx, E, cz), lens, 11.0)}
    ST.montrer(pieces[cas], tous)
    for v, cam in cams.items():
        ST.rendre(sc, cam, os.path.join(SORTIE, f"{cas}_{v}.png"))
print("FINI", SORTIE, flush=True)
