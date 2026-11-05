"""Mode observation : `python -m app.observe_cli [--interval 1.0] [--duration 600]`.

Analyse la fenêtre du jeu à intervalle régulier et enregistre chaque nouvel
écran de recherche. Lecture seule : aucune action n'est envoyée au jeu.
Arrêt : Ctrl+C (ou fin de --duration).
"""
from __future__ import annotations

import argparse
import logging
import sys
import time

from app.analysis.scoring import ScoringPreferences, load_preferences
from app.analysis.village_analysis import sheet_from_frame
from app.capture.screen import CaptureError, grab_window
from app.capture.window import WindowNotSupportedError, find_window
from app.config import Settings
from app.database.database import Database
from app.database.migrations import MigrationError
from app.database.repository import refresh_daily_statistics, save_evaluation
from app.observer import ObserverStats, ScoutRecorder
from app.strategy.advisor import evaluate_village
from app.strategy.strategies import strategy_label
from app.vision.frame import VisionModels, analyze_frame
from app.vision.image_io import TemplatesNotFoundError
from app.vision.preprocess import to_bgr

logger = logging.getLogger("app.observe")


def fmt(value: int | None) -> str:
    return "?" if value is None else f"{value:,}".replace(",", " ")


def observe_once(
    settings: Settings,
    models: VisionModels,
    recorder: ScoutRecorder,
    stats: ObserverStats,
    prefs: ScoringPreferences,
    db: Database,
) -> None:
    """Un cycle : trouver la fenêtre, capturer, analyser, enregistrer si besoin."""
    window = find_window(settings.game_window_title)
    if window is None:
        stats.missing_window += 1
        return
    image, _method = grab_window(window)
    bgr = to_bgr(image)
    analysis = analyze_frame(bgr, models)
    stats.frames += 1
    json_path = recorder.process(bgr, analysis)
    if json_path is not None:
        stats.saved += 1
        gold, elixir, dark = (r.value for r in analysis.loot)
        sheet = sheet_from_frame(analysis, source_image=json_path.with_suffix(".png").name)
        verdict = ""
        if sheet is not None:
            evaluation = evaluate_village(sheet, prefs)
            with db.session() as session:  # enregistrement en base + statistiques du jour
                save_evaluation(session, evaluation, prefs)
                refresh_daily_statistics(session, sheet.analyzed_at.date())
            result = evaluation.result
            verdict = (f"  -> {result.score}/100 {result.recommendation.value}"
                       f" ({strategy_label(evaluation.strategy.key if evaluation.strategy else None)})")
        print(f"[{time.strftime('%H:%M:%S')}] Village n°{stats.saved} : "
              f"or {fmt(gold)} | élixir {fmt(elixir)} | noir {fmt(dark)}{verdict}")


def main() -> int:
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = Settings.load()
    parser = argparse.ArgumentParser(description="Enregistre automatiquement les villages rencontrés")
    parser.add_argument("--interval", type=float, default=settings.observe_interval_s,
                        help="secondes entre deux analyses (défaut : %(default)s)")
    parser.add_argument("--duration", type=float, default=None, help="arrêt automatique après N secondes")
    args = parser.parse_args()
    if args.interval < 0.2:
        parser.error("--interval doit être d'au moins 0.2 seconde")

    try:
        models = VisionModels.load()
    except TemplatesNotFoundError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1

    try:
        db = Database.open(settings.database_path, settings.backups_dir)
    except MigrationError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1

    recorder = ScoutRecorder(settings.observations_dir)
    prefs = load_preferences(settings.data_dir)
    stats = ObserverStats()
    print(f"Observation en cours (toutes les {args.interval} s). Enregistrement dans :")
    print(f"  {settings.observations_dir}")
    print("Lance tes recherches dans le jeu. Ctrl+C pour arrêter.")

    started = time.monotonic()
    try:
        while args.duration is None or time.monotonic() - started < args.duration:
            cycle_start = time.monotonic()
            try:
                observe_once(settings, models, recorder, stats, prefs, db)
            except WindowNotSupportedError as exc:
                print(f"Erreur : {exc}", file=sys.stderr)
                return 1
            except CaptureError as exc:  # erreur ponctuelle : on continue
                stats.errors += 1
                logger.warning("Capture impossible : %s", exc)
            if stats.missing_window == 1 and stats.frames == 0:
                print("Fenêtre du jeu introuvable : lance Clash of Clans (on réessaie en continu).")
            time.sleep(max(0.0, args.interval - (time.monotonic() - cycle_start)))
    except KeyboardInterrupt:
        pass
    finally:
        db.close()

    elapsed = time.monotonic() - started
    print(f"\nArrêt après {elapsed:.0f} s : {stats.frames} analyse(s), {stats.saved} village(s) enregistré(s), "
          f"{stats.errors} erreur(s), fenêtre absente {stats.missing_window} fois.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
