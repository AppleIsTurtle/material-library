r"""Réglages réels d'un profil OrcaSlicer, héritage résolu (feature fdm-trajets, chunk-01) : Python système.
    python profil.py "<nom du profil>" [<clé> …]          ex. python profil.py "0.20 Standard @Snapmaker U1 (0.4 nozzle)"
    python profil.py --aplatir "<nom>" <sortie.json>      écrit le profil complet (pour --load-settings de la ligne de commande)
Cherche les profils par leur champ « name » dans les profils système d'OrcaSlicer (ORCA) ; un profil hérite (« inherits ») de
son parent, ses propres clés l'emportent. Sans clé : affiche les réglages qui décident des trajets (parois, dessus, couture…)."""
import glob, json, os, sys

ORCA = r"F:\OrcaSlicer\2.4.2"                       # version portable installée le 2026-10-27 (accord de Lou)
PROFILS = os.path.join(ORCA, "resources", "profiles")
TRAJETS = ("layer_height", "initial_layer_print_height", "line_width", "outer_wall_line_width", "inner_wall_line_width",
           "top_surface_line_width", "sparse_infill_line_width", "internal_solid_infill_line_width", "initial_layer_line_width",
           "wall_loops", "top_shell_layers", "top_shell_thickness", "bottom_shell_layers", "top_surface_pattern",
           "bottom_surface_pattern", "internal_solid_infill_pattern", "sparse_infill_pattern", "sparse_infill_density",
           "infill_direction", "solid_infill_direction", "wall_sequence", "wall_generator", "seam_position", "seam_gap",
           "infill_wall_overlap", "top_bottom_infill_wall_overlap", "ironing_type", "only_one_wall_top", "gap_fill_target",
           "filter_out_gap_fill", "precise_outer_wall", "detect_thin_wall", "nozzle_diameter", "elefant_foot_compensation",
           "xy_hole_compensation", "xy_contour_compensation", "fuzzy_skin", "staggered_inner_seams", "wall_direction")

_index = None


def index():
    global _index
    if _index is None:
        _index = {}
        for f in glob.glob(os.path.join(PROFILS, "**", "*.json"), recursive=True):
            try: d = json.load(open(f, encoding="utf-8"))
            except (ValueError, UnicodeDecodeError): continue
            if isinstance(d, dict) and "name" in d: _index.setdefault(d["name"], f)
    return _index


def profil(nom):
    """Profil complet (héritage résolu) : dict des réglages."""
    f = index()[nom]
    d = json.load(open(f, encoding="utf-8"))
    base = profil(d["inherits"]) if d.get("inherits") else {}
    base.update({k: v for k, v in d.items() if k != "inherits"})
    return base


if __name__ == "__main__":
    if sys.argv[1] == "--aplatir":
        d = profil(sys.argv[2]); d.pop("instantiation", None)
        json.dump(d, open(sys.argv[3], "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    else:
        d = profil(sys.argv[1])
        for k in (sys.argv[2:] or TRAJETS):
            print(f"{k:34s} {d.get(k, '(defaut Orca)')}")
