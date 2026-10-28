r"""Non-régression des assets d'un projet : on « photographie » un .blend (maillages, matières, positions, visibilité) avant une
modification de la bibliothèque, puis après, et on compare.
  Dump (dans Blender) :
    blender -b <fichier.blend> --factory-startup --python outils\non_regression.py -- dump <sortie.json>
  Comparaison (Python seul) :
    python outils\non_regression.py comparer <avant.json> <apres.json> [--matieres-renommees]
Code de sortie 0 = identiques, 1 = différences (listées). Tolérance de position / encombrement : 0,002 (unités de la scène, mm).
Repris de l'outil qui a vérifié la version noire du F-COM2 (MFS, 2026-10-27)."""
import json
import sys

TOL = 0.002


def dump(sortie):
    import bpy
    d = {}
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        me = o.data
        vs = me.vertices
        bb = ([min(v.co[i] for v in vs) for i in range(3)] + [max(v.co[i] for v in vs) for i in range(3)]) if vs else [0.0] * 6
        d[o.name] = dict(nv=len(vs), nf=len(me.polygons), bb=[round(x, 3) for x in bb],
                         mw=[round(x, 3) for r in o.matrix_world for x in r],
                         mats=[m.name if m else None for m in me.materials], hr=o.hide_render)
    with open(sortie, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=0)
    print("DUMP", len(d), "maillages ->", sortie)


def comparer(avant, apres, matieres_renommees=False):
    a = json.load(open(avant, encoding="utf-8")); b = json.load(open(apres, encoding="utf-8"))
    seuls = sorted(set(a) ^ set(b))
    diffs = []
    for n in sorted(set(a) & set(b)):
        cles = ("nv", "nf", "hr") if matieres_renommees else ("nv", "nf", "mats", "hr")
        ecart = [k for k in cles if a[n][k] != b[n][k]]
        if max(abs(p - q) for p, q in zip(a[n]["bb"] + a[n]["mw"], b[n]["bb"] + b[n]["mw"])) > TOL:
            ecart.append("position/encombrement")
        if ecart:
            diffs.append((n, ecart))
    print("communs", len(set(a) & set(b)), "| seulement d'un côté", len(seuls), seuls[:10], "| différences", len(diffs))
    for n, e in diffs[:30]:
        print("  ", n, e)
    return not seuls and not diffs


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if args[:1] == ["dump"]:
        dump(args[1])
    elif args[:1] == ["comparer"]:
        sys.exit(0 if comparer(args[1], args[2], "--matieres-renommees" in args) else 1)
    else:
        print(__doc__); sys.exit(2)
