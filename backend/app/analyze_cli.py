"""Classe les villages observés par rentabilité : `python -m app.analyze_cli [--explain N]`.

Lit les fichiers JSON du mode observation (dossier `observations`) et calcule
le score de chaque village avec les préférences de l'utilisateur.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from pydantic import ValidationError

from app.analysis.profitability import ProfitabilityResult, compute_profitability
from app.analysis.scoring import PREFERENCES_FILE, ScoringPreferences, load_preferences
from app.analysis.village_analysis import Loot, VillageSheet, build_sheet
from app.config import Settings
from app.observer import ObservationRecord

logger = logging.getLogger("app.analyze")


def sheet_from_record(record: ObservationRecord) -> VillageSheet | None:
    """Fiche village depuis un enregistrement du mode observation (None si butin incomplet)."""
    values = {name: c.value for name, c in record.loot.items()}
    if len(values) != 3 or any(v is None for v in values.values()):
        return None
    confidence = min(c.confidence for c in record.loot.values())
    return build_sheet(Loot(**values), confidence, record.captured_at, record.image)


def load_observations(directory: Path) -> list[VillageSheet]:
    sheets: list[VillageSheet] = []
    for path in sorted(directory.glob("scout_*.json")):
        try:
            record = ObservationRecord.model_validate_json(path.read_text(encoding="utf-8"))
        except (ValidationError, OSError) as exc:
            logger.warning("Fichier ignoré %s : %s", path.name, exc)
            continue
        sheet = sheet_from_record(record)
        if sheet is not None:
            sheets.append(sheet)
    return sheets


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

    prefs = load_preferences(settings.data_dir)
    if prefs == ScoringPreferences():
        print(f"Préférences par défaut (personnalisables dans {settings.data_dir / PREFERENCES_FILE})")
    sheets = load_observations(args.dir)
    if not sheets:
        print(f"Aucun village observé dans {args.dir} (lance python -m app.observe_cli)", file=sys.stderr)
        return 1

    ranked = sorted(((s, compute_profitability(s, prefs)) for s in sheets), key=lambda p: -p[1].score)
    print_ranking(ranked)
    for sheet, result in ranked[: max(0, args.explain)]:
        print(f"\nDétail - village de {sheet.analyzed_at:%H:%M:%S} ({sheet.source_image}) :")
        print("\n".join(result.explain()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
