r"""Catalogue des matières : une fiche par matière (procédé, teinte visée, base compensée et pour quel studio, valeurs physiques,
grain, rayon de Bevel, source, date, décision de Lou) et sa fonction de construction.
    from material_library.matieres import catalogue as CAT
    m = CAT.construire("peinture_fs36118")          # matière « SP_peinture_FS36118_satinee », nœud Bevel compris
Règles de Lou : teinte et rugosité uniformes, le grain est en RELIEF seul ; matières d'après la construction réelle du matériau
et des valeurs mesurées ; la teinte vue par Lou prime sur les photos ; base compensée à la pipette dans le studio (couleurs.py).
Les looks de fabrication (couches FDM, plateau texturé, ponçage, gravure laser…) ne sont pas ici : matieres/procedes.py.
Repris de MFS le 2026-10-27 : photoreal.py (nylon_pa12_noir, bumpon_noir, pvc_noir, alu_brosse_encre) et maquette_grand_format.py
(peinture_acrylique, mat_uniforme, MATIERES_FACADE, MATIERES_CAISSON, pla_imprimeur, resine_9600_mate, GF_acrylique_fume) ; la
visserie (inox, acier oxydé, laiton) vit dans visserie/shading.py (chunk-05), le catalogue y renvoie."""
from . import noeuds as N
from .couleurs import hexa, srgb

STUDIO = "site"          # studio de référence des bases compensées : G:\Blender\MFS\plans_fixes\site\hero.blend (studio.blend lié)


# ------------------------------------------------------------------ fonctions de construction (lisent la fiche)
def _rugosite(nt, b, f):
    r = f.get("rugosite", 0.5)
    if isinstance(r, tuple):              # (min, max, échelle 1/mm) : brillance qui varie doucement (pièces validées dans MFS)
        nt.links.new(N.plage(nt, N.bruit(nt, r[2], 3.0).outputs["Fac"], r[0], r[1]), b.inputs["Roughness"])
    else:
        b.inputs["Roughness"].default_value = r


def uniforme(f):
    """Teinte et rugosité uniformes, grain en relief seul (mat_uniforme de la maquette) ; voile (sheen), diffusion, transmission."""
    m, nt, b = N.neuf(f["matiere"])
    b.inputs["Base Color"].default_value = srgb(f["base"]); _rugosite(nt, b, f)
    b.inputs["Metallic"].default_value = f.get("metal", 0.0); b.inputs["IOR"].default_value = f.get("ior", 1.5)
    b.inputs["Transmission Weight"].default_value = f.get("transmission", 0.0)
    if f.get("voile"): b.inputs["Sheen Weight"].default_value = f["voile"]; b.inputs["Sheen Roughness"].default_value = 0.6
    if f.get("speculaire") is not None: b.inputs["Specular IOR Level"].default_value = f["speculaire"]
    if f.get("diffusion"):                # (poids, rayon RGB, échelle mm) : lumière qui s'arrondit dans les bords
        w, rayon, ech = f["diffusion"]
        b.inputs["Subsurface Weight"].default_value = w; b.inputs["Subsurface Radius"].default_value = rayon
        b.inputs["Subsurface Scale"].default_value = ech
    if f.get("grain"):                    # (pas mm, amplitude mm, détail)
        pas, amp, det = f["grain"]; N.ondulation(nt, b, ((1 / pas, amp, det),), 1.0)
    m.diffuse_color = srgb(f["base"]); return m


def peinture_grain_net(f):
    """Peinture satinée sur acrylique coulé (peinture_acrylique de la maquette, Lou 2026-10-27 : « assez lisse mais un léger
    grain », puis « accentue le grain, effet résine huilée », « un grain sharp, un noise avec plus de roughness ») : grain net
    (bruit à Roughness 0,8 au pas de 0,07, contraste resserré 0,3 → 0,7, hauteur 0 → 0,016 mm) + peau d'orange douce (≈ 1,7 mm,
    ± 3 µm) ; teinte uniforme, relief seul."""
    m, nt, b = N.neuf(f["matiere"])
    b.inputs["Base Color"].default_value = srgb(f["base"]); b.inputs["Roughness"].default_value = f["rugosite"]
    b.inputs["Sheen Weight"].default_value = f["voile"]; b.inputs["Sheen Roughness"].default_value = 0.6
    pas, haut = f["grain"][:2]
    gr = nt.nodes.new("ShaderNodeMapRange"); gr.clamp = True
    gr.inputs["From Min"].default_value, gr.inputs["From Max"].default_value = 0.3, 0.7
    gr.inputs["To Min"].default_value, gr.inputs["To Max"].default_value = 0.0, haut
    nt.links.new(N.bruit(nt, 1 / pas, 3.0, 0.8).outputs["Fac"], gr.inputs["Value"])
    pe = nt.nodes.new("ShaderNodeMapRange")                                                       # peau d'orange douce
    pe.inputs["To Min"].default_value, pe.inputs["To Max"].default_value = -0.003, 0.003
    nt.links.new(N.bruit(nt, 0.6, 2.0, 0.55).outputs["Fac"], pe.inputs["Value"])
    somme = nt.nodes.new("ShaderNodeMath"); somme.operation = "ADD"
    nt.links.new(gr.outputs["Result"], somme.inputs[0]); nt.links.new(pe.outputs["Result"], somme.inputs[1])
    N.relief(nt, b, somme.outputs[0], 1.0, 1.0)
    m.diffuse_color = srgb(f["base"]); return m


def caoutchouc(f):
    """Polyuréthane / PVC noir mat un peu gras (bumpon_noir, pvc_noir de photoreal) : brillance qui varie, voile, réflexion
    spéculaire réduite (noir profond même sous l'HDRI des reflets), grain fin en relief (Bump direct, force `grain[1]`)."""
    m, nt, b = N.neuf(f["matiere"])
    b.inputs["Base Color"].default_value = srgb(f["base"]); _rugosite(nt, b, f)
    b.inputs["Sheen Weight"].default_value = f["voile"]; b.inputs["Sheen Roughness"].default_value = 0.5
    b.inputs["Specular IOR Level"].default_value = 0.3
    ech, force = f["grain"][:2]
    N.relief(nt, b, N.bruit(nt, ech, 3.0, 0.6).outputs["Fac"], force, 0.01)
    m.diffuse_color = srgb(f["base"]); return m


def alu_brosse(f):
    """Aluminium déposé sous vide, brossé, sous pelliculage PET brillant (étiquette StickerApp « Brushed Alloy », photoreal
    alu_brosse_encre sans l'encre) : F0 0,913, teinte de bord 0,96, anisotropie 0,85 le long de U (UV de l'objet), micro-rayures
    de quelques µm, coat IOR 1,64 lisse (sa normale ne suit pas le brossage)."""
    m, nt, b = N.neuf(f["matiere"])
    b.inputs["Base Color"].default_value = (0.913, 0.922, 0.924, 1.0); b.inputs["Metallic"].default_value = 1.0
    b.inputs["Specular Tint"].default_value = (0.96, 0.965, 0.97, 1.0)
    b.inputs["Roughness"].default_value = 0.3; b.inputs["Anisotropic"].default_value = 0.85
    tg = nt.nodes.new("ShaderNodeTangent"); tg.direction_type = "UV_MAP"; nt.links.new(tg.outputs["Tangent"], b.inputs["Tangent"])
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (3.0 / 62.0, 1400.0 / 25.0, 1.0)        # rayures de l'étiquette (62 × 25, UV 0..1), en mm
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.0; nz.inputs["Detail"].default_value = 5.0
    nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    N.relief(nt, b, nz.outputs["Fac"], 1.0, 0.0015)
    b.inputs["Coat Weight"].default_value = 1.0; b.inputs["Coat IOR"].default_value = 1.64; b.inputs["Coat Roughness"].default_value = 0.02
    m.diffuse_color = (0.75, 0.76, 0.77, 1); return m


def _visserie(fonction):
    """Matière de la visserie (chunk-05, visserie/shading.py) : une seule vérité, le catalogue y renvoie."""
    def fabrique(f):
        from ..visserie import shading
        fn = getattr(shading, fonction)
        return fn(f["matiere"], bevel=f["bevel"]) if f.get("bevel") else fn(f["matiere"])
    return fabrique


# ------------------------------------------------------------------ fiches
# champs : titre, famille (catalogue de l'Asset Browser), procede, matiere (nom Blender), fabrique, cible (teinte visée : vue par
# Lou ou norme ; None si seul le rendu validé fait foi), base (base compensée pour STUDIO), rugosite, metal, ior, voile,
# transmission, diffusion, grain (pas mm, amplitude mm, détail), bevel (mm, aretes.RAYONS), source, date, decision
CATALOGUE = {
    # ---------------------------------------------------------------- peintures
    "peinture_fs36118": dict(
        titre="Peinture acrylique satinée gris FS 595 36118", famille="Peintures", fabrique=peinture_grain_net,
        procede="acrylique coulé découpé au laser, peint (plaque « jour / nuit »)", matiere="SP_peinture_FS36118_satinee",
        cible="#5C6169", base="#3b3f45", rugosite=0.40, voile=0.08, grain=(0.07, 0.016, 3.0), bevel=0.4,
        source="FS 595 36118 (#5C6169) ; base compensée à la pipette dans le studio du site : #3b3f45 rend #5f656c (MFS, rendu de "
               "face du F-COM2) ; grain calé sur le caisson SLA poncé huilé ; sur la pastille de la bibliothèque (planche_matieres) "
               "#3b3f45 rend #646a71 (la base compensée y serait #363940, rend #5f646c) ; la vue de face de MFS reste la référence",
        base_pastille="#363940", date="2026-10-27",
        decision="Lou : façade de la réplique en acrylique « jour / nuit » peint au gris FS 36118, satinée, grain net ; base "
                 "#3b3f45 validée dans MFS gardée (2026-10-27)"),
    # ---------------------------------------------------------------- résines (SLA)
    "sla_jlc_black": dict(
        titre="Résine SLA JLC Black poncée huilée", famille="Résines", fabrique=uniforme, procede="SLA JLC3DP, poncée, huilée",
        matiere="SP_SLA_JLC_Black_huilee", cible=None, base="#121214", rugosite=0.35, grain=(0.08, 0.015, 2.0), bevel=0.25,
        source="catalogue JLC3DP du 2026-10-26 ; réglée sur rendus (MFS, étude des matières JLC)", date="2026-10-26",
        decision="Lou : caisson du F-COM2 en SLA JLC Black poncée huilée (≈ 13 $ le caisson, devis estimé)"),
    "sla_jlc_grey": dict(
        titre="Résine SLA Grey poncée", famille="Résines", fabrique=uniforme, procede="SLA JLC3DP, poncée",
        matiere="SP_SLA_JLC_Grey", cible=None, base="#7f8285", rugosite=0.50, grain=(0.08, 0.02, 2.0), bevel=0.25,
        source="catalogue JLC3DP du 2026-10-26 (candidate de façade, lettres gravées ton sur ton)", date="2026-10-26",
        decision="candidate non retenue (façade ≈ 5,3 $)"),
    "resine_9600_blanche": dict(
        titre="Résine SLA 9600 blanche brute", famille="Résines", fabrique=uniforme, procede="SLA JLC3DP 9600, brute",
        matiere="SP_resine_9600_mate", cible=None, base="#e8e6e0", rugosite=0.45, grain=(0.08, 0.02, 2.0),
        diffusion=(1.0, (1.0, 0.82, 0.62), 0.15), bevel=0.25,
        source="photo de Lou (2026-10-15) ; Lou 2026-10-26 : sur une vraie pièce en résine, ni la teinte ni la rugosité ne "
               "varient, seulement un grain fin ; diffusion réduite (0,15) pour que les cannelures se lisent", date="2026-10-26",
        decision="Lou : molette du F-COM1 en résine 9600 blanche brute, sans traitement brillant"),
    # ---------------------------------------------------------------- PLA (la matière ; les couches FDM sont un procédé)
    "pla_noir": dict(
        titre="PLA noir", famille="Impression FDM", fabrique=uniforme, procede="FDM (Snapmaker U1 de l'imprimeur FDM) : voir procedes.fdm",
        matiere="SP_PLA_noir", cible=None, base="#18181a", rugosite=0.32, ior=1.46, bevel=0.3,
        source="pla_imprimeur de la maquette du F-COM2", date="2026-10-27",
        decision="Lou : petites pièces faciles à imprimer chez l'imprimeur FDM, en PLA noir"),
    "pla_blanc": dict(
        titre="PLA blanc (jamais de blanc absolu)", famille="Impression FDM", fabrique=uniforme, procede="FDM : voir procedes.fdm",
        matiere="SP_PLA_blanc", cible=None, base="#c9c7c1", rugosite=0.30, ior=1.46, bevel=0.3,
        source="lettres blanches de la façade U1 (MFS, 2026-10-26)", date="2026-10-26",
        decision="Lou : jamais de blanc absolu"),
    "pla_naturel": dict(
        titre="PLA naturel translucide", famille="Impression FDM", fabrique=uniforme, procede="FDM : voir procedes.fdm",
        matiere="SP_PLA_naturel", cible=None, base=hexa((0.86, 0.84, 0.78)), rugosite=0.35, ior=1.46, transmission=0.5, bevel=0.3,
        source="GF_PLA_naturel de la maquette du F-COM2 (guides de lumière)", date="2026-10-27", decision=""),
    # ---------------------------------------------------------------- nylon (fusion de poudre)
    "nylon_pa12_noir": dict(
        titre="Nylon PA12 MJF teint noir", famille="Nylon", fabrique=uniforme, procede="MJF / SLS JLC3DP, teint noir",
        matiere="SP_nylon_PA12_noir", cible=None, base="#1f2022", rugosite=(0.72, 0.86, 0.6), ior=1.53, voile=0.15,
        grain=(0.14, 0.08, 2.0), bevel=0.25,
        source="pièces MJF reçues de JLC3DP (photo de Lou du 2026-10-22) ; grain réglé par Lou dans le viewer (tuile 0,14, relief "
               "0,71) puis relief doublé sur le rendu", date="2026-10-25",
        decision="Lou : noir un peu gris, teinte uniforme (aucun bruit de couleur), grain fin en relief seul"),
    "nylon_pa12s_noir": dict(
        titre="Nylon PA12S MJF noir (grain plus fin)", famille="Nylon", fabrique=uniforme, procede="MJF JLC3DP",
        matiere="SP_MJF_PA12S_noir", cible=None, base="#1f2022", rugosite=0.78, voile=0.12, grain=(0.10, 0.05, 2.0), bevel=0.25,
        source="catalogue JLC3DP du 2026-10-26", date="2026-10-26", decision="candidate de caisson (≈ 29 $)"),
    "sls_3201pa_f": dict(
        titre="Nylon SLS 3201PA-F gris-noir", famille="Nylon", fabrique=uniforme, procede="SLS JLC3DP",
        matiere="SP_SLS_3201PA_F", cible=None, base="#2b2c2e", rugosite=0.86, voile=0.15, grain=(0.18, 0.10, 2.0), bevel=0.25,
        source="catalogue JLC3DP du 2026-10-26", date="2026-10-26", decision="candidate de caisson (≈ 19 $), plus granuleuse"),
    # ---------------------------------------------------------------- métaux
    "inox_a2": dict(
        titre="Inox A2 naturel (vis)", famille="Métaux", fabrique=_visserie("inox_naturel"), procede="visserie du commerce",
        matiere="SP_inox_A2", cible=None, base="#c3c5c7", rugosite=0.2, metal=1.0, bevel=0.2,
        source="visserie/shading.py (chunk-05) ; Lou 2026-10-15 : inox naturel non teinté", date="2026-10-15", decision=""),
    "acier_oxyde_noir": dict(
        titre="Acier oxydé noir usé (vis)", famille="Métaux", fabrique=_visserie("acier_oxyde_noir"), procede="visserie du commerce",
        matiere="SP_acier_oxyde_noir", cible=None, base="#26272a", rugosite=0.4, metal=1.0, bevel=0.2,
        source="visserie/shading.py (chunk-05) ; photo d'un lot de DIN 965 M4 oxydées noires", date="2026-10-27",
        decision="Lou : vis standards, avec imperfections d'après de vraies références"),
    "laiton": dict(
        titre="Laiton CuZn37 (inserts)", famille="Métaux", fabrique=_visserie("laiton"), procede="inserts filetés à chaud",
        matiere="SP_laiton", cible=None, base=hexa((0.86, 0.66, 0.34)), rugosite=(0.22, 0.34, 2.0), metal=1.0, bevel=None,
        source="visserie/shading.py (chunk-05)", date="2026-10-27", decision=""),
    "alu_anodise_gris_fonce": dict(
        titre="Alu 6061 sablé anodisé gris foncé", famille="Métaux", fabrique=uniforme, procede="usinage JLCCNC, sablé, anodisé",
        matiere="SP_alu_anodise_gris_fonce", cible=None, base="#5a5e63", rugosite=0.38, metal=1.0, grain=(0.05, 0.012, 2.0),
        bevel=0.25, source="catalogue JLCCNC du 2026-10-26", date="2026-10-26", decision="candidate de façade (≈ 10–30 $, estimé)"),
    "alu_brosse": dict(
        titre="Alu brossé sous pelliculage (étiquette)", famille="Métaux", fabrique=alu_brosse,
        procede="PET métallisé brossé, pelliculage PET brillant (StickerApp « Brushed Alloy »)", matiere="SP_alu_brosse_pellicule",
        cible=None, base=hexa((0.913, 0.922, 0.924)), rugosite=0.3, metal=1.0, bevel=None,
        source="photoreal.alu_brosse_encre (F0 alu 0,913, PET IOR 1,64)", date="2026-10-16",
        decision="Lou : matériau physiquement précis (couches réelles de l'étiquette)"),
    # ---------------------------------------------------------------- verres, caoutchoucs
    "acrylique_fume": dict(
        titre="Acrylique fumé foncé (≈ 22 % de transmission)", famille="Verres", fabrique=uniforme,
        procede="PMMA coulé teinté, découpé au laser", matiere="SP_acrylique_fume", cible=None,
        base=hexa((0.245, 0.235, 0.225)), rugosite=0.02, ior=1.49, transmission=1.0, bevel=0.2,
        source="teinte 0,24 mesurée dans Cycles : 0,5 → 46 %, 0,25 → 23 % de transmission (MFS, 2026-10-26)", date="2026-10-26",
        decision="Lou : vitre qui cache la colle blanche des segments éteints"),
    "bumpon_noir": dict(
        titre="Patin 3M Bumpon noir (polyuréthane)", famille="Caoutchoucs", fabrique=caoutchouc, procede="patin adhésif du commerce",
        matiere="SP_bumpon_noir", cible=None, base="#111113", rugosite=(0.42, 0.56, 1.2), voile=0.1, grain=(6.0, 0.04), bevel=0.6,
        source="photoreal.bumpon_noir (SJ5076)", date="2026-10-15", decision=""),
    "pvc_noir": dict(
        titre="PVC noir mat (gaine de câble)", famille="Caoutchoucs", fabrique=caoutchouc, procede="extrudé",
        matiere="SP_PVC_noir", cible=None, base="#0f0f10", rugosite=(0.48, 0.6, 0.8), voile=0.08, grain=(4.0, 0.04), bevel=0.2,
        source="photoreal.pvc_noir (câble USB-C)", date="2026-10-15", decision=""),
}


def construire(nom, **changes):
    """Construit la matière de la fiche `nom` (changes : remplace des champs, ex. base= pendant une compensation, matiere= pour
    un autre nom Blender) ; nœud Bevel de la fiche ; la matière garde le nom de sa fiche (propriété « material_library »)."""
    f = dict(CATALOGUE[nom], **changes)
    m = f["fabrique"](f)
    if f.get("bevel"):                     # relançable : reprend un Bevel déjà posé (visserie) au même rayon
        from .. import aretes as AR
        AR.bevel_rendu(m, f["bevel"])
    m["material_library"] = nom
    return m


def fiche(nom):
    return CATALOGUE[nom]


def noms(famille=None):
    return [n for n, f in CATALOGUE.items() if famille is None or f["famille"] == famille]
