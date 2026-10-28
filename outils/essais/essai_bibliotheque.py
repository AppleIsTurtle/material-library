r"""Essai du chunk-06 : la bibliothèque bibliotheque\blender_<X.Y>\bibliotheque_matieres.blend de la version qui lance l'essai
  1. s'ouvre dans cette version de Blender (4.4 ou 5.1), chaque asset a un aperçu non vide et un catalogue connu, les images sont
     packées ; les aperçus sont exportés (planche des aperçus) :
       blender -b bibliotheque\blender_5.1\bibliotheque_matieres.blend --python outils\essais\essai_bibliotheque.py -- ouvrir
  2. une matière AJOUTÉE (append) dans le studio du site rend comme sur la planche du chunk-03 (pipette de la même pastille,
     écart ≤ 2 avec releve.json) :
       blender -b G:\Blender\MFS\plans_fixes\site\hero.blend --python outils\essais\essai_bibliotheque.py -- studio"""
import json
import os
import sys

import bpy

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, RACINE)
import material_library as SP                                   # noqa: E402

ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
VERSION_BLENDER = "{}.{}".format(*bpy.app.version[:2])
DOSSIER = os.path.join(RACINE, "bibliotheque", f"blender_{VERSION_BLENDER}")
BIBLIO = os.path.join(DOSSIER, "bibliotheque_matieres.blend")
SORTIE = os.path.join(SP.DONNEES, "planches", "bibliotheque", f"blender_{VERSION_BLENDER}"); os.makedirs(SORTIE, exist_ok=True)

if ARGV[:1] == ["ouvrir"]:
    import numpy as np
    cats = {l.split(":")[0] for l in open(os.path.join(DOSSIER, "blender_assets.cats.txt"), encoding="utf-8")
            if l.count(":") >= 2 and not l.startswith("#")}
    ids = [i for i in list(bpy.data.materials) + list(bpy.data.collections) if i.asset_data]
    erreurs = []
    for i in ids:
        p = i.preview; w, h = p.image_size if p else (0, 0)
        px = np.empty(w * h * 4, np.float32)
        if w: p.image_pixels_float.foreach_get(px)
        if not w or px.reshape(-1, 4)[:, 3].max() == 0: erreurs.append(f"{i.name} : aperçu vide")
        if i.asset_data.catalog_id not in cats: erreurs.append(f"{i.name} : catalogue inconnu")
        if w:                                                   # export de l'aperçu (planche des aperçus)
            im = bpy.data.images.new(f"_ap_{i.name}", w, h, alpha=True); im.pixels.foreach_set(px)
            im.filepath_raw = os.path.join(SORTIE, f"{i.name}.png"); im.file_format = "PNG"; im.save(); bpy.data.images.remove(im)
    non_packees = [im.name for im in bpy.data.images if im.source == "FILE" and not im.packed_file]
    if non_packees: erreurs.append(f"images non packées : {non_packees}")
    print(f"BIBLIOTHEQUE {len(ids)} assets ({sum(isinstance(i, bpy.types.Material) for i in ids)} matières), {len(cats)} catalogues")
    for e in erreurs: print("ERREUR", e)
    json.dump([dict(nom=i.name, image=os.path.join(SORTIE, f"{i.name}.png"), description=i.asset_data.description) for i in ids],
              open(os.path.join(SORTIE, "apercus.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("ESSAI BIBLIOTHEQUE OUVRIR", "OK" if not erreurs else "ECHEC"); sys.exit(1 if erreurs else 0)

if ARGV[:1] == ["studio"]:
    sys.path.insert(0, os.path.join(RACINE, "outils", "planches"))
    import studio as ST                                        # noqa: E402
    from material_library import aretes as AR                   # noqa: E402
    from material_library.matieres import catalogue as CAT      # noqa: E402
    from material_library.matieres import couleurs as CO        # noqa: E402
    sc, col, _ = ST.preparer("bibliotheque", res=(400, 400), echantillons=128)
    rel = os.path.join(SP.DONNEES, "planches", "matieres", "releve.json")             # version finale, sinon l'aperçu
    releve = json.load(open(rel if os.path.exists(rel) else rel.replace(".json", "_quick.json"), encoding="utf-8"))
    noms = {CAT.fiche(n)["matiere"]: n for n in releve if releve[n]["base"] == releve[n]["base_fiche"]}
    with bpy.data.libraries.load(BIBLIO, link=False) as (src, dst):       # « glisser » = Append, comme l'Asset Browser
        dst.materials = [m for m in src.materials if m in noms]
    me = bpy.data.meshes.new("pastille"); AR.plaque(30.0, 30.0, 3.0, 0.0, 3.0, (0.6, 0.6), cz=15.0).to_mesh(me)
    o = bpy.data.objects.new("pastille", me); col.objects.link(o); AR.lisser(o)
    from material_library.imperfections import uv_mm            # noqa: E402
    uv_mm.uv_plan_mm(o)                                       # comme la planche : l'alu brossé et l'oxydé lisent les UV
    cam = ST.camera(col, "CAM_pastille", (0, -160, 15), (0.0, 0.0, 15.0), 100, 11.0)
    pires = 0
    for m in dst.materials:
        n = noms[m.name.split(".")[0]]
        o.data.materials.clear(); o.data.materials.append(m)
        f = ST.rendre(sc, cam, os.path.join(SORTIE, f"pastille_{n}.png"))
        mes = CO.mesurer(f, (0.4, 0.4, 0.6, 0.6)); ec = CO.ecart(mes, releve[n]["mesure"]); pires = max(pires, ec)
        print(f"APPEND {n} : rend {mes}, planche {releve[n]['mesure']}, écart {ec}", flush=True)
    print("ESSAI BIBLIOTHEQUE STUDIO", "OK" if pires <= 2 else "ECHEC", f"(pire écart {pires})")
