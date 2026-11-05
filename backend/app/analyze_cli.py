"""Classe les villages observés par rentabilité : `python -m app.analyze_cli [--explain N]`.

Lit les fichiers JSON du mode observation (dossier `observations`) et calcule
le score de chaque village avec les préférences de l'utilisateur.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from app.analysis.profitability import ProfitabilityResult, compute_profitability
from app.analysis.scoring import ScoringPreferences
from app.analysis.village_analysis import VillageSheet
from app.config import Settings
from app.observer import load_observations
from app.user_settings import load_from_app_settings


def fmt(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def print_ranking(ranked: list[tuple[VillageSheet, ProfitabilityResult]]) -> None:
    print(f"{'#':>2}  {'heure':<8} {'or':>10} {'élixir':>11} {'noir':>8}  {'score':>5}  recommandation")
    for i, (sheet, result) in enumerate(ranked, start=1):
        loot = sheet.loot
        print(f"{i:>2}  {sheet.analyzed_at:%H:%M:%S} {fmt(loot.gold):>10} {fmt(loot.elixir):>11} "
              f"{fmt(loot.dark_elixir):>8}  {result.score:>5}  {result.recommendation.value}")


def main() -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    settings = Settings.load()
    parser = argparse.ArgumentParser(description="Classe les villages observés par rentabilité")
    parser.add_argument("--dir", type=Path, default=settings.observations_dir, help="dossier des observations")
    parser.add_argument("--explain", type=int, default=1, metavar="N",
                        help="détailler le calcul des N meilleurs villages (défaut : 1)")
    args = parser.parse_args()

    prefs = load_from_app_settings(settings).preferences
    if prefs == ScoringPreferences():
        print("Préférences par défaut (personnalisables via l'API : PUT /api/settings)")
    sheets = load_observations(args.dir)
    if not sheets:
        print(f"Aucun village observé dans {args.dir} (lance python -m app.observe_cli)", file=sys.stderr)
        return 1

    # Égalité de score (ex. plusieurs 100/100) : départage par la valeur NON plafonnée du butin.
    ranked = sorted(
        ((s, compute_profitability(s, prefs)) for s in sheets),
        key=lambda p: (p[1].score, prefs.loot_value(p[0].loot.gold, p[0].loot.elixir, p[0].loot.dark_elixir)),
        reverse=True,
    )
    print_ranking(ranked)
    for sheet, result in ranked[: max(0, args.explain)]:
        print(f"\nDétail - village de {sheet.analyzed_at:%H:%M:%S} ({sheet.source_image}) :")
        print("\n".join(result.explain()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
