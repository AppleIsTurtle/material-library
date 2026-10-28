r"""Matières de la visserie : inox naturel A2, acier oxydé noir usé (d'après photo), têtes peintes, laiton des inserts ; nœud Bevel
de la tête (pas d'arête vive au rendu, R 0,2 : aretes.RAYONS["vis"]). Repris de MFS : photoreal.acier_vis (V3_vis_grise),
maquette_grand_format.inox_noirci_use (GF_acier_oxyde_noir) et laiton (GF_laiton). Les cartes d'imperfections sont lues sur des UV
dépliés en mm : appeler imperfections.uv_mm.uv_plan_mm(objet) sur chaque pièce oxydée ou peinte (pieces.py le fait)."""
from ..imperfections import imperfections as IMP
from ..matieres.couleurs import srgb
from ..matieres.noeuds import neuf as _neuf


class _Noeuds:
    """Petits constructeurs de nœuds (maths, plages, bruits sur UV, mélanges de couleurs) pour une matière."""
    def __init__(self, nt, uv):
        self.nt, self.uv = nt, uv

    def op(self, o, a, b_=None, clamp=False):
        n_ = self.nt.nodes.new("ShaderNodeMath"); n_.operation = o; n_.use_clamp = clamp
        for k, v in enumerate((a, b_)):
            if v is None: continue
            if isinstance(v, (int, float)): n_.inputs[k].default_value = v
            else: self.nt.links.new(v, n_.inputs[k])
        return n_.outputs[0]

    def plage(self, src, de, a=0.0, b_=1.0):
        mr = self.nt.nodes.new("ShaderNodeMapRange"); mr.clamp = True
        mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = de
        mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = a, b_
        self.nt.links.new(src, mr.inputs["Value"]); return mr.outputs["Result"]

    def bruit(self, echelle, detail=3.0):
        n_ = self.nt.nodes.new("ShaderNodeTexNoise"); n_.inputs["Scale"].default_value = echelle; n_.inputs["Detail"].default_value = detail
        self.nt.links.new(self.uv, n_.inputs["Vector"]); return n_.outputs["Fac"]

    def carte(self, nom, tuile, decal, de):
        c = IMP.carte_uv(self.nt, self.uv, nom, tuile, decal)
        return self.plage(c, de) if c else self.op("MULTIPLY", 0.0, 0.0)

    def arete(self, de, rayon=0.25):
        """Masque des arêtes indépendant du maillage : écart entre la normale arrondie par un nœud Bevel de `rayon` et la normale
        vraie (0 sur les faces, → 1 sur l'arête), ramené de `de` à 0..1. (La Pointiness de MFS dépend de la densité du maillage :
        sur un écrou peu dense, toute la surface passait pour une arête.)"""
        bev = self.nt.nodes.new("ShaderNodeBevel"); bev.inputs["Radius"].default_value = rayon; bev.samples = 8
        geo = self.nt.nodes.new("ShaderNodeNewGeometry")
        dp = self.nt.nodes.new("ShaderNodeVectorMath"); dp.operation = "DOT_PRODUCT"
        self.nt.links.new(bev.outputs["Normal"], dp.inputs[0]); self.nt.links.new(geo.outputs["Normal"], dp.inputs[1])
        return self.plage(self.op("SUBTRACT", 1.0, dp.outputs["Value"]), de)

    def mix(self, fac, a, c):
        mx = self.nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"
        e = lambda ident: next(i for i in mx.inputs if i.identifier == ident)
        self.nt.links.new(fac, e("Factor_Float"))
        if isinstance(a, tuple): e("A_Color").default_value = a
        else: self.nt.links.new(a, e("A_Color"))
        if isinstance(c, tuple): e("B_Color").default_value = c
        else: self.nt.links.new(c, e("B_Color"))
        return next(o for o in mx.outputs if o.identifier == "Result_Color")


def bevel_tete(m, rayon=0.2):
    """Nœud Bevel de la tête (R 0,2 : arêtes d'une tête frappée à froid) sous le relief de la matière : aretes.bevel_rendu."""
    from .. import aretes as AR
    return AR.bevel_rendu(m, rayon)


def inox_naturel(nom="SP_inox_A2", bevel=0.2):
    """Vis en inox A2 naturel, non teinté (Lou, 2026-10-15 ; vis du F-COM1 et attaches du F-COM2) : gris clair métallique,
    rugosité uniforme 0,2 (une rugosité par zones tachait les têtes en gros plan). bevel = rayon du nœud Bevel (None : sans)."""
    m, nt, b = _neuf(nom)
    b.inputs["Base Color"].default_value = srgb("#c3c5c7"); b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.2
    m.diffuse_color = srgb("#c3c5c7")
    return bevel_tete(m, bevel) if bevel else m


def acier_oxyde_noir(nom="SP_acier_oxyde_noir", bevel=0.2):
    """Acier oxydé noir du commerce, usé (petites vis M3 ISO 7046 de la réplique ; Lou, 2026-10-27 : « elles doivent avoir des
    imperfections, prends des vraies références »). D'après la photo d'un lot de DIN 965 M4 oxydées noires (monsterbolts.com) :
    gris anthracite satiné (pas un noir pur) légèrement marbré, fin piqueté brillant de l'oxyde, arêtes du dessus et de l'empreinte
    nettement arrondies (frappe à froid) ; usure : micro-rayures, frottements, métal clair par endroits sur les arêtes vives
    (masque d'arête par nœud Bevel depuis le 2026-10-27, au lieu de la Pointiness de MFS).
    Cartes et bruits lus sur les UV en mm (uv_plan_mm) ; arrondi des arêtes au rendu par le nœud Bevel."""
    m, nt, b = _neuf(nom)
    b.inputs["Metallic"].default_value = 1.0
    K = _Noeuds(nt, nt.nodes.new("ShaderNodeUVMap").outputs["UV"])
    marbre = K.plage(K.bruit(0.6, 4.0), (0.4, 0.62))                                 # marbrure de l'oxyde (~1,5 mm)
    vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 22.0; nt.links.new(K.uv, vo.inputs["Vector"])
    pique = K.op("MULTIPLY", K.plage(vo.outputs["Distance"], (0.12, 0.03)), K.plage(K.bruit(2.0), (0.45, 0.7)))   # piqueté ~0,04 mm
    micro = K.carte("micro_rayures", 9.0, 0.31, (0.35, 0.9)); frot = K.carte("frottements", 17.0, 0.57, (0.2, 0.85))
    pou = K.carte("poussiere", 7.0, 0.13, (0.65, 0.95))
    use = K.op("MULTIPLY", K.arete((0.02, 0.12)), K.plage(K.bruit(3.0, 6.0), (0.45, 0.62)), clamp=True)   # métal clair sur les arêtes
    coul = K.mix(K.op("MULTIPLY", marbre, 0.6), srgb("#26272a"), srgb("#34363a"))
    coul = K.mix(K.op("MULTIPLY", pique, 0.5), coul, srgb("#5c5e62"))
    coul = K.mix(K.op("MULTIPLY", use, 0.8), coul, srgb("#8a8c8f"))
    coul = K.mix(K.op("MULTIPLY", pou, 0.35), coul, srgb("#a8a49c"))
    nt.links.new(coul, b.inputs["Base Color"])
    rug = K.op("ADD", 0.4, K.op("MULTIPLY", K.op("SUBTRACT", marbre, 0.5), 0.08))
    rug = K.op("ADD", rug, K.op("MULTIPLY", micro, 0.14)); rug = K.op("ADD", rug, K.op("MULTIPLY", frot, 0.1))
    rug = K.op("ADD", rug, K.op("MULTIPLY", pou, 0.3)); rug = K.op("SUBTRACT", rug, K.op("MULTIPLY", use, 0.15), clamp=True)
    nt.links.new(rug, b.inputs["Roughness"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25; bp.inputs["Distance"].default_value = 0.003
    nt.links.new(pique, bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    m.diffuse_color = srgb("#26272a")
    return bevel_tete(m, bevel) if bevel else m


inox_noirci_use = acier_oxyde_noir          # nom dans MFS (maquette_grand_format.inox_noirci_use)


def tete_peinte(hexa, nom=None, rugo=0.42, bevel=0.2):
    """Tête peinte industrielle (vis à tête laquée au RAL de la façade, minimum de commande : réservée aux séries) : laque satinée
    `hexa` (base compensée à la pipette) sur acier, peau d'orange très fine, laque usée sur les arêtes vives (acier gris visible),
    micro-rayures et frottements sur UV en mm."""
    m, nt, b = _neuf(nom or f"SP_tete_peinte_{hexa.lstrip('#')}")
    K = _Noeuds(nt, nt.nodes.new("ShaderNodeUVMap").outputs["UV"])
    use = K.op("MULTIPLY", K.arete((0.03, 0.14)), K.plage(K.bruit(2.5, 6.0), (0.5, 0.65)), clamp=True)
    nt.links.new(K.mix(use, srgb(hexa), srgb("#8a8c8f")), b.inputs["Base Color"])
    nt.links.new(use, b.inputs["Metallic"])
    micro = K.carte("micro_rayures", 9.0, 0.21, (0.4, 0.9)); frot = K.carte("frottements", 17.0, 0.47, (0.2, 0.85))
    rug = K.op("ADD", rugo, K.op("ADD", K.op("MULTIPLY", micro, 0.1), K.op("MULTIPLY", frot, 0.08)))
    nt.links.new(K.op("SUBTRACT", rug, K.op("MULTIPLY", use, 0.15), clamp=True), b.inputs["Roughness"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.08; bp.inputs["Distance"].default_value = 0.01
    nt.links.new(K.bruit(3.0, 2.0), bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])   # peau d'orange
    m.diffuse_color = srgb(hexa)
    return bevel_tete(m, bevel) if bevel else m


def laiton(nom="SP_laiton"):
    """Inserts filetés à chaud en laiton (CuZn37) : métal jaune, réflectance du laiton, légèrement terni (rugosité 0,22 à 0,34)."""
    m, nt, b = _neuf(nom)
    b.inputs["Base Color"].default_value = (0.86, 0.66, 0.34, 1.0); b.inputs["Metallic"].default_value = 1.0
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 2.0; nz.inputs["Detail"].default_value = 3.0; nz.inputs["Roughness"].default_value = 0.5
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.clamp = False                      # comme photoreal._plage (sans borne)
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = 0.3, 0.7
    mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 0.22, 0.34
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"]); nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])
    m.diffuse_color = (0.86, 0.66, 0.34, 1.0)
    return m


MATIERES = {"inox": inox_naturel, "oxyde": acier_oxyde_noir, "laiton": laiton}
