# Marquages imprimés des composants (circuits, afficheurs) pour les rendus : texte rendu en encre imprimée par texte.py
# (Python de KiCad, PIL : étalement, bord irrégulier, épaisseur qui varie — encre.py), posé en décalque sur la pièce (plan à 4 µm de
# la surface) ; matière : encre mate mélangée à du transparent selon l'image, légère surépaisseur. Lou, 2026-10-26 : « les écritures
# sont imprimées, elles sont un peu baveuses, pas parfaitement imprimées ».
# Repris de MFS boitier/scripts/impression.py (2026-10-26), material-library chunk-04 ; l'image est faite par texte.py (Python de
# KiCad s'il est installé, sinon le Python système : il faut Pillow et numpy).
# Usage (Blender) : decalques.decalque(col, parent, nom, "TM1637|2341A", cap_mm, matrice, encre="#c9c9c4")
#   matrice : pose du décalque dans le repère de `parent` (plan local XY, texte lisible selon +X, normale +Z vers l'extérieur).
import os, subprocess, tempfile, zlib
import bpy, bmesh
from mathutils import Matrix
from material_library.matieres.couleurs import srgb

ICI = os.path.dirname(os.path.abspath(__file__))
KICAD_PY = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "KiCad", "10.0", "bin", "python.exe")
PYTHON = KICAD_PY if os.path.exists(KICAD_PY) else "python"          # Python avec Pillow (pas celui de Blender)
POLICE = r"C:\Windows\Fonts\arial.ttf"


def image(lignes, cap, police=POLICE, interligne=1.45):
    """Image d'encre (PNG, 200 px/mm) → (chemin, largeur mm, hauteur mm)."""
    cle = f"{zlib.crc32(f'{lignes}|{cap}|{police}|{interligne}'.encode()):08x}"
    dst = os.path.join(tempfile.gettempdir(), f"sp_marquage_{cle}.png")
    r = subprocess.run([PYTHON, os.path.join(ICI, "texte.py"), dst, str(cap), police, lignes, str(interligne)],
                       check=True, capture_output=True, text=True)
    _, _, w, h = next(l for l in r.stdout.splitlines() if l.startswith("TEXTE")).split()
    return dst, float(w), float(h)


def matiere(nom, chemin, encre="#c9c9c4", rugo=0.55):
    """Encre mate selon l'image (blanc = encre), transparent ailleurs, surépaisseur de quelques µm."""
    m = bpy.data.materials.new(nom); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial"); b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = srgb(encre); b.inputs["Roughness"].default_value = rugo
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mix = nt.nodes.new("ShaderNodeMixShader")
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = bpy.data.images.load(chemin, check_existing=True)
    tex.image.colorspace_settings.name = 'Non-Color'; tex.interpolation = 'Cubic'; tex.extension = 'CLIP'
    nt.links.new(tex.outputs["Color"], mix.inputs["Fac"]); nt.links.new(tr.outputs["BSDF"], mix.inputs[1])
    nt.links.new(b.outputs["BSDF"], mix.inputs[2]); nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Distance"].default_value = 0.006
    nt.links.new(tex.outputs["Color"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    m.diffuse_color = srgb(encre); return m


def decalque(col, parent, nom, lignes, cap, matrice, encre="#c9c9c4", police=POLICE, interligne=1.45):
    chemin, w, h = image(lignes, cap, police, interligne)
    bm = bmesh.new(); uv = bm.loops.layers.uv.new("UVMap")
    vs = [bm.verts.new((x, y, 0.0)) for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
    f = bm.faces.new(vs)
    for lp, (u, v) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uv].uv = (u, v)
    me = bpy.data.meshes.new(nom); bm.to_mesh(me); bm.free()
    me.materials.append(matiere(nom + "_encre", chemin, encre))
    o = bpy.data.objects.new(nom, me); col.objects.link(o)
    o.parent = parent; o.matrix_parent_inverse = Matrix.Identity(4); o.matrix_basis = matrice
    o.visible_shadow = False                                  # une pellicule d'encre ne projette pas d'ombre
    return o
