r"""Looks par procédé de fabrication : une pièce prend l'aspect de sa vraie fabrication en une ligne ; la matière vient du
catalogue (catalogue.py), le procédé ajoute ce que la fabrication laisse (couches, plateau, ponçage, poudre, gravure…).
    from material_library.matieres import procedes as PR
    PR.poser(ob, PR.fdm("pla_noir", buse=0.4, axe="Y", plateau="-Y"))     # l'imprimeur FDM : couches de 0,2 le long de y, face -y sur le plateau texturé
    PR.poser(ob, PR.sla("sla_jlc_black", "poncee_huilee"))
    PR.poser(ob, PR.mjf("nylon_pa12_noir"))
    PR.poser(ob, PR.acrylique_laser("peinture_fs36118", masque=np.load(npz)))   # « jour / nuit » : nœud force_lettres (0 le jour)
    PR.poser(ob, PR.metal("alu_anodise_gris_fonce"))
Vrais trajets de la buse (feature fdm-trajets) : PR.trajets(ob, "trajets.npz") après PR.fdm(), avec les trajets simulés par
impression/tranchage.py pour ce maillage — ou, plus simple, matieres/reglages_fdm.imprimer(ob, …) (panneau « Impression FDM ») ;
sans trajets, fdm() garde des couches procédurales le long de `axe` (matière glissée depuis la bibliothèque). Lettres imprimées
dans la masse (impression/lettres.py) : lettres_imprimees(). Règles : methode/procedes.md, methode/fdm_trajets.md.
L'orientation d'impression (axe, plateau) est un paramètre de la pièce, jamais une constante.
Repris de MFS le 2026-10-27 : photoreal.pla_fdm / couches_fdm, maquette_grand_format (mat_uniforme plateau=, pla_imprimeur,
lettres_imprimees, lettres_gravees, MATIERES_FACADE / CAISSON)."""
import math
import os

import bpy

from .. import aretes as AR
from . import catalogue as CAT
from . import noeuds as N
from .couleurs import srgb

# réglages courants du trancheur pour les buses de l'imprimeur FDM (Snapmaker U1) : hauteur de couche, largeur de cordon (mm)
BUSES = {0.4: dict(couche=0.2, cordon=0.45), 0.2: dict(couche=0.1, cordon=0.22)}
# finitions SLA (JLC3DP) : rugosité, grain (pas mm, amplitude mm, détail)
SLA = {"poncee_huilee": dict(rugosite=0.35, grain=(0.08, 0.015, 2.0)),    # JLC Black poncée huilée (choix de Lou, 2026-10-26)
       "poncee": dict(rugosite=0.50, grain=(0.08, 0.02, 2.0)),            # ponçage standard inclus (SLA Grey)
       "brute": dict(rugosite=0.45, grain=(0.08, 0.02, 2.0)),             # 9600 brute (molette du F-COM1)
       "lisse": dict(rugosite=0.25, grain=(0.05, 0.004, 2.0))}            # sortie de bac nettoyée : ESTIMÉE, sans photo


def poser(ob, m):
    """La matière m sur toutes les faces de ob (un seul emplacement)."""
    ob.data.materials.clear(); ob.data.materials.append(m)
    return ob


def _op(nt, o, a, b=None):
    x = nt.nodes.new("ShaderNodeMath"); x.operation = o
    for k, v in enumerate((a, b)):
        if v is None: continue
        if isinstance(v, (int, float)): x.inputs[k].default_value = v
        else: nt.links.new(v, x.inputs[k])
    return x.outputs[0]


def _sous_relief(nt, b, bump):
    """Insère `bump` au pied de la chaîne de relief du BSDF b (sous les Bump existants, au-dessus d'un Bevel) : les reliefs
    s'additionnent."""
    entree = b.inputs["Normal"]
    while entree.is_linked and entree.links[0].from_node.type == "BUMP":
        entree = entree.links[0].from_node.inputs["Normal"]
    if entree.is_linked:                                   # Bevel (ou autre normale) : passe sous le nouveau Bump
        nt.links.new(entree.links[0].from_socket, bump.inputs["Normal"])
    nt.links.new(bump.outputs["Normal"], entree)
    return bump


def _bsdf(m):
    return next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


# ------------------------------------------------------------------ FDM (imprimeur FDM)
def _couches(nt, axe, couche):
    """Hauteur des lignes de couches (photoreal.pla_fdm) : fil écrasé (bosse arrondie) le long de `axe`, couches pas tout à fait
    droites (± 0,03), fil plus ou moins régulier."""
    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.name = "couches_fdm"
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
    t = _op(nt, "ADD", sep.outputs[axe.upper()], _op(nt, "MULTIPLY", _op(nt, "SUBTRACT", N.bruit(nt, 0.8, 2.0).outputs["Fac"], 0.5), 0.06))
    bosse = _op(nt, "POWER", _op(nt, "ABSOLUTE", _op(nt, "SINE", _op(nt, "MULTIPLY", _op(nt, "DIVIDE", t, couche), math.pi))), 0.6)
    return _op(nt, "MULTIPLY", bosse, N.plage(nt, N.bruit(nt, 1.5, 3.0).outputs["Fac"], 0.75, 1.0))


def fdm(matiere="pla_noir", buse=0.4, couche=None, axe="Y", plateau=None, translucide=0.0, nom=None, grain="fin"):
    """PLA imprimé par dépôt de fil (Snapmaker U1 de l'imprimeur FDM) : la teinte et la rugosité de la fiche `matiere` ; IOR 1,46 ;
    brillance qui varie (rugosité - 0,08 … + 0,04) ; lignes de couches de `couche` mm (défaut : celle de la buse) le long de
    l'axe d'impression `axe` de la pièce — elles n'apparaissent que sur les flancs ; épaisseur de couche et de fil un peu
    irrégulières ; teinte UNIFORME (Lou, 2026-10-28 : « noise trop intense sur la diffuse » ; même règle que le nylon : le grain
    est en relief seulement) ; plateau = face posée sur le plateau texturé (« -Y », « +Z »…) : grain sur cette face seulement,
    `grain` = « fin » ou « granuleux » (GRAINS) ; translucide : diffusion (PLA naturel, guides de lumière)."""
    f = CAT.fiche(matiere); couche = couche or BUSES[buse]["couche"]
    m, nt, b = N.neuf(nom or f"{f['matiere']}_FDM_{str(couche).replace('.', '')}")
    rugo = f["rugosite"] if not isinstance(f["rugosite"], tuple) else sum(f["rugosite"][:2]) / 2
    bp = N.relief(nt, b, _couches(nt, axe, couche), 1.0, 0.025 * couche / 0.2); bp.name = "couches_fdm_relief"   # éteint par trajets()
    b.inputs["Base Color"].default_value = srgb(f["base"])
    nt.links.new(N.plage(nt, N.bruit(nt, 0.5, 3.0).outputs["Fac"], rugo - 0.08, rugo + 0.04), b.inputs["Roughness"])
    b.inputs["IOR"].default_value = 1.46
    if f.get("transmission"): b.inputs["Transmission Weight"].default_value = f["transmission"]
    if translucide:
        b.inputs["Subsurface Weight"].default_value = translucide; b.inputs["Subsurface Scale"].default_value = 0.35
        b.inputs["Subsurface Radius"].default_value = (1.0, 0.9, 0.7)
    if plateau: plateau_texture(m, plateau, grain=grain)
    m.diffuse_color = srgb(f["base"]); m["material_library"] = matiere; m["procede"] = f"FDM buse {buse}, couches {couche}, axe {axe}"
    return AR.bevel_rendu(m, f.get("bevel") or AR.RAYONS["pla"])


def couches(materiaux, couche=0.2, axe="Y", distance=0.025):
    """Ajoute seulement le relief des lignes de couches (même calcul que fdm) à des matières existantes, sans les reconstruire
    (photoreal.couches_fdm : site.blend, où Lou règle les matières). Relançable (nœud « couches_fdm »)."""
    for m in materiaux:
        if not m or m.library or not m.node_tree or "couches_fdm" in m.node_tree.nodes: continue
        nt = m.node_tree; h = _couches(nt, axe, couche)
        for b in [n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"]:
            bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 1.0; bp.inputs["Distance"].default_value = distance
            nt.links.new(h, bp.inputs["Height"]); _sous_relief(nt, b, bp)


# grains de plateau (tuile mm, hauteur ± mm, détail et rugosité du bruit) : « fin » = PEI poudré fin (défaut, sans taches au
# gros plan) ; « granuleux » = plaque d'impression granuleuse du F-COM1 (photo de Lou du 2026-10-26, ancienne façade U1 de la
# maquette : cellules de 0,35, ± 0,05), voulue pour la façade noire du F-COM2 (Lou, 2026-10-28)
GRAINS = {"fin": (0.06, 0.003, 1.0, 0.4), "granuleux": (0.35, 0.05, 2.0, 0.55)}


def plateau_texture(m, face="-Y", tuile=None, amp=None, grain="fin"):
    """Grain du plateau texturé sur la seule face posée dessus (normale objet le long de `face`), flancs et chanfreins lisses
    (photo de Lou du 2026-10-26 : grain brillant) : bruit de `tuile` mm, hauteur ± amp mm (défauts : GRAINS[grain]), sans
    variation à grande échelle ; sommets un peu plus brillants. Masque (nœud « plateau_masque ») par la normale seule : trajets()
    le restreint ensuite aux points réellement au contact du plateau (un creux tourné vers le plateau ne l'a jamais touché)."""
    t0, a0, detail, rough = GRAINS[grain]; tuile = tuile or t0; amp = amp or a0
    nt = m.node_tree; b = _bsdf(m)
    grain = _op(nt, "SUBTRACT", N.bruit(nt, 1 / tuile, detail, rough).outputs["Fac"], 0.5)
    grain = _op(nt, "MULTIPLY", grain, 0.35 / 0.2)                               # ± 0,35 environ, comme avant
    somme = _op(nt, "MULTIPLY", grain, amp / 0.35)
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Distance"].default_value = 1.0; nt.links.new(somme, bp.inputs["Height"])
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Normal"], sep.inputs["Vector"])
    s = -1.0 if face.startswith("-") else 1.0
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.name = "plateau_masque"
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = 0.97 * s, 0.995 * s
    nt.links.new(sep.outputs[face[-1].upper()], mr.inputs["Value"]); nt.links.new(mr.outputs["Result"], bp.inputs["Strength"])
    _sous_relief(nt, b, bp)
    ri = b.inputs["Roughness"]                                                    # sommets des grains plus brillants (face seule)
    r0 = ri.links[0].from_socket if ri.is_linked else ri.default_value
    brille = _op(nt, "MULTIPLY", _op(nt, "MULTIPLY", _op(nt, "MAXIMUM", grain, 0.0), 1 / 0.35), mr.outputs["Result"])
    nt.links.new(_op(nt, "MULTIPLY", r0, _op(nt, "SUBTRACT", 1.0, _op(nt, "MULTIPLY", brille, 0.4))), ri)
    return m


# ------------------------------------------------------------------ trajets réels de la buse (feature fdm-trajets, chunk-03)
RELIEF_TRANCHE = 0.22          # creux entre deux couches sur une tranche, en part de la hauteur de couche (0,044 mm en 0,2)
ANISOTROPIE = 0.3              # reflet étiré le long du fil


def _cuire(o, res, sortie):
    """Position ou normale (repère de l'objet) de chaque texel des UV de o, cuite en EMIT par Cycles : tableau (res, res, 4)."""
    import numpy as np
    sc = bpy.context.scene
    img = bpy.data.images.new(f"_cuisson_{sortie}_{o.name}", res, res, float_buffer=True, alpha=True)
    img.generated_color = (0, 0, 0, 0)
    m = bpy.data.materials.new(f"_cuisson_{sortie}"); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    tc = nt.nodes.new("ShaderNodeTexCoord"); em = nt.nodes.new("ShaderNodeEmission"); out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(tc.outputs["Object" if sortie == "pos" else "Normal"], em.inputs["Color"]); nt.links.new(em.outputs[0], out.inputs[0])
    it = nt.nodes.new("ShaderNodeTexImage"); it.image = img; nt.nodes.active = it
    mats = list(o.data.materials); o.data.materials.clear(); o.data.materials.append(m)
    s0 = sc.cycles.samples; sc.cycles.samples = 1
    bpy.ops.object.bake(type="EMIT", margin=4, use_clear=True)
    sc.cycles.samples = s0
    o.data.materials.clear()
    for x in mats: o.data.materials.append(x)
    a = np.empty(res * res * 4, np.float32); img.pixels.foreach_get(a)
    bpy.data.images.remove(img); bpy.data.materials.remove(m)
    return a.reshape(res, res, 4)


def _image(nom, a, chemin=None):
    """Image flottante (Non-Color) depuis un tableau (res, res) ou (res, res, 3) : enregistrée à `chemin` en EXR 16 bits
    compressé (OpenImageIO, livré avec Blender ; Image.save() de Blender l'écrivait en 32 bits sans compression) puis relue,
    sinon empaquetée dans le .blend."""
    import numpy as np
    r = a.shape[0]; img = bpy.data.images.get(nom)
    if img: bpy.data.images.remove(img)
    rgb = np.repeat(a[..., None], 3, -1) if a.ndim == 2 else a
    if chemin:
        import OpenImageIO as oiio
        os.makedirs(os.path.dirname(chemin), exist_ok=True)
        spec = oiio.ImageSpec(r, r, 3, "half"); spec.attribute("compression", "zip")
        out = oiio.ImageOutput.create(chemin); out.open(chemin, spec)
        out.write_image(np.ascontiguousarray(rgb[::-1], dtype=np.float32)); out.close()   # haut de l'image en premier
        img = bpy.data.images.load(chemin); img.name = nom; img.colorspace_settings.name = "Non-Color"
        return img
    img = bpy.data.images.new(nom, r, r, float_buffer=True, alpha=False); img.colorspace_settings.name = "Non-Color"
    rgba = np.ones((r, r, 4), np.float32); rgba[..., :3] = rgb
    img.pixels.foreach_set(rgba.ravel()); img.pack()
    return img


def trajets(o, trajets_npz, res=None, copie=True, dossier=None):
    """Pose sur o les vrais trajets de la buse (simulés par impression/tranchage.py, au format de outils/fdm/gcode.py) :
    UV dépliés, position et normale cuites, cartes calculées par impression/cartes.py (Python système : hauteur des cordons des
    dessus, de la face plateau et des coutures ; direction du fil), puis une copie de la matière de o reçoit : couches des
    tranches calculées dans le shader (vraie première couche, cordon arrondi, couches un peu inégales), relief des cartes,
    reflet étiré le long du fil (anisotropie). Le relief de couches procédural de fdm() est éteint. res : côté des images
    (défaut : ≥ 5 texels par largeur de cordon d'après la surface de la pièce, borné à 256 … 8192). UV dans un jeu à part
    (« UV_fdm » : les autres UV, en mm pour les imperfections, ne bougent pas). copie=False : la matière de o est modifiée sur
    place (recalcul depuis le panneau, la matière vient d'être refaite par fdm()). dossier : cartes enregistrées en EXR
    (<objet>_hauteur.exr, <objet>_fil.exr), sinon empaquetées."""
    import json, subprocess, tempfile
    import numpy as np
    import material_library as SP
    t = dict(np.load(trajets_npz, allow_pickle=True))
    R, org = np.asarray(t["rotation"]), np.asarray(t["origine"])
    reg = json.loads(str(t["reglages"])); h0, h = float(reg["premiere"]), float(reg["couche"])
    wmin = float(np.min(t["largeur"][t["largeur"] > 0]))
    if res is None:
        res = int(min(8192, max(256, math.sqrt(sum(p.area for p in o.data.polygons)) * 5 / wmin * 1.6)))   # petites pièces : 256
    sc = bpy.context.scene
    if o.data.users > 1: o.data = o.data.copy()                                   # maillage partagé : une copie à soi
    uvs = o.data.uv_layers; actif = uvs.active.name if uvs.active else None
    uvs.active = uvs.get("UV_fdm") or uvs.new(name="UV_fdm")
    for x in bpy.context.view_layer.objects: x.select_set(False)
    o.hide_set(False); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.003)
    bpy.ops.object.mode_set(mode="OBJECT")
    moteur = sc.render.engine; sc.render.engine = "CYCLES"
    P, Nn = _cuire(o, res, "pos"), _cuire(o, res, "nor")
    sc.render.engine = moteur
    if actif: uvs.active = uvs[actif]
    nrm = Nn[..., :3] / np.maximum(np.linalg.norm(Nn[..., :3], axis=-1, keepdims=True), 1e-9)
    with tempfile.TemporaryDirectory() as d:
        cu, so = os.path.join(d, "cuisson.npz"), os.path.join(d, "cartes.npz")
        np.savez(cu, P=P[..., :3], N=nrm, masque=P[..., 3] > 0.5); del P, Nn
        script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "impression", "cartes.py")
        r = subprocess.run([SP.PYTHON_SYSTEME, script, cu, trajets_npz, so], capture_output=True, text=True)
        if r.returncode: raise RuntimeError(f"cartes.py : {r.stdout[-1500:]}\n{r.stderr[-1500:]}")
        print("TRAJETS", o.name, res, r.stdout.strip(), flush=True)
        with np.load(so) as c: ch, cf = c["hauteur"].copy(), c["fil"].copy()
    fic = (lambda n: os.path.join(dossier, f"{o.name}_{n}.exr")) if dossier else (lambda n: None)
    ih, ifil = _image(f"SP_hauteur_{o.name}", ch, fic("hauteur")), _image(f"SP_fil_{o.name}", cf, fic("fil")); del ch, cf
    m = o.data.materials[0]
    if copie: m = m.copy(); m.name = f"{o.data.materials[0].name}_{o.name}"; o.data.materials[0] = m
    nt = m.node_tree; b = _bsdf(m)
    if "couches_fdm_relief" in nt.nodes: nt.nodes["couches_fdm_relief"].inputs["Strength"].default_value = 0.0
    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.name = "trajets_fdm"
    up = R[2]                                                                   # axe de montée de l'impression, repère objet

    def dot(sortie):
        v = nt.nodes.new("ShaderNodeVectorMath"); v.operation = "DOT_PRODUCT"; v.inputs[1].default_value = tuple(up)
        nt.links.new(tc.outputs[sortie], v.inputs[0]); return v.outputs["Value"]
    zp = _op(nt, "SUBTRACT", dot("Object"), float(org[2]))                      # hauteur dans l'impression (mm)
    if "plateau_masque" in nt.nodes:                       # grain du plateau : seulement là où la pièce le touche (Lou, 2026-10-28)
        pm = nt.nodes["plateau_masque"].outputs["Result"]; vers = [l.to_socket for l in pm.links]
        contact = nt.nodes.new("ShaderNodeMapRange"); contact.name = "plateau_contact"     # 1 à z ≤ 0,03, 0 dès 0,08 mm
        contact.inputs["From Min"].default_value, contact.inputs["From Max"].default_value = 0.03, 0.08
        contact.inputs["To Min"].default_value, contact.inputs["To Max"].default_value = 1.0, 0.0
        nt.links.new(zp, contact.inputs["Value"])
        masque = _op(nt, "MULTIPLY", pm, contact.outputs["Result"])
        for s_ in vers: nt.links.new(masque, s_)
    tranche = nt.nodes.new("ShaderNodeMapRange")                                # 1 sur les tranches, 0 sur dessus / dessous
    tranche.inputs["From Min"].default_value, tranche.inputs["From Max"].default_value = 0.6, 0.75
    tranche.inputs["To Min"].default_value, tranche.inputs["To Max"].default_value = 1.0, 0.0
    nt.links.new(_op(nt, "ABSOLUTE", dot("Normal")), tranche.inputs["Value"])
    u = _op(nt, "DIVIDE", _op(nt, "SUBTRACT", zp, h0), h)                       # couches au-dessus de la première
    prem = _op(nt, "LESS_THAN", zp, h0)
    tl = _op(nt, "ADD", _op(nt, "MULTIPLY", prem, _op(nt, "DIVIDE", zp, h0)),
             _op(nt, "MULTIPLY", _op(nt, "SUBTRACT", 1.0, prem), _op(nt, "FRACT", u)))
    s = _op(nt, "SUBTRACT", _op(nt, "MULTIPLY", tl, 2.0), 1.0)
    prof = _op(nt, "SQRT", _op(nt, "MAXIMUM", _op(nt, "SUBTRACT", 1.0, _op(nt, "MULTIPLY", s, s)), 0.0))
    wn = nt.nodes.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = "1D"
    nt.links.new(_op(nt, "FLOOR", u), wn.inputs["W"])                           # chaque couche un peu différente
    amp = _op(nt, "ADD", _op(nt, "MULTIPLY", wn.outputs["Value"], 0.4 * RELIEF_TRANCHE * h), 0.8 * RELIEF_TRANCHE * h)
    h_tranche = _op(nt, "MULTIPLY", _op(nt, "MULTIPLY", _op(nt, "SUBTRACT", prof, 1.0), amp), tranche.outputs["Result"])
    uv = nt.nodes.new("ShaderNodeUVMap"); uv.uv_map = "UV_fdm"
    th = nt.nodes.new("ShaderNodeTexImage"); th.image = ih; th.interpolation = "Cubic"; nt.links.new(uv.outputs["UV"], th.inputs["Vector"])
    tf = nt.nodes.new("ShaderNodeTexImage"); tf.image = ifil; tf.interpolation = "Closest"; nt.links.new(uv.outputs["UV"], tf.inputs["Vector"])
    sep = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(th.outputs["Color"], sep.inputs["Color"])
    hauteur = _op(nt, "ADD", h_tranche, sep.outputs["Red"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.name = "trajets_fdm_relief"
    bp.inputs["Strength"].default_value = 1.0; bp.inputs["Distance"].default_value = 1.0
    nt.links.new(hauteur, bp.inputs["Height"]); _sous_relief(nt, b, bp)
    vt = nt.nodes.new("ShaderNodeVectorTransform"); vt.vector_type = "VECTOR"; vt.convert_from = "OBJECT"; vt.convert_to = "WORLD"
    nt.links.new(tf.outputs["Color"], vt.inputs["Vector"]); nt.links.new(vt.outputs["Vector"], b.inputs["Tangent"])
    b.inputs["Anisotropic"].default_value = ANISOTROPIE
    m["procede"] = f"{m.get('procede', 'FDM')} ; trajets {os.path.basename(trajets_npz)}"
    return m


# ------------------------------------------------------------------ masques de lettres projetés sur la face avant (-y)
def _masque(nt, ml, nom, interpolation):
    import numpy as np
    m_ = ml["masque"]; nz, nx = m_.shape
    img = bpy.data.images.new(nom, nx, nz, float_buffer=False, alpha=False); img.colorspace_settings.name = "Non-Color"
    px = np.empty((nz, nx, 4), np.float32); px[..., 0] = px[..., 1] = px[..., 2] = m_; px[..., 3] = 1.0
    img.pixels.foreach_set(px.ravel()); img.pack()
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
    uv = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(_op(nt, "DIVIDE", _op(nt, "SUBTRACT", sep.outputs["X"], float(ml["x0"])), nx * float(ml["pas"])), uv.inputs["X"])
    nt.links.new(_op(nt, "DIVIDE", _op(nt, "SUBTRACT", sep.outputs["Z"], float(ml["z0"])), nz * float(ml["pas"])), uv.inputs["Y"])
    it = nt.nodes.new("ShaderNodeTexImage"); it.image = img; it.interpolation = interpolation; it.extension = "CLIP"
    nt.links.new(uv.outputs[0], it.inputs["Vector"])
    sep_n = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Normal"], sep_n.inputs[0])
    face = nt.nodes.new("ShaderNodeMapRange")                    # seulement la face avant (normale -y)
    face.inputs["From Min"].default_value, face.inputs["From Max"].default_value = -0.9, -0.97
    nt.links.new(sep_n.outputs["Y"], face.inputs["Value"])
    return it.outputs["Color"], face.outputs["Result"], sep, tc


def _melange(nt, b, fac, coul):
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
    e = lambda ident: next(i for i in mix.inputs if i.identifier == ident)
    nt.links.new(fac, e("Factor_Float")); e("B_Color").default_value = srgb(coul)
    base = b.inputs["Base Color"]                          # teinte d'un nœud (FDM : écart de couche) ou valeur fixe
    if base.is_linked: nt.links.new(base.links[0].from_socket, e("A_Color"))
    else: e("A_Color").default_value = base.default_value
    nt.links.new(next(o for o in mix.outputs if o.identifier == "Result_Color"), b.inputs["Base Color"])


def lettres_gravees(m, ml, blanc="#e4dfdf", chaud="#ffa957"):
    """Plaque « jour / nuit » : acrylique translucide peint, lettres découvertes au laser jusqu'à la sous-couche blanche (FS 37875,
    jamais de blanc absolu), mates ; rétroéclairées la nuit en blanc chaud (≈ 2 700 K) : nœud « force_lettres » (0 le jour).
    ml = masque exact des lettres (impression/lettres.py … exact) projeté sur la face avant (-y) de la plaque pleine."""
    nt = m.node_tree; b = _bsdf(m)
    masque, face, _, _ = _masque(nt, ml, f"{m.name}_lettres_gravees", "Cubic")
    f_ = _op(nt, "MULTIPLY", masque, face)
    _melange(nt, b, f_, blanc)
    r0 = b.inputs["Roughness"].default_value
    nt.links.new(_op(nt, "ADD", r0, _op(nt, "MULTIPLY", f_, 0.8 - r0)), b.inputs["Roughness"])   # sous-couche découverte : mate
    b.inputs["Emission Color"].default_value = srgb(chaud)
    fo = nt.nodes.new("ShaderNodeMath"); fo.operation = "MULTIPLY"; fo.name = "force_lettres"; fo.inputs[1].default_value = 0.0
    nt.links.new(f_, fo.inputs[0]); nt.links.new(fo.outputs[0], b.inputs["Emission Strength"])
    return m


def lettres_imprimees(m, ml, blanc="#c9c7c1"):
    """Lettres blanches imprimées dans la masse d'une façade FDM noire (méthode du transpondeur, Lou 2026-10-26) : masque de leur
    premier calque (impression/lettres.py : coins arrondis par le cordon, traits fins, bord qui ondule, mélange des matières)
    projeté sur la face avant ; blanc adouci ; stries à 45° du premier calque qui ressortent en brillance par plaques."""
    nt = m.node_tree; b = _bsdf(m)
    masque, face, sep, tc = _masque(nt, ml, f"{m.name}_lettres_imprimees", "Linear")
    _melange(nt, b, _op(nt, "MULTIPLY", masque, face), blanc)
    pas_s = _op(nt, "ADD", 0.45, _op(nt, "MULTIPLY", masque, float(ml["largeur"]) - 0.45))       # pas local du cordon
    u = _op(nt, "MULTIPLY", _op(nt, "ADD", sep.outputs["X"], sep.outputs["Z"]), 0.70711)          # le long de la diagonale à 45°
    strie = _op(nt, "POWER", _op(nt, "MULTIPLY", _op(nt, "ADD", _op(nt, "SINE", _op(nt, "DIVIDE", _op(nt, "MULTIPLY", u, 2 * math.pi), pas_s)), 1.0), 0.5), 3.0)
    br = nt.nodes.new("ShaderNodeTexNoise"); br.inputs["Scale"].default_value = 0.12; br.inputs["Detail"].default_value = 1.5
    nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
    plaques = nt.nodes.new("ShaderNodeMapRange")
    plaques.inputs["From Min"].default_value, plaques.inputs["From Max"].default_value = 0.48, 0.62
    nt.links.new(br.outputs["Fac"], plaques.inputs["Value"])
    vis = _op(nt, "MULTIPLY", _op(nt, "MULTIPLY", strie, plaques.outputs["Result"]), face)
    rug = b.inputs["Roughness"]
    r0 = rug.links[0].from_socket if rug.is_linked else rug.default_value
    nt.links.new(_op(nt, "SUBTRACT", r0, _op(nt, "MULTIPLY", vis, 0.12)), rug)                    # ligne de cordon un peu plus lisse
    return m


# ------------------------------------------------------------------ SLA, MJF, acrylique, métaux
def sla(matiere="sla_jlc_black", finition="poncee_huilee", nom=None):
    """Résine SLA (JLC3DP) : la teinte de la fiche, la finition décide la rugosité et le grain (SLA) ; une résine qui diffuse
    (9600) garde sa diffusion : la lumière s'arrondit dans les bords et les parois fines."""
    f = CAT.fiche(matiere)
    m = CAT.construire(matiere, matiere=nom or f"{f['matiere']}_{finition}", **SLA[finition])
    m["procede"] = f"SLA {finition}"; return m


def mjf(matiere="nylon_pa12_noir", tuile=None, relief=None, nom=None):
    """Nylon fondu par lit de poudre (MJF / SLS) : teinte uniforme, mate, grain de poudre en relief seul (règle « nylon » de Lou) ;
    tuile (mm) et relief (amplitude mm) pour régler le grain (défaut : la fiche)."""
    f = CAT.fiche(matiere); pas, amp, det = f["grain"]
    m = CAT.construire(matiere, matiere=nom or f["matiere"], grain=(tuile or pas, relief or amp, det))
    m["procede"] = "MJF / SLS"; return m


def acrylique_laser(matiere="peinture_fs36118", masque=None, blanc="#e4dfdf", chaud="#ffa957", nom=None):
    """Acrylique coulé découpé au laser et peint, lettres découvertes au laser jusqu'à la sous-couche (« jour / nuit », comme le
    transpondeur et la réplique du F-COM2) ; masque = .npz chargé (impression/lettres.py … exact), None : plaque sans lettres.
    La nuit : m.node_tree.nodes['force_lettres'].inputs[1] = force d'émission des lettres."""
    m = CAT.construire(matiere, matiere=nom or CAT.fiche(matiere)["matiere"])
    if masque is not None: lettres_gravees(m, masque, blanc, chaud)
    m["procede"] = "acrylique laser peint"; return m


def metal(matiere="alu_anodise_gris_fonce", nom=None):
    """Métaux (usinés, du commerce) : la fiche porte déjà sa finition (sablé anodisé, brossé, oxydé noir, inox naturel, laiton)."""
    m = CAT.construire(matiere, matiere=nom or CAT.fiche(matiere)["matiere"])
    m["procede"] = CAT.fiche(matiere)["procede"]; return m
