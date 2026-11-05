"""Outil de diagnostic : `python -m app.vision_debug [image.png]`.

Analyse une capture (par défaut la plus récente) et enregistre une copie annotée :
- rectangles bleus : zones analysées ;
- rectangles verts : caractères détectés.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import cv2
from PIL import Image

from app.config import Settings
from app.vision.preprocess import to_bgr
from app.vision.regions import HOME_RESOURCE_REGIONS
from app.vision.resources import locate_resource_counters

BLUE, GREEN = (255, 120, 0), (0, 220, 0)  # couleurs OpenCV (BGR)


def latest_capture(directory: Path) -> Path | None:
    captures = sorted(directory.glob("capture_*.png"))
    return captures[-1] if captures else None


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Diagnostic de la reconnaissance des ressources")
    parser.add_argument("image", nargs="?", type=Path, help="capture à analyser (défaut : la plus récente)")
    args = parser.parse_args()

    settings = Settings.load()
    path = args.image or latest_capture(settings.screenshots_dir)
    if path is None or not path.is_file():
        print(f"Aucune capture trouvée ({path or settings.screenshots_dir})", file=sys.stderr)
        return 1

    bgr = to_bgr(Image.open(path))
    readings = locate_resource_counters(bgr, HOME_RESOURCE_REGIONS)

    for r in readings:
        cv2.rectangle(bgr, (r.region.x, r.region.y), (r.region.right, r.region.bottom), BLUE, 1)
        for c in r.characters:
            cv2.rectangle(bgr, (c.x, c.y), (c.right - 1, c.bottom - 1), GREEN, 1)
        print(f"{r.resource.value:<12} {len(r.characters)} caractère(s)")

    out_dir = settings.data_dir / "debug"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{path.stem}_debug.png"
    cv2.imwrite(str(out), bgr)
    print(f"Image annotée : {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
