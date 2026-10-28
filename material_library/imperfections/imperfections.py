r"""Imperfections de surface (PBR) ajoutées à des matières existantes sans toucher à leurs valeurs physiques. Repris de MFS
(boitier/scripts/imperfections.py, 2026-10-17, Lou : « sur les photos macros on voit que ce n'est pas parfait : dépôt de poussière,
frottements, différents niveaux de roughness… ça doit être PBR »). Cartes de Lou (D:\Blender Assets\Imperfections, préparées en
8 bits 2K par imperfections_cartes.py de MFS), dans les données communes (material_library.DONNEES\imperfections ; à défaut celles de
MFS), projetées en boîte sur les coordonnées objet (mm), remixées entre elles et avec du bruit (taille différente par carte, masques)
pour casser la répétition :
  - rugosité : variation de fond (Megascans), frottements (Smudges_06) et traces de doigts éparses (ATOM 02) plus mates sur les
    surfaces brillantes, grain fin ;
  - métaux : micro-rayures (Micro Scratch) et quelques rayures (ATOM SCRATCH 04), rugosité plus haute ;
  - poussière : couche diélectrique mate gris clair (albédo ~0,55) — grains (ATOM DUST 03), salissure (Dirt_02), quelques peluches,
    voile léger — plus dense dans les recoins (occlusion ambiante) et sur les faces tournées vers le haut (monde).
Sans les cartes : bruits procéduraux seuls. Relançable (nœud « imperfections »). Sur UV en mm (uv_mm.uv_plan_mm) : carte_uv()."""
import os

import bpy

import material_library as SP

from material_library.matieres.couleurs import srgb

CARTES = next((p for p in (os.path.join(SP.DONNEES, "imperfections"), r"G:\Blender\MFS\imperfections") if os.path.isdir(p)),
              os.path.join(SP.DONNEES, "imperfections"))
TUILE = {"fond": 22.0, "frottements": 17.0, "doigts": 60.0, "micro_rayures": 9.0, "rayures": 26.0, "poussiere": 7.0, "salissure": 31.0}   # mm par tuile

SANS = ("CARTE_oled_pixels", "V3_OLED_pixels", "eclate_ligne", "V3_decoupe_rouge", "fond_bleu", "fond_noir", "sol_ombre")   # MFS : émissifs, traits, outils, fonds


def carte_uv(nt, uv, nom, tuile=None, decal=0.0):
    """Carte d'imperfection lue sur des UV en mm (uv_plan_mm), tuile de `tuile` mm (défaut TUILE[nom]), décalée de `decal`
    (tuiles) pour que deux cartes ne se superposent pas : sortie Color, ou None si la carte est absente."""
    f = os.path.join(CARTES, nom + ".png")
    if not os.path.exists(f): return None
    im = bpy.data.images.load(f, check_existing=True); im.colorspace_settings.name = "Non-Color"
    tuile = tuile or TUILE[nom]
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1 / tuile, 1 / tuile, 1.0)
    mp.inputs["Location"].default_value = (decal, decal * 0.7, 0.0); nt.links.new(uv, mp.inputs["Vector"])
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = im; t.interpolation = "Cubic"; nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
    return t.outputs["Color"]

def _op(nt, o, a, b=None, clamp=False):
    x = nt.nodes.new("ShaderNodeMath"); x.operation = o; x.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if v is None: continue
        if isinstance(v, (int, float)): x.inputs[i].default_value = v
        else: nt.links.new(v, x.inputs[i])
    return x.outputs[0]

def _bruit(nt, pos, echelle, detail=3.0, rug=0.55, etire=None):
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = echelle
    n.inputs["Detail"].default_value = detail; n.inputs["Roughness"].default_value = rug
    if etire:
        mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = etire; nt.links.new(pos, mp.inputs["Vector"]); pos = mp.outputs["Vector"]
    nt.links.new(pos, n.inputs["Vector"]); return n.outputs["Fac"]

def _plage(nt, src, de, a, b, lisse=True):
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.clamp = True
    if lisse: mr.interpolation_type = 'SMOOTHSTEP'
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = de
    mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = a, b
    nt.links.new(src, mr.inputs["Value"]); return mr.outputs["Result"]

def _carte(nt, coord, nom):
    """Carte d'imperfection projetée en boîte (coordonnées objet en mm, tuile de TUILE[nom] mm), ou None si absente."""
    f = os.path.join(CARTES, nom + ".png")
    if not os.path.exists(f): return None
    im = bpy.data.images.load(f, check_existing=True); im.colorspace_settings.name = 'Non-Color'
    mp = nt.nodes.new("ShaderNodeMapping"); k = 1.0 / TUILE[nom]; mp.inputs["Scale"].default_value = (k, k, k)
    mp.inputs["Location"].default_value = (hash(nom) % 97 / 97, hash(nom) % 89 / 89, 0)
    nt.links.new(coord, mp.inputs["Vector"])
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = im; t.projection = 'BOX'; t.projection_blend = 0.3; t.interpolation = 'Cubic'
    nt.links.new(mp.outputs["Vector"], t.inputs["Vector"]); return t.outputs["Color"]

def _matiere(m, force):
    nt = m.node_tree; bsdfs = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED']
    out = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output), None)
    if not bsdfs or out is None or not out.inputs["Surface"].links: return
    geo = nt.nodes.new("ShaderNodeNewGeometry"); geo.name = "imperfections"; pos = geo.outputs["Position"]
    obj = nt.nodes.new("ShaderNodeTexCoord").outputs["Object"]
    c = {n: _carte(nt, obj, n) for n in TUILE}
    # rugosité : taches de frottement (~3 mm), grain fin (~0,2 mm), micro-rayures (métaux)
    tache = _plage(nt, _bruit(nt, pos, 0.35, 4.0), (0.52, 0.72), 0.0, 1.0)
    if c["frottements"]: tache = _op(nt, 'MULTIPLY', _op(nt, 'ADD', tache, 0.35), _plage(nt, c["frottements"], (0.15, 0.85), 0.0, 1.0, lisse=False))
    if c["doigts"]:                                           # traces de doigts éparses : une sur trois environ
        tache = _op(nt, 'MAXIMUM', tache, _op(nt, 'MULTIPLY', _plage(nt, c["doigts"], (0.2, 0.8), 0.0, 1.0), _plage(nt, _bruit(nt, pos, 0.05), (0.5, 0.6), 0.0, 1.0)))
    grain = _plage(nt, _bruit(nt, pos, 5.0, 2.0), (0.3, 0.7), -1.0, 1.0, lisse=False)
    if c["fond"]: grain = _op(nt, 'ADD', _op(nt, 'MULTIPLY', grain, 0.5), _plage(nt, c["fond"], (0.2, 0.8), -1.0, 1.0, lisse=False))
    onde = nt.nodes.new("ShaderNodeTexWave"); onde.wave_type = 'BANDS'; onde.inputs["Scale"].default_value = 0.9
    onde.inputs["Distortion"].default_value = 9.0; onde.inputs["Detail"].default_value = 4.0; nt.links.new(pos, onde.inputs["Vector"])
    rayure = _op(nt, 'MULTIPLY', _plage(nt, onde.outputs["Fac"], (0.92, 0.99), 0.0, 1.0), _plage(nt, _bruit(nt, pos, 0.8), (0.5, 0.65), 0.0, 1.0))
    if c["micro_rayures"]: rayure = _op(nt, 'MAXIMUM', rayure, _op(nt, 'MULTIPLY', _plage(nt, c["micro_rayures"], (0.35, 0.9), 0.0, 1.0), 0.6))
    if c["rayures"]: rayure = _op(nt, 'MAXIMUM', rayure, _plage(nt, c["rayures"], (0.25, 0.8), 0.0, 1.0))
    for b in bsdfs:
        metal = b.inputs["Metallic"].default_value if not b.inputs["Metallic"].links else 1.0
        src = b.inputs["Roughness"].links[0].from_socket if b.inputs["Roughness"].links else b.inputs["Roughness"].default_value
        d = _op(nt, 'ADD', _op(nt, 'MULTIPLY', tache, 0.12 * force), _op(nt, 'MULTIPLY', grain, 0.03 * force))
        if metal > 0.5: d = _op(nt, 'ADD', d, _op(nt, 'MULTIPLY', rayure, 0.18 * force))
        nt.links.new(_op(nt, 'ADD', src, d, clamp=True), b.inputs["Roughness"])
    # poussière : grains épars (~0,05 mm) + voile léger, plus dense dans les recoins et vers le haut
    vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 1.4; nt.links.new(pos, vo.inputs["Vector"])
    vo.inputs["Randomness"].default_value = 1.0                                       # grains de 0,03 à 0,07 mm, épars
    grains = _op(nt, 'MULTIPLY', _plage(nt, vo.outputs["Distance"], (0.10, 0.04), 0.0, 1.0), _plage(nt, _bruit(nt, pos, 0.5), (0.52, 0.6), 0.0, 1.0))
    peluche = nt.nodes.new("ShaderNodeTexWave"); peluche.wave_type = 'RINGS'; peluche.inputs["Scale"].default_value = 0.35
    peluche.inputs["Distortion"].default_value = 14.0; peluche.inputs["Detail"].default_value = 3.0; nt.links.new(pos, peluche.inputs["Vector"])
    fils = _op(nt, 'MULTIPLY', _plage(nt, peluche.outputs["Fac"], (0.975, 0.995), 0.0, 1.0), _plage(nt, _bruit(nt, pos, 0.2), (0.71, 0.73), 0.0, 1.0))
    grains = _op(nt, 'MAXIMUM', grains, fils)                                         # quelques fibres de peluche
    if c["poussiere"]: grains = _op(nt, 'MAXIMUM', grains, _plage(nt, c["poussiere"], (0.6, 0.92), 0.0, 1.0))
    if c["salissure"]: grains = _op(nt, 'ADD', grains, _plage(nt, c["salissure"], (0.4, 1.0), 0.0, 0.08))
    voile = _plage(nt, _bruit(nt, pos, 0.15, 3.0), (0.5, 0.8), 0.0, 0.04)   # Lou : « il n'y en a pas autant »
    ao = nt.nodes.new("ShaderNodeAmbientOcclusion"); ao.inputs["Distance"].default_value = 0.6; ao.samples = 8
    recoin = _plage(nt, ao.outputs["AO"], (0.9, 0.3), 0.0, 0.10)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Normal"], sep.inputs[0])
    haut = _plage(nt, sep.outputs["Z"], (-0.2, 1.0), 0.4, 1.0, lisse=False)
    fac = _op(nt, 'MULTIPLY', _op(nt, 'ADD', _op(nt, 'ADD', _op(nt, 'MULTIPLY', grains, 0.5), voile), recoin), _op(nt, 'MULTIPLY', haut, force), clamp=True)
    pou = nt.nodes.new("ShaderNodeBsdfPrincipled"); pou.inputs["Base Color"].default_value = srgb("#c4c0b6")
    pou.inputs["Roughness"].default_value = 0.92; pou.inputs["Sheen Weight"].default_value = 0.3
    mx = nt.nodes.new("ShaderNodeMixShader"); s = out.inputs["Surface"].links[0].from_socket
    nt.links.new(fac, mx.inputs["Fac"]); nt.links.new(s, mx.inputs[1]); nt.links.new(pou.outputs["BSDF"], mx.inputs[2])
    nt.links.new(mx.outputs["Shader"], out.inputs["Surface"])

def appliquer(objets, force=1.0, sans=SANS):
    """Ajoute les imperfections à toutes les matières des objets donnés (une fois par matière), sauf celles nommées dans `sans`."""
    mats = {s.material for o in objets if o.type in ('MESH', 'CURVE') for s in o.material_slots if s.material}
    for m in mats:
        if m.name in sans or not m.use_nodes or "imperfections" in m.node_tree.nodes: continue
        verre = "verre" in m.name or any(n.type == 'BSDF_PRINCIPLED' and n.inputs["Transmission Weight"].default_value > 0.5 for n in m.node_tree.nodes)
        _matiere(m, force * (0.3 if verre else 1.0))          # verres (écran) : à peine, l'affichage reste net
