r"""Planche des matières (chunk-03) : chaque fiche du catalogue sur une boule et une plaque à arêtes arrondies, dans le studio du
site ; pipette sur une pastille vue de face (médiane hors reflets et ombres), écart à la teinte visée (cible) s'il y en a une ;
option `compenser` : les fiches à cible sont compensées (couleurs.compenser) jusqu'à un écart ≤ 3 par canal et la planche montre la
base trouvée (à reporter dans la fiche si Lou la retient) ; sans l'option, la planche montre la base de la fiche.
    blender -b G:\Blender\MFS\plans_fixes\site\hero.blend --python outils\planches\planche_matieres.py -- [quick] [seul=nom,nom] [compenser]
puis : python outils\planches\assembler.py <sortie>\grille.json <sortie>\planche_matieres.png"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import studio as ST                                   # noqa: E402
import bmesh                                          # noqa: E402
import bpy                                            # noqa: E402
from material_library import aretes as AR               # noqa: E402
from material_library.imperfections import uv_mm        # noqa: E402
from material_library.matieres import catalogue as CAT  # noqa: E402
from material_library.matieres import couleurs as CO    # noqa: E402

SEUL = next((a[5:].split(",") for a in ST.ARGV if a.startswith("seul=")), None)
sc, col, SORTIE = ST.preparer("matieres", res=(1000, 750))


def objet(nom, bm, lisse=True):
    me = bpy.data.meshes.new(nom); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(nom, me); col.objects.link(o)
    if lisse: AR.lisser(o)
    uv_mm.uv_plan_mm(o)
    return o


bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=96, v_segments=48, radius=8.0)
bmesh.ops.translate(bm, verts=bm.verts, vec=(-11.0, 2.0, 8.0))
BOULE = objet("MAT_boule", bm); BOULE.data.shade_smooth()
PLAQUE = objet("MAT_plaque", AR.plaque(20.0, 16.0, 2.0, 0.0, 3.0, (0.6, 0.6), cz=8.0))
PLAQUE.location = (11.0, 0.0, 0.0); PLAQUE.rotation_euler.z = math.radians(-22)
PASTILLE = objet("MAT_pastille", AR.plaque(30.0, 30.0, 3.0, 0.0, 3.0, (0.6, 0.6), cz=15.0))
TOUS = [BOULE, PLAQUE, PASTILLE]
CAM = ST.camera(col, "CAM_matiere", (-60, -125, 48), (0.0, 0.0, 7.0), 85, 8.0)
CAM_P = ST.camera(col, "CAM_pastille", (0, -160, 15), (0.0, 0.0, 15.0), 100, 11.0)


def poser(m):
    for o in TOUS:
        o.data.materials.clear(); o.data.materials.append(m)


def pastille(nom, **changes):
    """Rend la pastille de face avec la fiche (changes : base=…) et mesure sa teinte."""
    poser(CAT.construire(nom, **changes)); ST.montrer([PASTILLE], TOUS)
    res, ech = (sc.render.resolution_x, sc.render.resolution_y), sc.cycles.samples
    sc.render.resolution_x, sc.render.resolution_y = 400, 400; sc.cycles.samples = 128
    q, ST.QUICK = ST.QUICK, False                    # la pipette se fait toujours à pleine résolution
    sc.render.resolution_percentage = 100
    f = ST.rendre(sc, CAM_P, os.path.join(SORTIE, "pastilles", f"{nom}_{changes.get('base', CAT.fiche(nom)['base']).lstrip('#')}.png"))
    ST.QUICK = q; sc.render.resolution_percentage = 50 if q else 100
    sc.render.resolution_x, sc.render.resolution_y = res; sc.cycles.samples = ech
    return CO.mesurer(f, (0.4, 0.4, 0.6, 0.6))


os.makedirs(os.path.join(SORTIE, "pastilles"), exist_ok=True)
noms = [n for n in CAT.CATALOGUE if SEUL is None or n in SEUL]
releve = {}
for nom in noms:
    f = CAT.fiche(nom)
    if f["cible"] and "compenser" in ST.ARGV:
        base, mes, ec, hist = CO.compenser(f["base"], f["cible"], lambda b: pastille(nom, base=b))
        print(f"COMPENSATION {nom} : cible {f['cible']} | " + " → ".join(f"{b} rend {m}" for b, m in hist)
              + f" | base retenue {base} (écart {ec})", flush=True)
    else:
        base, mes = f["base"], pastille(nom); ec = CO.ecart(mes, f["cible"]) if f["cible"] else None
    releve[nom] = dict(base=base, mesure=mes, cible=f["cible"], ecart=ec, base_fiche=f["base"])
    print(f"PIPETTE {nom} : base {base} rend {mes}" + (f" (cible {f['cible']}, écart {ec})" if f["cible"] else ""), flush=True)
    poser(CAT.construire(nom, base=base)); ST.montrer([BOULE, PLAQUE], TOUS)
    releve[nom]["image"] = ST.rendre(sc, CAM, os.path.join(SORTIE, f"{nom}.png"))

with open(os.path.join(SORTIE, "releve_quick.json" if ST.QUICK else "releve.json"), "w", encoding="utf-8") as fh:
    json.dump(releve, fh, ensure_ascii=False, indent=1)

# grille : par famille, 4 par ligne
lignes, rang = [], []
for fam in dict.fromkeys(CAT.fiche(n)["famille"] for n in noms):
    for n in [n for n in noms if CAT.fiche(n)["famille"] == fam]:
        rang.append(n)
        if len(rang) == 4: lignes.append(rang); rang = []
if rang: lignes.append(rang)


def note(n):
    r = releve[n]
    t = f"{CAT.fiche(n)['titre'][:44]}\nbase {r['base']} → rendu {r['mesure']}"
    return t + (f" (cible {r['cible']}, écart {r['ecart']})" if r["cible"] else "")


g = dict(titre="Matières du catalogue — boule et plaque à arêtes arrondies (studio du site)", colonnes=["", "", "", ""],
         lignes=[dict(titre=" / ".join(dict.fromkeys(CAT.fiche(n)["famille"] for n in l)),
                      images=[releve[n]["image"] for n in l] + [None] * (4 - len(l)),
                      notes=[note(n) for n in l] + [None] * (4 - len(l))) for l in lignes],
         pied="Pipette : médiane hors reflets et ombres d'une pastille vue de face (même studio). Bases des fiches, validées dans "
              "les rendus de MFS ; FS 36118 : base #3b3f45 gardée (Lou, 2026-10-27), elle rend #5f656c sur le rendu de face du F-COM2.")
with open(os.path.join(SORTIE, "grille_quick.json" if ST.QUICK else "grille.json"), "w", encoding="utf-8") as fh:
    json.dump(g, fh, ensure_ascii=False, indent=1)
print("FINI", SORTIE, flush=True)
