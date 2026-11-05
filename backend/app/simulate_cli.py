"""Compare les stratégies de farm sur les villages observés : `python -m app.simulate_cli`.

Simulation THÉORIQUE : aucune attaque n'est lancée. Les hypothèses utilisées
sont affichées avec les résultats et réglables dans `simulation.json`.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from app.analysis.village_analysis import Resource
from app.config import Settings
from app.observer import load_observations
from app.strategy.simulator import SimulationResult, compare_strategies
from app.strategy.strategies import DEFAULT_STRATEGIES
from app.user_settings import load_from_app_settings


def fmt(n: float) -> str:
    return f"{round(n):,}".replace(",", " ")


def print_comparison(results: list[SimulationResult]) -> None:
    print(f"{'#':>2}  {'stratégie':<22} {'attaques':>9} {'passés':>7}  "
          f"{'or net/h':>11} {'élixir net/h':>13} {'noir net/h':>11}  {'points/h':>8}")
    for i, r in enumerate(results, start=1):
        h = r.net_per_hour
        print(f"{i:>2}  {r.strategy.label:<22} {r.attacks:>4}/{r.villages_seen:<4} {r.skip_rate:>7.0%}  "
              f"{fmt(h.gold):>11} {fmt(h.elixir):>13} {fmt(h.dark_elixir):>11}  {r.points_per_hour:>8.0f}")


def print_detail(r: SimulationResult) -> None:
    print(f"\nDétail - {r.strategy.label} : {r.strategy.description}")
    print(f"  {r.attacks} attaque(s) sur {r.villages_seen} village(s) vus, durée simulée {r.duration_s / 60:.1f} min")
    for res in Resource:
        print(f"  {res.value:<12} récupéré {fmt(r.gross_loot.get(res)):>10}  "
              f"coûts {fmt(r.costs.get(res)):>9}  net {fmt(r.net_loot.get(res)):>10}")


def main() -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    settings = Settings.load()
    parser = argparse.ArgumentParser(description="Compare les stratégies de farm (simulation théorique)")
    parser.add_argument("--dir", type=Path, default=settings.observations_dir, help="dossier des observations")
    args = parser.parse_args()

    sheets = load_observations(args.dir)
    if not sheets:
        print(f"Aucun village observé dans {args.dir} (lance python -m app.observe_cli)", file=sys.stderr)
        return 1
    user = load_from_app_settings(settings)
    prefs, assumptions = user.preferences, user.simulation
    results, search_time = compare_strategies(DEFAULT_STRATEGIES, sheets, prefs, assumptions)

    print(f"Simulation théorique sur {len(sheets)} village(s) observé(s) - aucune attaque réelle.\n")
    print_comparison(results)
    print_detail(results[0])
    print("\nHypothèses (réglables via l'API : PUT /api/settings) :")
    for line in assumptions.describe(search_time):
        print(f"  {line}")
    if not any(prefs.army_cost.get(r) for r in Resource):
        print("  [non configuré] coût de l'armée = 0 : butin net surestimé (army_cost dans les préférences)")
    print("\npoints/h : valeur du butin net selon tes préférences (100 points = butin visé atteint).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
