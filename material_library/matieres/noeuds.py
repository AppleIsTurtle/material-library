r"""Briques de nœuds communes aux matières (catalogue.py, procedes.py) : matière vidée, bruit, plage, relief, ondulation.
Repris de MFS boitier/scripts/photoreal.py (_neuf, _bruit, _plage, _relief, _ondulation), 2026-10-27 ; mm partout."""
import bpy


def neuf(nom):
    """Matière vidée : Principled BSDF + sortie (on repart de zéro à chaque appel). Jamais une matière liée (asset) : on en crée
    une locale du même nom plutôt que de la modifier."""
    m = (next((x for x in bpy.data.materials if x.name == nom and x.library is None), None) or bpy.data.materials.new(nom))
    m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial"); b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    return m, nt, b


def bruit(nt, scale, detail=3.0, rough=0.5, coord="Object"):
    """Bruit sur les coordonnées objet (mm) : échelle en 1/mm."""
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = detail
    nz.inputs["Roughness"].default_value = rough
    nt.links.new(tc.outputs[coord], nz.inputs["Vector"]); return nz


def bruit_multi(nt, echelles, poids=None, graine=0.0, coord="Object"):
    """Aléatoire à plusieurs échelles, sans tuile ni régularité (Lou, 2026-11-14 : « fréquence trop élevée, trop even, répétitif ;
    il faut de l'aléatoire à différentes échelles ») : une somme de bruits 4D, un par échelle (`echelles` en mm, `poids` relatifs),
    décorrélés (graine différente), légèrement déformés, et chacun présent par zones (masqué par un bruit trois fois plus large) :
    pas de motif uniforme. Renvoie une sortie ≈ 0 … 1 centrée sur 0,5 (même usage que bruit(...).outputs["Fac"])."""
    poids = poids or [1.0 / len(echelles)] * len(echelles)
    tc = nt.nodes.new("ShaderNodeTexCoord"); somme = None
    def op(o, x, y):
        m = nt.nodes.new("ShaderNodeMath"); m.operation = o
        for k, v in enumerate((x, y)):
            if isinstance(v, (int, float)): m.inputs[k].default_value = v
            else: nt.links.new(v, m.inputs[k])
        return m.outputs[0]
    def nz(l, w, detail, distorsion):
        n = nt.nodes.new("ShaderNodeTexNoise"); n.noise_dimensions = "4D"
        n.inputs["Scale"].default_value = 1.0 / l; n.inputs["W"].default_value = w
        n.inputs["Detail"].default_value = detail; n.inputs["Roughness"].default_value = 0.55
        n.inputs["Distortion"].default_value = distorsion
        nt.links.new(tc.outputs[coord], n.inputs["Vector"]); return n.outputs["Fac"]
    for i, (l, p_) in enumerate(zip(echelles, poids)):
        b_ = op("SUBTRACT", nz(l, graine + 17.31 * i, 2.0, 0.35), 0.5)
        masque = plage(nt, nz(3.0 * l, graine + 53.7 * i + 5.1, 1.0, 0.0), 0.25, 1.0, de=(0.35, 0.65))
        c_ = op("MULTIPLY", op("MULTIPLY", b_, masque), 2.0 * p_)
        somme = c_ if somme is None else op("ADD", somme, c_)
    return op("ADD", somme, 0.5)


def plage(nt, src, a, b, de=(0.3, 0.7)):
    """src (0..1, bruit centré sur 0,5) → a..b (non borné)."""
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = de
    mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = a, b
    nt.links.new(src, mr.inputs["Value"]); return mr.outputs["Result"]


def relief(nt, b, src, strength, distance):
    """Hauteur src → nœud Bump → entrée Normal du BSDF."""
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = strength
    bp.inputs["Distance"].default_value = distance
    nt.links.new(src, bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return bp


def ondulation(nt, b, couches, force=1.0):
    """Relief en vraie hauteur : somme de bruits (échelle en 1/mm, amplitude en mm, détail) → Bump (force 1, distance = force) ;
    les reflets ondulent ou se cassent comme sur une vraie pièce. Teinte et rugosité ne sont pas touchées (règle de Lou : le grain
    est en relief seul)."""
    somme = None
    for echelle, amp, detail in couches:
        c = nt.nodes.new("ShaderNodeMath"); c.operation = "SUBTRACT"; c.inputs[1].default_value = 0.5
        nt.links.new(bruit(nt, echelle, detail, 0.55).outputs["Fac"], c.inputs[0])
        h = nt.nodes.new("ShaderNodeMath"); h.operation = "MULTIPLY_ADD"; h.inputs[1].default_value = amp * 5.0   # bruit ±0,2 → ±amp
        nt.links.new(c.outputs[0], h.inputs[0])
        if somme is None: h.inputs[2].default_value = 0.0
        else: nt.links.new(somme, h.inputs[2])
        somme = h.outputs[0]
    return relief(nt, b, somme, 1.0, force)
