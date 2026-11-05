"""Capture manuelle : `python -m app.capture_cli [--full] [--method auto|window|screen]`.

Cherche la fenêtre du jeu ; sinon (ou avec --full) capture le moniteur principal.
"""
from __future__ import annotations

import argparse
import logging
import sys

from app.capture.screen import CaptureError, CaptureMethod, grab_primary_monitor, grab_window, save_capture
from app.capture.window import WindowNotSupportedError, find_window
from app.config import Settings


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Capture la fenêtre Clash of Clans")
    parser.add_argument("--full", action="store_true", help="capturer tout le moniteur principal")
    parser.add_argument(
        "--method",
        choices=[m.value for m in CaptureMethod],
        default=CaptureMethod.AUTO.value,
        help="auto (défaut) : PrintWindow puis écran ; window : PrintWindow seul ; screen : écran seul",
    )
    args = parser.parse_args()

    settings = Settings.load()
    try:
        window = None if args.full else find_window(settings.game_window_title)
        if window is None:
            print("Fenêtre du jeu non trouvée -> capture du moniteur principal.")
            image, used = grab_primary_monitor(), "moniteur"
        else:
            image, method = grab_window(window, CaptureMethod(args.method))
            used = method.value
        path = save_capture(image, settings.screenshots_dir)
    except WindowNotSupportedError as exc:
        print(f"{exc} -> capture du moniteur principal.")
        path, used = save_capture(grab_primary_monitor(), settings.screenshots_dir), "moniteur"
    except CaptureError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1
    print(f"OK ({used}) : {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
