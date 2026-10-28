r"""Chiffrage d'un boîtier : prix des procédés relevés sur le F-COM2 et tableau « l'argent là où ça se voit ». Python seul.
Méthode : methode/conception_boitier.md, étapes 3 et 9. Montants en € TTC (Lou achète en particulier : TVA et port sont des
coûts). Les prix sont ceux relevés en 2026-10 (MFS, etude-fabrication-pcb.md § 9 à 13) : à refaire sur devis avant de commander.
"""
USD_EUR = 0.8938          # taux du 2026-10-26
TVA = 0.20

# prix relevés (2026-10) ; « ⚠ » dans la source = estimation à confirmer
PRIX = dict(
    sla_jlc_black_usd_g=0.13,       # SLA JLC Black (caisson, supports) : 36,1 cm³ → 6,13 $ (§ 12)
    sla_9600_usd_g=0.07,            # résine 9600 blanche (molettes) : translucide, pas pour une pièce qui doit cacher la lumière
    sla_densite=1.3,                # g/cm³
    jlc_min_piece_usd=1.05,         # minimum JLC3DP par pièce : grouper les petites pièces en grappe
    port_jlc_usd_kg=27.0,           # DHL ≈ 27 $/kg ⚠
    insert_jlc_usd=0.53,            # insert posé par JLC (résine : pas d'insert à chaud) ≈ 0,57 € TTC
    pla_eur_kg=22.0,                # filament de l'imprimeur FDM (U1), remplissage 20 % ⚠
    pla_densite_effective=0.7,      # g/cm³ de pièce à 20 % de remplissage (boîte à lumière 36,1 cm³ ≈ 0,7 €) ⚠
    port_imprimeur_eur_boitier=0.73, # Mondial Relay, lot d'essai puis colis ≤ 2 kg, série de 30
)


def ttc(usd):
    """Dollars HT → euros TTC."""
    return usd * USD_EUR * (1 + TVA)


def sla_jlc(volume_cm3, resine="black"):
    """Pièce SLA chez JLC3DP (€ TTC, hors port) : volume × densité × prix au gramme, minimum par pièce."""
    usd_g = PRIX["sla_jlc_black_usd_g"] if resine == "black" else PRIX["sla_9600_usd_g"]
    return ttc(max(volume_cm3 * PRIX["sla_densite"] * usd_g, PRIX["jlc_min_piece_usd"]))


def port_jlc(masse_g):
    """Port JLC3DP (€ TTC) pour une masse ; à répartir sur la série (une seule commande groupée)."""
    return ttc(masse_g / 1000 * PRIX["port_jlc_usd_kg"])


def pla_imprimeur(volume_cm3):
    """Filament d'une pièce imprimée chez l'imprimeur FDM (€), sans le temps machine (rémunération à convenir)."""
    return volume_cm3 * PRIX["pla_densite_effective"] / 1000 * PRIX["pla_eur_kg"]


def inserts_jlc(n):
    """n inserts posés par JLC (€ TTC)."""
    return n * ttc(PRIX["insert_jlc_usd"])


def tableau(lignes, cible=None):
    """lignes = [(poste, se_voit, euros, choix)] → tableau Markdown « l'argent là où ça se voit » avec le total (et l'écart à la
    cible de coût de revient) ; euros peut être un nombre ou (min, max)."""
    def fmt(e):
        return f"{e[0]:.2f}–{e[1]:.2f}" if isinstance(e, tuple) else f"{e:.2f}"
    lo = sum(e[0] if isinstance(e, tuple) else e for *_, e, _c in lignes)
    hi = sum(e[1] if isinstance(e, tuple) else e for *_, e, _c in lignes)
    out = ["| Poste | Se voit ? | € / boîtier | Choix |", "|---|---|---|---|"]
    out += [f"| {p} | {'**oui**' if v is True else 'non' if v is False else v} | {fmt(e)} | {c} |" for p, v, e, c in lignes]
    tot = f"{lo:.2f}" if abs(hi - lo) < 1e-9 else f"{lo:.2f}–{hi:.2f}"
    out.append(f"| **Total** | | **{tot}** | {'' if cible is None else f'cible {cible} €'} |")
    return "\n".join(out)
