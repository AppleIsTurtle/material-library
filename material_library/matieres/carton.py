r"""Carton ondulé kraft (cannelure E) et papiers imprimés : matières procédurales, sans répétition, en mm, sur une UV à plat en mm.
    from material_library.matieres import catalogue as CAT
    ext = CAT.construire("carton_e_kraft_ext", masque=chemin_png, masque_cadre=(xmin, ymin, largeur, hauteur))
Méthode, sources et limites : methode/cartons.md. La couche « uv_mm » porte les coordonnées du patron à plat (mm) : fibres et lignes de
cannelure suivent la feuille pliée. L'attribut de point « pli » (0 à 1, optionnel) marque les plis, où le papier blanchit en s'étirant.

Construction réelle : deux couvertures kraft (machine continue : fibres couchées dans le sens de la feuille, marbrure en nuages de la pâte
recyclée, paillettes sombres) collées sur une cannelure ondulée. La cannelure se devine par transparence (lignes au pas de 3,3 mm). L'encre
de flexographie noire ne couvre pas tout : elle boit la couverture et laisse les fibres claires affleurer, bord légèrement baveux."""
import bpy

from . import noeuds as N
from .couleurs import srgb

PAS_CANNELURE = 3.3      # cannelure E : 3,2 à 3,5 mm de pas, ≈ 1,1 mm de haut


def _math(nt, op, a, b=None):
    n = nt.nodes.new("ShaderNodeMath"); n.operation = op
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            nt.links.new(v, n.inputs[i])
    return n.outputs[0]


def _xyz(nt, couche):
    uv = nt.nodes.new("ShaderNodeUVMap"); uv.uv_map = couche
    return uv.outputs["UV"]


def _bruit(nt, vec, echelle, detail=4.0, rugosite=0.55, etire=(1.0, 1.0), decale=0.0):
    """Bruit sur des coordonnées en mm : `echelle` = taille du motif en mm ; etire : (x, y) divise la taille selon l'axe."""
    m = nt.nodes.new("ShaderNodeMapping")
    m.inputs["Scale"].default_value = (etire[0] / echelle, etire[1] / echelle, 1.0)
    m.inputs["Location"].default_value = (decale, decale * 1.7, decale * 0.3)
    nt.links.new(vec, m.inputs["Vector"])
    n = nt.nodes.new("ShaderNodeTexNoise"); n.noise_dimensions = "3D"
    n.inputs["Scale"].default_value = 1.0; n.inputs["Detail"].default_value = detail; n.inputs["Roughness"].default_value = rugosite
    nt.links.new(m.outputs[0], n.inputs["Vector"])
    return n.outputs["Fac"]


def _centre(nt, s, a):
    """Bruit (0..1, centré sur 0,5) → ±a."""
    return N.plage(nt, s, -a, a)


def _paillettes(nt, vec, taille, seuil, force):
    """Paillettes de fibres : Voronoï, 1 dans les petits points ; renvoie une valeur à ajouter (signe de `force`)."""
    v = nt.nodes.new("ShaderNodeTexVoronoi"); v.feature = "F1"; v.inputs["Scale"].default_value = 1 / taille; v.inputs["Randomness"].default_value = 1.0
    nt.links.new(vec, v.inputs["Vector"])
    r = nt.nodes.new("ShaderNodeMapRange"); r.clamp = True
    r.inputs["From Min"].default_value, r.inputs["From Max"].default_value = seuil, seuil * 0.45
    r.inputs["To Min"].default_value, r.inputs["To Max"].default_value = 0.0, force
    nt.links.new(v.outputs["Distance"], r.inputs["Value"])
    return r.outputs["Result"]


def matiere_carton(f):
    """Couverture kraft d'un carton ondulé, avec encre si la fiche a un `masque` (PNG en niveaux de gris, encre = blanc) et son cadre en mm."""
    m, nt, b = N.neuf(f["matiere"])
    vec = _xyz(nt, f.get("couche", "uv_mm"))
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(vec, sep.inputs[0])
    # teinte : marbrure en nuages (photos Packhelp : taches pâles de 10 à 80 mm), fibres couchées selon X, paillettes
    t = _centre(nt, _bruit(nt, vec, 62.0, 3.0, 0.5, decale=f.get("graine", 3.0)), f.get("nuages", 0.03))
    t = _math(nt, "ADD", t, _centre(nt, _bruit(nt, vec, 11.0, 5.0, 0.58, decale=7.1), f.get("nuages", 0.03) * 0.7))
    fibres = _bruit(nt, vec, 1.5, 4.0, 0.62, etire=(1.0, 16.0), decale=2.2)
    t = _math(nt, "ADD", t, _centre(nt, fibres, f.get("fibres_teinte", 0.025)))
    t = _math(nt, "SUBTRACT", t, _paillettes(nt, vec, 2.6, 0.045, f.get("paillettes", 0.10)))
    t = _math(nt, "ADD", t, _paillettes(nt, vec, 3.1, 0.035, f.get("paillettes", 0.10) * 0.5))
    # la cannelure se devine : lignes parallèles à Y, un peu plus claires sur les crêtes
    phase = _math(nt, "ADD", _math(nt, "MULTIPLY", sep.outputs["X"], 6.28318 / PAS_CANNELURE), _centre(nt, _bruit(nt, vec, 40.0, 2.0, 0.5, decale=9.0), 0.5))
    onde = _math(nt, "SINE", phase)
    force_onde = N.plage(nt, _bruit(nt, vec, 34.0, 2.0, 0.5, decale=4.0), 0.25, 1.0)
    t = _math(nt, "ADD", t, _math(nt, "MULTIPLY", _math(nt, "MULTIPLY", onde, force_onde), f.get("cannelure_teinte", 0.006)))
    # plis : le papier blanchit et se fissure en s'étirant
    att = nt.nodes.new("ShaderNodeAttribute"); att.attribute_name = "pli"
    pli = att.outputs["Fac"]
    fissure = N.plage(nt, _bruit(nt, vec, 0.9, 5.0, 0.7, etire=(1.0, 1.0), decale=1.3), 0.0, 1.0, de=(0.42, 0.62))
    t = _math(nt, "ADD", t, _math(nt, "MULTIPLY", _math(nt, "MULTIPLY", pli, fissure), f.get("pli_clair", 0.20)))
    val = _math(nt, "ADD", t, 1.0)
    coul = nt.nodes.new("ShaderNodeVectorMath"); coul.operation = "SCALE"
    coul.inputs[0].default_value = srgb(f["base"])[:3]; nt.links.new(val, coul.inputs["Scale"])
    sortie_coul = coul.outputs[0]
    rug = N.plage(nt, fibres, f["rugosite"] - 0.05, f["rugosite"] + 0.05)
    # relief en vraie hauteur (mm) : fibres, grain, lignes de cannelure
    h = _centre(nt, fibres, f.get("h_fibres", 0.008))
    h = _math(nt, "ADD", h, _centre(nt, _bruit(nt, vec, 0.45, 4.0, 0.6, decale=5.5), 0.005))
    h = _math(nt, "ADD", h, _math(nt, "MULTIPLY", _math(nt, "MULTIPLY", onde, force_onde), f.get("h_cannelure", 0.012)))
    h = _math(nt, "ADD", h, _math(nt, "MULTIPLY", _math(nt, "MULTIPLY", pli, fissure), -0.02))
    # encre
    if f.get("masque"):
        x0, y0, W, H = f["masque_cadre"]
        # bord baveux : coordonnées poussées de ± 0,05 mm par les fibres
        pousse = _centre(nt, _bruit(nt, vec, 0.35, 3.0, 0.6, decale=8.8), 0.05)
        u = _math(nt, "DIVIDE", _math(nt, "SUBTRACT", _math(nt, "ADD", sep.outputs["X"], pousse), x0), W)
        v = _math(nt, "SUBTRACT", 1.0, _math(nt, "DIVIDE", _math(nt, "SUBTRACT", _math(nt, "ADD", sep.outputs["Y"], pousse), y0), H))
        cv = nt.nodes.new("ShaderNodeCombineXYZ"); nt.links.new(u, cv.inputs[0]); nt.links.new(v, cv.inputs[1])
        ti = nt.nodes.new("ShaderNodeTexImage"); ti.extension = "CLIP"; ti.interpolation = "Cubic"
        ti.image = bpy.data.images.load(f["masque"], check_existing=True); ti.image.colorspace_settings.name = "Non-Color"
        nt.links.new(cv.outputs[0], ti.inputs["Vector"])
        # l'encre boit la couverture : les fibres claires affleurent
        couvre = N.plage(nt, fibres, f.get("encre_min", 0.88), 1.0, de=(0.34, 0.5))
        a = nt.nodes.new("ShaderNodeMath"); a.operation = "MULTIPLY"; a.use_clamp = True
        nt.links.new(ti.outputs["Color"], a.inputs[0]); nt.links.new(couvre, a.inputs[1])
        mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
        nt.links.new(a.outputs[0], mix.inputs["Factor"]); nt.links.new(sortie_coul, mix.inputs[6])
        mix.inputs[7].default_value = srgb(f.get("encre", "#14110f"))
        sortie_coul = mix.outputs[2]
        rug = _math(nt, "SUBTRACT", rug, _math(nt, "MULTIPLY", a.outputs[0], f["rugosite"] - f.get("encre_rugosite", 0.72)))
        h = _math(nt, "ADD", h, _math(nt, "MULTIPLY", a.outputs[0], 0.004))
        libre = _math(nt, "SUBTRACT", 1.0, a.outputs[0])
        nt.links.new(_math(nt, "MULTIPLY", f.get("voile", 0.25), libre), b.inputs["Sheen Weight"])
        # l'encre de flexographie reste mate : peu de reflet, sinon elle vire au brun sous un studio
        nt.links.new(_math(nt, "ADD", 0.08, _math(nt, "MULTIPLY", 0.42, libre)), b.inputs["Specular IOR Level"])
    nt.links.new(sortie_coul, b.inputs["Base Color"]); nt.links.new(rug, b.inputs["Roughness"])
    if not f.get("masque"):
        b.inputs["Sheen Weight"].default_value = f.get("voile", 0.25)
    b.inputs["Sheen Roughness"].default_value = 0.7
    N.relief(nt, b, h, 1.0, 1.0)
    m.diffuse_color = srgb(f["base"]); return m


def matiere_tranche(f):
    """Tranche et cannelure : papier recyclé plus gris, sans encre, fibres courtes."""
    m, nt, b = N.neuf(f["matiere"])
    tc = nt.nodes.new("ShaderNodeTexCoord"); vec = tc.outputs["Object"]
    t = _centre(nt, _bruit(nt, vec, 2.2, 5.0, 0.6, decale=1.0), 0.14)
    val = _math(nt, "ADD", t, 1.0)
    coul = nt.nodes.new("ShaderNodeVectorMath"); coul.operation = "SCALE"
    coul.inputs[0].default_value = srgb(f["base"])[:3]; nt.links.new(val, coul.inputs["Scale"])
    nt.links.new(coul.outputs[0], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = f["rugosite"]
    b.inputs["Sheen Weight"].default_value = f.get("voile", 0.3); b.inputs["Sheen Roughness"].default_value = 0.8
    N.relief(nt, b, _centre(nt, _bruit(nt, vec, 0.3, 4.0, 0.6, decale=3.0), 0.02), 1.0, 1.0)
    m.diffuse_color = srgb(f["base"]); return m


def matiere_papier(f):
    """Papier imprimé : image (UV 0..1 de l'objet) sur un papier non couché (fibres fines) ou pelliculé mat (`pellicule`)."""
    m, nt, b = N.neuf(f["matiere"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    if f.get("image"):
        ti = nt.nodes.new("ShaderNodeTexImage"); ti.image = bpy.data.images.load(f["image"], check_existing=True); ti.interpolation = "Cubic"
        nt.links.new(tc.outputs["UV"], ti.inputs["Vector"]); nt.links.new(ti.outputs["Color"], b.inputs["Base Color"])
    else:
        b.inputs["Base Color"].default_value = srgb(f["base"])
    b.inputs["Roughness"].default_value = f["rugosite"]
    b.inputs["Sheen Weight"].default_value = f.get("voile", 0.12); b.inputs["Sheen Roughness"].default_value = 0.7
    N.relief(nt, b, _centre(nt, _bruit(nt, tc.outputs["Object"], f.get("grain", 0.5), 4.0, 0.6), f.get("h_grain", 0.004)), 1.0, 1.0)
    m.diffuse_color = srgb(f["base"]); return m
