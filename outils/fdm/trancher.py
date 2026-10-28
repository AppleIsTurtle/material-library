r"""Tranche des STL avec OrcaSlicer, profil Snapmaker U1 par défaut (feature fdm-trajets, chunk-01) : Python système.
    python trancher.py <dossier de sortie> <buse 0.4|0.2> <pièce.stl> … [--set clé=valeur …]
Les STL d'une même pièce (une par matière) gardent leurs positions relatives : elles sont déplacées ensemble au centre du
plateau (copies binaires dans le dossier de sortie), puis tranchées sans réarrangement ni réorientation, assemblées en **un seul
objet** (--assemble) en « Snapmaker PLA @U1 ». Limite (2026-10-27) : la ligne de commande d'Orca 2.4.2 fond alors les parties en
une seule matière (un seul outil) — exact pour une pièce mono-matière, approché pour une pièce multi-matière (pas de parois aux
frontières entre matières) ; trancher les matières en objets séparés est faux (une flèche de 0,2 mm sous une première couche
de 0,25 disparaît). Le vrai multi-matière demandera un .3mf à parties (point ouvert). Le filament est lu dans son fichier
système (un profil filament aplati fait planter Orca dès qu'il y a plusieurs filaments). --set modifie le profil de réglages
(variantes : wall_loops=1, top_surface_pattern=concentric, seam_position=back…). Écrit plate_1.gcode et reglages.json."""
import json, os, struct, subprocess, sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import profil as PF

EXE = os.path.join(PF.ORCA, "orca-slicer.exe")
PROCESS = {0.4: "0.20 Standard @Snapmaker U1 (0.4 nozzle)", 0.2: "0.10 Standard @Snapmaker U1 (0.2 nozzle)"}   # défauts du profil U1
FILAMENT = "Snapmaker PLA @U1"
CENTRE = (135.0, 135.0)                              # plateau de la U1 : 270 × 270 mm


def lire_stl(chemin):
    d = open(chemin, "rb").read()
    if d[:5] == b"solid" and b"facet" in d[:300]:     # STL texte
        v = [list(map(float, l.split()[1:4])) for l in d.decode("ascii", "replace").splitlines() if l.strip().startswith("vertex")]
        return np.array(v).reshape(-1, 3, 3)
    n = struct.unpack("<I", d[80:84])[0]
    a = np.frombuffer(d[84:84 + 50 * n], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return a["v"].reshape(-1, 3, 3).astype(np.float64)


def ecrire_stl(chemin, tri):
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    a = np.zeros(len(tri), dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    a["n"] = n; a["v"] = tri.reshape(-1, 9)
    with open(chemin, "wb") as f: f.write(b"\0" * 80 + struct.pack("<I", len(tri)) + a.tobytes())


def trancher(dest, buse, pieces, reglages=None):
    """pieces : [stl] ; reglages : {clé: valeur} ajoutés au profil de réglages."""
    os.makedirs(dest, exist_ok=True)
    tris = [lire_stl(p) for p in pieces]
    tout = np.concatenate([t.reshape(-1, 3) for t in tris])
    dep = np.array([CENTRE[0] - (tout[:, 0].min() + tout[:, 0].max()) / 2, CENTRE[1] - (tout[:, 1].min() + tout[:, 1].max()) / 2,
                    -tout[:, 2].min()])
    stls = []
    for p, t in zip(pieces, tris):
        q = os.path.join(dest, os.path.basename(p)); ecrire_stl(q, t + dep); stls.append(q)
    mach = os.path.join(dest, "machine.json"); proc = os.path.join(dest, "process.json"); fil = PF.index()[FILAMENT]
    d = PF.profil(f"Snapmaker U1 ({buse} nozzle)"); d.pop("instantiation", None); json.dump(d, open(mach, "w", encoding="utf-8"), indent=1)
    d = PF.profil(PROCESS[buse]); d.pop("instantiation", None); d.update(reglages or {})
    json.dump(d, open(proc, "w", encoding="utf-8"), indent=1)
    cmd = [EXE, "--slice", "0", "--orient", "0", "--arrange", "0"] + (["--assemble"] if len(stls) > 1 else []) + [
           "--load-settings", f"{mach};{proc}", "--load-filaments", fil, "--outputdir", dest] + stls
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    json.dump(dict(buse=buse, process=PROCESS[buse], filament=FILAMENT, pieces=pieces, reglages=reglages or {},
                   deplacement=dep.round(4).tolist(), code=r.returncode), open(os.path.join(dest, "reglages.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    g = os.path.join(dest, "plate_1.gcode")
    if r.returncode or not os.path.exists(g):
        raise SystemExit(f"OrcaSlicer : code {r.returncode}\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
    return g


if __name__ == "__main__":
    a = sys.argv[1:]; reg = {}
    if "--set" in a:
        i = a.index("--set"); reg = dict(kv.split("=", 1) for kv in a[i + 1:]); a = a[:i]
    print(trancher(a[0], float(a[1]), a[2:], reg))
