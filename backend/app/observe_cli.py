"""Mode observation : `python -m app.observe_cli [--interval 1.0] [--duration 600]`.

Analyse la fenêtre du jeu à intervalle régulier et enregistre chaque nouvel
écran de recherche (fichiers + base). Lecture seule : aucune action envoyée au jeu.
Même moteur que l'API (`ObserverService`). Arrêt : Ctrl+C (ou fin de --duration).
"""
from __future__ import annotations

import argparse
import logging
import sys
import time

from app.config import Settings
from app.database.database import Database
from app.database.migrations import MigrationError
from app.logging_setup import configure_logging
from app.observer_service import ObservedVillage, ObserverError, ObserverService, game_window_frames
from app.user_settings import load_user_settings
from app.vision.frame import VisionModels, analyze_frame
from app.vision.image_io import TemplatesNotFoundError


def fmt(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def print_village(v: ObservedVillage) -> None:
    print(f"[{v.analyzed_at:%H:%M:%S}] or {fmt(v.gold)} | élixir {fmt(v.elixir)} | noir {fmt(v.dark_elixir)}"
          f"  -> {v.score}/100 {v.recommendation} ({v.strategy})")


def main() -> int:
    settings = Settings.load()
    # Console : avertissements seulement (les villages sont affichés par print_village) ;
    # fichier de logs : tout depuis INFO.
    configure_logging(settings.logs_dir, console_level=logging.WARNING)
    parser = argparse.ArgumentParser(description="Enregistre automatiquement les villages rencontrés")
    parser.add_argument("--interval", type=float, default=None,
                        help="secondes entre deux analyses (défaut : réglage « fréquence des analyses »)")
    parser.add_argument("--duration", type=float, default=None, help="arrêt automatique après N secondes")
    args = parser.parse_args()

    try:
        models = VisionModels.load()
        db = Database.open(settings.database_path, settings.backups_dir)
    except (TemplatesNotFoundError, MigrationError) as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1

    with db.session() as session:
        interval = load_user_settings(session, settings.data_dir).app.observe_interval_s
    service = ObserverService(settings, db, game_window_frames(settings),
                              lambda bgr: analyze_frame(bgr, models), on_village=print_village)
    try:
        status = service.start(args.interval if args.interval is not None else interval)
    except ObserverError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        db.close()
        return 1

    print(f"Observation en cours (toutes les {status.interval_s} s). Captures : {settings.observations_dir}")
    print("Lance tes recherches dans le jeu. Ctrl+C pour arrêter.")
    started = time.monotonic()
    try:
        while service.status().running and (args.duration is None or time.monotonic() - started < args.duration):
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    finally:
        status = service.stop()
        db.close()

    print(f"\nArrêt après {time.monotonic() - started:.0f} s : {status.frames} analyse(s), "
          f"{status.villages_saved} village(s) enregistré(s), {status.errors} erreur(s), "
          f"fenêtre absente {status.missing_window} fois.")
    if status.last_error:
        print(f"Dernière erreur : {status.last_error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
