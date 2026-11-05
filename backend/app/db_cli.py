"""Gestion de la base : `python -m app.db_cli import|stats|backup`.

- import : importe les villages du mode observation (ré-exécutable sans doublon) ;
- stats  : résumé de la base et statistiques par jour ;
- backup : copie de sauvegarde manuelle.
"""
from __future__ import annotations

import argparse
import logging
import sys

from app.config import Settings
from app.database.database import Database
from app.database.importer import import_observations
from app.database.migrations import MigrationError, backup_database
from app.database.repository import count_villages, daily_statistics, recent_villages
from app.strategy.strategies import strategy_label
from app.user_settings import load_user_settings


def fmt(n: float) -> str:
    return f"{round(n):,}".replace(",", " ")


def cmd_import(db: Database, settings: Settings) -> None:
    with db.session() as session:
        prefs = load_user_settings(session, settings.data_dir).preferences
    report = import_observations(db, settings.observations_dir, prefs)
    print(f"{report.found} observation(s) trouvée(s) : {report.imported} importée(s), "
          f"{report.already_present} déjà présente(s).")


def cmd_stats(db: Database) -> None:
    with db.session() as session:
        print(f"Villages en base : {count_villages(session)}")
        stats = daily_statistics(session)
        if stats:
            print(f"\n{'jour':<11} {'villages':>8} {'or':>12} {'élixir':>13} {'noir':>9} {'score moyen':>12}")
            for s in stats:
                print(f"{s.day:%Y-%m-%d} {s.villages_count:>8} {fmt(s.total_gold):>12} {fmt(s.total_elixir):>13} "
                      f"{fmt(s.total_dark_elixir):>9} {s.average_score:>12.1f}")
        recent = recent_villages(session, limit=5)
        if recent:
            print("\n5 derniers villages :")
            for v in recent:
                print(f"  {v.analyzed_at:%Y-%m-%d %H:%M:%S}  or {fmt(v.gold):>9}  élixir {fmt(v.elixir):>10}  "
                      f"noir {fmt(v.dark_elixir):>7}  {v.profitability_score:>3}/100  {v.recommendation}  "
                      f"({strategy_label(v.recommended_strategy)})")


def main() -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Gestion de la base de données CoC AutoFarm")
    parser.add_argument("command", choices=["import", "stats", "backup"])
    args = parser.parse_args()

    settings = Settings.load()
    if args.command == "backup":
        if not settings.database_path.is_file():
            print("Aucune base à sauvegarder.", file=sys.stderr)
            return 1
        print(f"Sauvegarde : {backup_database(settings.database_path, settings.backups_dir, 'manuel')}")
        return 0
    try:
        db = Database.open(settings.database_path, settings.backups_dir)
    except MigrationError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1
    try:
        cmd_import(db, settings) if args.command == "import" else cmd_stats(db)
    finally:
        db.close()
    print(f"\nBase : {settings.database_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
