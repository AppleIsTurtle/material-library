r"""UV dépliés à l'échelle réelle, en mm (Lou, 2026-10-27 : « déplie les UVs pour avoir des textures non déformées »). Repris de
uv_plan_mm() de MFS (boitier/scripts/maquette_grand_format.py). Une carte d'imperfection lue sur ces UV garde partout la même taille
(tuile en mm), sans l'étirement d'une projection en boîte sur les flancs inclinés (cône d'une tête fraisée)."""
from mathutils import Vector


def uv_plan_mm(ob, nom="UV_mm"):
    """Chaque face est posée à plat sur son propre plan (coordonnées objet, mm) ; les faces coplanaires (dessus d'une tête)
    partagent le même repère, donc sont continues. Écrit dans la première couche UV (créée sous `nom` s'il n'y en a pas)."""
    me = ob.data; lay = me.uv_layers.new(name=nom) if not me.uv_layers else me.uv_layers[0]
    for poly in me.polygons:
        n = poly.normal.normalized()
        ref = Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((1, 0, 0))
        u = ref.cross(n).normalized(); v = n.cross(u)
        for li in poly.loop_indices:
            p_ = me.vertices[me.loops[li].vertex_index].co
            lay.data[li].uv = (p_.dot(u), p_.dot(v))
    return ob
