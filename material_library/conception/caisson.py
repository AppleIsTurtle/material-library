r"""Caisson d'un panneau : coque imprimée ouverte devant, vissée à la façade par ses attaches (inserts dans des colonnes), rainures
du clipsage des supports. Repris de la maquette du F-COM2 (MFS, maquette_grand_format.py : caisson creux, colonnes d'angle,
rainures en queue d'aronde) et rendu générique sur un panneau.Panneau. Méthode : methode/conception_boitier.md, étapes 2, 4, 6.
Repère des maquettes : x à droite (0 = milieu), y vers l'arrière (0 = face avant de la façade), z en haut (0 = bas), mm.

    from material_library.conception import caisson as CA
    R, autour, alertes = CA.rayon_colonne(x_attache=66.35, largeur=145.1, x_obstacle=60.0)
    cai = CA.construire(coll, parent, "GAB_", panneau, profondeur=30.0, y_dos_facade=4.6, matiere=m)
"""
import math

# règles (chacune vient d'un aller-retour du F-COM2 : methode/conception_boitier.md, pièges)
REGLES = dict(
    retrait=0.3,          # contour du caisson en retrait du contour de la façade (le caisson prend la largeur de la façade)
    paroi=2.5,            # parois SLA
    rayon=4.0,            # coins du caisson (vu de face), comme ceux de la façade et du transpondeur
    arrondi_avant=0.4, arrondi_dos=1.5,
    r_colonne_max=6.0,    # colonnes des inserts d'attache
    autour_insert=2.0,    # matière minimale autour d'un insert (JLC en demande 3 : 2,2 accepté au F-COM2)
    retrait_flanc=0.5,    # une colonne reste 0,5 sous la face extérieure du flanc (à R 6 elle ressortait : F-COM2, 2026-10-27)
    jeu_obstacle=0.3,     # entre une colonne et une pièce voisine (cadres des fenêtres)
)

# inserts laiton posés à froid par JLC dans la résine (un insert à chaud ne tient pas dans la SLA, qui ne fond pas) ;
# cotes de la maquette du F-COM2 (≈ 0,57 € TTC pièce, chiffrage.inserts_jlc)
INSERTS = dict(M4=dict(d=5.6, l=6.0, loge_r=2.75), M3=dict(d=4.6, l=5.7, loge_r=2.32))


def dimensions(panneau, profondeur, y_dos_facade, regles=None):
    """Contour du caisson : largeur, z0, z1, y0 (avant, contre le dos de la façade), y1 (dos), rayon."""
    R = dict(REGLES, **(regles or {}))
    return dict(largeur=panneau.largeur - 2 * R["retrait"], z0=R["retrait"], z1=panneau.hauteur - R["retrait"],
                y0=y_dos_facade, y1=y_dos_facade + profondeur, rayon=R["rayon"])


def rayon_colonne(x_attache, largeur, x_obstacle=None, insert="M4", regles=None):
    """Rayon de la colonne d'insert d'une attache à |x| = x_attache : borné pour rester retrait_flanc sous la face du flanc et
    jeu_obstacle à côté de l'obstacle le plus proche vers le milieu (|x| de son bord). Renvoie (R, matière autour de l'insert,
    alertes) ; alerte si la matière autour de l'insert passe sous autour_insert."""
    Rg = dict(REGLES, **(regles or {})); x = abs(x_attache)
    R = min(Rg["r_colonne_max"], largeur / 2 - x - Rg["retrait_flanc"])
    if x_obstacle is not None:
        R = min(R, x - abs(x_obstacle) - Rg["jeu_obstacle"])
    autour = R - INSERTS[insert]["d"] / 2; alertes = []
    if autour < Rg["autour_insert"]:
        alertes.append(f"colonne de l'attache x = {x_attache} : {autour:.2f} de matière autour de l'insert {insert} "
                       f"(≥ {Rg['autour_insert']}) → rentrer l'attache ou écarter l'obstacle")
    for a in alertes: print("CAISSON ALERTE", a, flush=True)
    return R, autour, alertes


def _cylindre_y(x, z, y0, y1, r, n=12):
    """Cylindre d'axe y (bmesh), arêtes vives : pour les unions et les retraits cachés."""
    from material_library import aretes as AR
    return AR.plaque(2 * r, 2 * r, r - 1e-3, y0, y1, (0.0, 0.0), cx=x, cz=z, n=n)


def construire(coll, parent, prefixe, panneau, profondeur, y_dos_facade, matiere, x_obstacle=None, inserts_dos=(),
               clipsage=True, y_butee=None, regles=None):
    """Caisson creux (objet <prefixe>CAISSON) : coque à parois `paroi`, ouverte devant ; colonnes d'insert M4 aux attaches du
    panneau (logements des inserts) ; inserts M3 au dos aux (x, z) de inserts_dos (fixation sur pupitre) ; rainures du clipsage
    des supports (supports.CLIPSAGE) ouvertes au dos, butée à y_butee (défaut : 40 % de la profondeur), sous leurs renforts.
    Renvoie (objet, dimensions, alertes)."""
    import bpy
    from mathutils import Vector
    from material_library import aretes as AR
    from material_library.conception import supports as SU
    R = dict(REGLES, **(regles or {})); D = dimensions(panneau, profondeur, y_dos_facade, R)
    W, z0, z1, y0, y1, cr, p = D["largeur"], D["z0"], D["z1"], D["y0"], D["y1"], D["rayon"], R["paroi"]
    cz, h = (z0 + z1) / 2, z1 - z0
    me = bpy.data.meshes.new(prefixe + "CAISSON")
    AR.plaque(W, h, cr, y0, y1, (R["arrondi_avant"], R["arrondi_dos"]), cz=cz, n=12).to_mesh(me)
    me.materials.append(matiere)
    ob = bpy.data.objects.new(prefixe + "CAISSON", me); coll.objects.link(ob); ob.parent = parent
    AR.retrancher(ob, [AR.plaque(W - 2 * p, h - 2 * p, cr - p, y0 - 1.0, y1 - p, (0.05, 0.6), cz=cz, n=12)])
    alertes, cols = [], []
    ins = INSERTS["M4"]
    for x, z in panneau.attaches:
        rc, _, al = rayon_colonne(x, W, x_obstacle, "M4", R); alertes += al
        cols.append(_cylindre_y(x, z, y0 - 0.01, y0 + ins["l"] + 4.0, rc, 16))
    cl = SU.CLIPSAGE; yb = y_butee if y_butee is not None else y0 + 0.4 * profondeur
    if clipsage:      # renforts intérieurs au-dessus des rainures
        for sx in (-1, 1):
            xc = sx * (W / 2 - cl["X"])
            cols.append(AR.plaque(2 * cl["RIB_HW"], cl["RIB_TOP"] - 1.0, 0.5, yb - 0.5, y1 - p + 0.5, (0.05, 0.05),
                                  cx=xc, cz=z0 + (1.0 + cl["RIB_TOP"]) / 2, n=4))
    for x, z in inserts_dos:
        cols.append(_cylindre_y(x, z, y1 - p - INSERTS["M3"]["l"] - 0.8, y1 - 0.5, 5.5, 24))
    if cols: AR.retrancher(ob, cols, op="UNION")
    trous = [_cylindre_y(x, z, y0 - 0.5, y0 + ins["l"], ins["loge_r"], 24) for x, z in panneau.attaches]
    trous += [_cylindre_y(x, z, y1 - INSERTS["M3"]["l"], y1 + 0.5, INSERTS["M3"]["loge_r"], 24) for x, z in inserts_dos]
    if clipsage:      # rainures en queue d'aronde, entrée évasée de CH_ENTREE à 45° dans la paroi du dos
        import bmesh
        for sx in (-1, 1):
            xc = sx * (W / 2 - cl["X"]); bm = bmesh.new()
            AR.loft(bm, [[Vector((x, y, z)) for x, z in SU.profil_rainure(xc, z0, off, cl)] for y, off in
                         ((yb, 0.0), (y1 - cl["CH_ENTREE"], 0.0), (y1 + 1.0, cl["CH_ENTREE"] + 1.0))])
            trous.append(bm)
    AR.retrancher(ob, trous)
    D["y_butee"] = yb
    return ob, D, alertes
