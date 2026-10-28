r"""Pièces du commerce par leur désignation normalisée → objets Blender habillés (géométrie de fixations.py / filets.py, matière de
shading.py, booléens appliqués, pas d'arête vive, UV en mm) :
    vis("M4 x 8 DIN 84 inox A2", x, z, y_appui, col=COLL, prefixe="GF_VIS_QDT_0")
    ecrou("M3 ISO 4032 inox", x, z, y_av, col=COLL)        rondelle("M3 DIN 125", …)        insert("M3 INSERT laiton", …)
Repère des maquettes : axe parallèle à y, -y vers l'utilisateur ; la tête est du côté -y. Les noms suivent `prefixe` (tête, puis
`prefixe`_filet et `prefixe`_ame pour la tige) : les contrôles de collision des maquettes reconnaissent leurs préfixes (GF_VIS_*…)."""
import math

import bpy

from .. import aretes as AR
from ..imperfections.uv_mm import uv_plan_mm
from . import filets as F
from . import fixations as FX
from . import normes as N
from . import shading as SH

BISEAU = {"cylindrique_fendue": 0.2, "bombee_cruciforme": 0.15, "fraisee_cruciforme": 0.15, "btr": 0.15}   # biseau appliqué (mm)
_MATIERES = {}


def matiere(nom):
    """Matière de la visserie (« inox », « oxyde », « laiton » ou une bpy.types.Material), créée une fois par fichier."""
    if isinstance(nom, bpy.types.Material): return nom
    m = _MATIERES.get(nom)
    if m is None or m.name not in bpy.data.materials:
        m = _MATIERES[nom] = SH.MATIERES[nom]()
    return m


def objet(nom, bm, mat, col, parent=None, lisse=35.0):
    """bmesh → objet lissé (arêtes marquées au-delà de `lisse` degrés), dans `col`, enfant de `parent` (coordonnées dans son
    repère)."""
    me = bpy.data.meshes.new(nom); bm.to_mesh(me); bm.free()
    me.materials.append(mat)
    if lisse: me.shade_smooth(); me.set_sharp_from_angle(angle=math.radians(lisse))
    o = bpy.data.objects.new(nom, me); col.objects.link(o)
    if parent: o.parent = parent
    return o


def _uv(o, m):
    """UV en mm : l'oxydé et les têtes peintes y lisent leurs cartes (sans effet sur l'inox)."""
    return uv_plan_mm(o)


def vis(designation, x=0.0, z=0.0, y_appui=0.0, a=0.0, col=None, parent=None, prefixe="SP_VIS", mat=None, filetee=True):
    """Vis complète : tête (norme, empreinte tournée de a degrés, booléen appliqué, biseau) + tige filetée de la longueur de la
    désignation. y_appui = plan sous la tête ; pour une fraisée, plan du dessus (la longueur se compte depuis lui, comme le
    commerce). Renvoie [tête, filet, âme]."""
    D = N.designation(designation); c = N.cotes(D["norme"], D["d"]); d, l = D["d"], D["l"]
    col = col or bpy.context.scene.collection
    m = matiere(mat or D["matiere"])
    bm, outils = FX.tete(D["norme"], d, x, z, y_appui, a)
    t = objet(prefixe, bm, m, col, parent)
    AR.retrancher(t, outils, ponderer=False); AR.adoucir(t, BISEAU[c["forme"]])
    objs = [_uv(t, m)]
    if filetee and l:
        y0 = y_appui + (round(0.6 * c["k"], 1) if c["forme"] == "fraisee_cruciforme" else 0.0)   # fraisée : tige dans le cône
        bf, ba = F.tige(x, z, y0, l - (y0 - y_appui), d, c["pas"], sortie=1.0)   # filet roulé : sort sur la pointe
        objs += [_uv(objet(prefixe + "_filet", bf, m, col, parent, 48.0), m), _uv(objet(prefixe + "_ame", ba, m, col, parent, 48.0), m)]
    return objs


def ecrou(designation, x=0.0, z=0.0, y_av=0.0, col=None, parent=None, prefixe="SP_ECROU", mat=None):
    """Écrou hexagonal ISO 4032 de y_av à y_av + m (vers +y) : [corps, taraudage]."""
    D = N.designation(designation); c = N.cotes(D["norme"], D["d"])
    col = col or bpy.context.scene.collection; m = matiere(mat or D["matiere"])
    bc, bt = F.ecrou(x, z, y_av, y_av + c["m"], D["d"], c["pas"], c["s"])
    return [_uv(objet(prefixe, bc, m, col, parent), m), _uv(objet(prefixe + "_taraudage", bt, m, col, parent, 48.0), m)]


def rondelle(designation, x=0.0, z=0.0, y_av=0.0, col=None, parent=None, prefixe="SP_RONDELLE", mat=None):
    """Rondelle plate DIN 125 de y_av à y_av + h : [rondelle]."""
    D = N.designation(designation); col = col or bpy.context.scene.collection; m = matiere(mat or D["matiere"])
    return [_uv(objet(prefixe, F.rondelle(x, z, y_av, d=D["d"]), m, col, parent, 30.0), m)]


def insert(designation, x=0.0, z=0.0, y_face=0.0, col=None, parent=None, prefixe="SP_INSERT", mat="laiton", mat_fond=None):
    """Insert laiton à chaud (ruthex) : face visible en y_face, corps vers -y (logement à prévoir : filets.insert_cotes) ;
    [insert, fond de l'alésage]."""
    D = N.designation(designation); r_in, r_out, L, _ = F.insert_cotes(D["d"])
    col = col or bpy.context.scene.collection
    bi, bf = F.insert(x, z, y_face - L, y_face - 0.08, r_in, r_out)
    fond = mat_fond or bpy.data.materials.get("SP_fond_de_filetage")
    if fond is None:
        fond = bpy.data.materials.new("SP_fond_de_filetage"); fond.use_nodes = True
        b = fond.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.01, 0.01, 0.01, 1); b.inputs["Roughness"].default_value = 0.6
    return [objet(prefixe, bi, matiere(mat), col, parent, 50.0), objet(prefixe + "_fond", bf, fond, col, parent, 0)]


def piece(designation, *args, **kw):
    """vis(), ecrou(), rondelle() ou insert() selon la norme de la désignation."""
    D = N.designation(designation); forme = N.cotes(D["norme"], D["d"])["forme"]
    return {"ecrou": ecrou, "rondelle": rondelle, "insert": insert}.get(forme, vis)(designation, *args, **kw)
