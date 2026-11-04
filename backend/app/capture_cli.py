"""Première capture : `python -m app.capture_cli [--full]`.

Cherche la fenêtre du jeu ; sinon (ou avec --full) capture le moniteur principal.
"""
from __future__ import annotations

import argparse
import logging
import sys

from app.capture.screen import CaptureError, grab_primary_monitor, grab_region, save_capture
from app.capture.window import WindowNotSupportedError, find_window
from app.config import Settings


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Capture la fenêtre Clash of Clans")
    parser.add_argument("--full", action="store_true", help="capturer tout le moniteur principal")
    args = parser.parse_args()

    settings = Settings.load()
    try:
        rect = None if args.full else find_window(settings.game_window_title)
        if rect is None:
            print("Fenêtre du jeu non trouvée -> capture du moniteur principal.")
            image = grab_primary_monitor()
        else:
            image = grab_region(rect)
        path = save_capture(image, settings.screenshots_dir)
    except WindowNotSupportedError as exc:
        print(f"{exc} -> capture du moniteur principal.")
        path = save_capture(grab_primary_monitor(), settings.screenshots_dir)
    except CaptureError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1
    print(f"OK : {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
