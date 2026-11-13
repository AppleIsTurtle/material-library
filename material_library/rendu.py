r"""Rendu produit : la méthode complète en quelques appels, pour qu'un script de rendu ne puisse plus en oublier une étape.

Ce que fait chaque fonction, et pourquoi :
- `studio()` : la scène de référence (studio du site, ouverte EN LECTURE, jamais enregistrée), celle où les bases des matières du
  catalogue sont compensées à la pipette ; Cycles sur GPU (OptiX), débruitage. Un studio maison change toutes les teintes : un PLA
  noir (albédo ≈ 0,04) y sort bouché, sans reflet (Lou, 2026-11-13 : « rendus hyper sombres »).
- `piece_fdm()` : une pièce imprimée par dépôt de fil telle qu'elle sort de l'imprimante : sommets soudés (STL), lissage par angle et
  normales pondérées, matière FDM de la fiche, VRAIS TRAJETS de la buse (tranchage du profil de l'imprimeur, `procedes.trajets`) avec
  la face sur le plateau (lisse par défaut : sillons du premier lit lisibles au reflet, aucun grain), nœud Bevel
  (`aretes.RAYONS["pla"]`). Pas d'imperfections de frottement sur le PLA (methode/fdm_trajets.md : poussière fine seulement, à faire).
- `piece()` : toute autre pièce (SLA, MJF, acrylique, métal, matière du catalogue) : soudure, normales, matière, nœud Bevel.
- `visserie()` : nœud Bevel des têtes de vis (`aretes.RAYONS["vis"]`) et imperfections (rayures, frottements, poussière) sur les
  objets de `visserie.pieces`.
- `camera()`, `rendre()` : caméra en mm à profondeur de champ, rendu d'une vue.

« Brouillon » = moins d'échantillons, jamais moins de méthode : la recette d'aperçu de l'exemple d'AGENTS.md ne sert qu'à contrôler
une géométrie.

    blender -b <STUDIO> --python mon_rendu.py        (STUDIO : variable MATERIAL_LIBRARY_STUDIO ; lancer via le garde-fou mémoire)
"""
import math
import os

import bmesh
import bpy
from mathutils import Vector

from . import DONNEES
from . import aretes as AR
from .matieres import catalogue as CAT, procedes as PR, reglages_fdm as SRF

STUDIO = os.environ.get("MATERIAL_LIBRARY_STUDIO") or r"G:\Projets\SimLogix\blender\f-com\plans_fixes\site\hero.blend"
ECARTER = ("F-COM1",)          # objets de la scène du site qui ne doivent pas être dans le champ (écartés, pas supprimés)


def studio(echantillons=128, res=(1600, 900), ecarter=ECARTER):
    """Scène prête dans le studio de référence ; refuse de tourner dans une autre scène (message avec la commande à lancer)."""
    if os.path.normcase(os.path.abspath(bpy.data.filepath or "")) != os.path.normcase(os.path.abspath(STUDIO)):
        raise RuntimeError(f"rendu.studio() : ouvrir le studio de référence en lecture avant le script : "
                           f"blender -b \"{STUDIO}\" --python <script> (ouvert : {bpy.data.filepath or 'scène vide'})")
    sc = bpy.context.scene
    for nom in ecarter:
        if nom in bpy.data.objects: bpy.data.objects[nom].location = (0.0, 0.0, -5000.0)
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"; prefs.get_devices()
    for d in prefs.devices: d.use = d.type == "OPTIX"
    sc.render.engine = "CYCLES"; sc.cycles.device = "GPU"; sc.cycles.samples = echantillons; sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    return sc


def _souder_lisser(ob, souder=True):
    """Sommets soudés (un STL a chaque triangle à part : sans soudure, ni lissage ni normales pondérées), lissage par angle,
    normales pondérées par l'aire des faces (modificateur gardé : les cuissons lisent le maillage évalué)."""
    if souder:
        bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bm.to_mesh(ob.data); bm.free()
    ob.data.update(); ob.data.shade_smooth(); ob.data.set_sharp_from_angle(angle=math.radians(45.0))
    if "normales_ponderees" not in ob.modifiers:
        m = ob.modifiers.new("normales_ponderees", "WEIGHTED_NORMAL")
        m.mode = "FACE_AREA"; m.weight = 50; m.keep_sharp = True; m.thresh = 0.01


def piece_fdm(ob, matiere="pla_noir", plateau="-Z", grain="lisse", buse=0.4, res=None, translucide=0.0, trajets=True,
              arrondi=None, dossier=None, souder=True, res_premier_lit=None, **reglages):
    """Pièce FDM comme imprimée : `plateau` = face posée sur le plateau dans le repère de l'objet (« -Y » : face avant) ; `grain`
    du plateau (procedes.GRAINS ; « lisse » par défaut : plateau lisse de l'imprimeur FDM) ; trajets=False pour une pièce d'une ou
    deux couches posée sur une autre (lettres, cœurs à fleur) : matière FDM seule ; res : côté des cartes des trajets (défaut :
    automatique ; 4096 garde une grande façade sous 12 Go) ; res_premier_lit : les faces posées sur le plateau deviennent un objet
    à part (même repère, mêmes trajets) avec leurs propres cartes de ce côté — sur une grande pièce, une carte commune ne résout pas
    les sillons nets du premier lit (≈ 0,1 mm) : ils disparaissent de la face (2026-11-13) ; arrondi : rayon du nœud Bevel (défaut RAYONS["pla"] ; 0 : aucun,
    pour une matière à fleur d'une autre, où il dessinerait un liseré) ; reglages : réglages du tranchage (motif_dessus=…).
    Renvoie la matière posée."""
    _souder_lisser(ob, souder)
    m = PR.fdm(matiere, buse=buse, axe=plateau[-1].upper(), plateau=plateau, translucide=translucide,
               nom=f"{matiere}_FDM_{ob.name}", grain=grain)
    PR.poser(ob, m)
    pieces = [(ob, res)]
    if trajets:
        dossier = dossier or os.path.join(DONNEES, "fdm", "rendu")
        npz = SRF.trancher_objet(ob, dossier, buse, plateau, **reglages)       # tranchage de la pièce entière
        if res_premier_lit:
            lit = _separer_premier_lit(ob, plateau)
            if lit: lit.data.materials[0] = PR.fdm(matiere, buse=buse, axe=plateau[-1].upper(), plateau=plateau,
                                                   translucide=translucide, nom=f"{matiere}_FDM_{lit.name}", grain=grain)
            if lit: pieces.append((lit, res_premier_lit))
        for o, r_ in pieces:
            PR.trajets(o, npz, res=r_, copie=False, dossier=dossier)
            print("RENDU.trajets", o.name, r_, flush=True)
    r = AR.RAYONS["pla"] if arrondi is None else arrondi
    for o, _ in pieces:
        if r: AR.bevel_rendu(o.active_material, r)
    return ob.active_material


def _separer_premier_lit(ob, plateau, epaisseur=0.02):
    """Sépare les faces de `ob` posées sur le plateau (tous leurs sommets à moins de `epaisseur` mm du plan du plateau ; par la
    position seule : les lamelles laissées par les booléens ont des normales faussées, gardées à part elles ressortaient en
    tirets brillants sur la face, 2026-11-13) dans un
    objet `<nom>_premier_lit` de même repère, même parent et mêmes modificateurs ; `ob` garde le reste. Renvoie l'objet, ou None."""
    i = "XYZ".index(plateau[-1].upper()); s = -1.0 if plateau.startswith("-") else 1.0
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
    bord = max(v.co[i] for v in bm.verts) if s > 0 else min(v.co[i] for v in bm.verts)   # plan du plateau
    def au_plateau(f):
        return all(abs(v.co[i] - bord) < epaisseur for v in f.verts)
    sel = [f for f in bm.faces if au_plateau(f)]
    if not sel: bm.free(); return None
    me_lit = ob.data.copy(); lit = ob.copy(); lit.data = me_lit; lit.name = ob.name + "_premier_lit"
    lit["uv_plan"] = plateau[-1].upper()          # face plane : UV projetés à plat (un îlot), pas de couture dans ses cartes
    for m_ in list(lit.modifiers): lit.modifiers.remove(m_)   # plane : ombrée à plat (les lamelles des booléens, lissées, faisaient
    me_lit.shade_flat()                                        # de petits triangles clairs ; le Bevel arrondit toujours ses bords)
    for c in ob.users_collection: c.objects.link(lit)
    garde = {f.index for f in sel}                                             # indices avant toute suppression
    b2 = bm.copy(); bmesh.ops.delete(bm, geom=sel, context="FACES"); bm.to_mesh(ob.data); bm.free()
    b2.faces.ensure_lookup_table()
    bmesh.ops.delete(b2, geom=[f for f in b2.faces if f.index not in garde], context="FACES"); b2.to_mesh(me_lit); b2.free()
    return lit


def piece(ob, matiere, arrondi, souder=True):
    """Toute autre pièce : `matiere` = bpy.types.Material (PR.sla, PR.mjf, PR.acrylique_laser, PR.metal…) ou nom d'une fiche du
    catalogue ; `arrondi` = rayon du nœud Bevel (aretes.RAYONS[…] ; 0 : aucun). Renvoie la matière posée."""
    _souder_lisser(ob, souder)
    m = CAT.construire(matiere) if isinstance(matiere, str) else matiere
    PR.poser(ob, m)
    if arrondi: AR.bevel_rendu(m, arrondi)
    return m


def visserie(objets, arrondi=None, imperfections=1.0):
    """Visserie de visserie.pieces telle qu'en vrai : nœud Bevel des têtes (frappe à froid : RAYONS["vis"]) et imperfections
    (imperfections.appliquer : micro-rayures et rayures des métaux, frottements, poussière dans les recoins ; UV en mm posés par
    visserie.pieces) ; imperfections=0 : aucune (Lou, 2026-11-13 : « les vis n'ont aucune imperfection »)."""
    from .imperfections import imperfections as IM
    r = AR.RAYONS["vis"] if arrondi is None else arrondi
    for m in {s.material for o in objets if o.type == "MESH" for s in o.material_slots if s.material}:
        if m.library is None and m.use_nodes: AR.bevel_rendu(m, r)
    if imperfections: IM.appliquer(objets, force=imperfections)


def camera(nom, loc, cible, focale, fstop=8.0, col=None):
    """Caméra en mm (capteur 36), profondeur de champ mise au point sur `cible` ; devient la caméra de la scène."""
    sc = bpy.context.scene
    cd = bpy.data.cameras.new(nom); cd.lens = focale; cd.sensor_width = 36.0; cd.clip_start = 1.0; cd.clip_end = 20000.0
    o = bpy.data.objects.new(nom, cd); (col or sc.collection).objects.link(o)
    viser(o, loc, cible, fstop)
    sc.camera = o
    return o


def viser(cam, loc, cible, fstop=None):
    """Replace une caméra (et sa mise au point) : de `loc` vers `cible`."""
    cam.location = loc; cam.rotation_euler = (Vector(cible) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    cam.data.dof.use_dof = True; cam.data.dof.focus_distance = (Vector(cible) - Vector(loc)).length
    if fstop: cam.data.dof.aperture_fstop = fstop


def rendre(chemin, res=None):
    """Rend la caméra active dans `chemin` (PNG) ; res : (largeur, hauteur) pour cette vue."""
    sc = bpy.context.scene
    if res: sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = chemin
    bpy.ops.render.render(write_still=True)
    print("RENDU", chemin, flush=True)
    return chemin
