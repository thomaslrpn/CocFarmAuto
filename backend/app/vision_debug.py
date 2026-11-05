"""Outil de diagnostic : `python -m app.vision_debug [image.png]`.

Analyse une capture (par défaut la plus récente), affiche les valeurs lues
et enregistre une copie annotée :
- rectangles bleus : zones analysées ;
- rectangles verts : caractères détectés ;
- texte : valeur lue (rouge si la confiance est faible).
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import cv2
from PIL import Image

from app.config import Settings
from app.vision.digits import MIN_RELIABLE_CONFIDENCE, DigitTemplates, TemplatesNotFoundError
from app.vision.preprocess import to_bgr
from app.vision.regions import REGION_SETS
from app.vision.resources import ResourceReading, read_resource_counters

BLUE, GREEN, RED = (255, 120, 0), (0, 220, 0), (0, 0, 255)  # couleurs OpenCV (BGR)


def latest_capture(directory: Path) -> Path | None:
    captures = sorted(directory.glob("capture_*.png"))
    return captures[-1] if captures else None


def annotate(bgr, reading: ResourceReading) -> None:  # type: ignore[no-untyped-def]
    r = reading.region
    cv2.rectangle(bgr, (r.x, r.y), (r.right, r.bottom), BLUE, 1)
    for c in reading.characters:
        cv2.rectangle(bgr, (c.x, c.y), (c.right - 1, c.bottom - 1), GREEN, 1)
    if reading.value is not None:
        color = GREEN if reading.confidence >= MIN_RELIABLE_CONFIDENCE else RED
        cv2.putText(bgr, f"{reading.value:,}".replace(",", " "), (r.right + 4, r.bottom - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1, cv2.LINE_AA)


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

    try:
        templates: DigitTemplates | None = DigitTemplates.load()
    except TemplatesNotFoundError as exc:
        print(f"{exc} -> localisation seule, sans lecture.")
        templates = None

    bgr = to_bgr(Image.open(path))
    print(f"Analyse de {path.name}")
    for set_name, regions in REGION_SETS.items():
        for reading in read_resource_counters(bgr, regions, templates):
            annotate(bgr, reading)
            value = "-" if reading.value is None else f"{reading.value:,}".replace(",", " ")
            flag = "" if reading.confidence >= MIN_RELIABLE_CONFIDENCE else "  (incertain)"
            print(f"  {set_name:<5} {reading.resource.value:<12} {value:>12}  "
                  f"confiance {reading.confidence:.2f}{flag}")

    out_dir = settings.data_dir / "debug"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{path.stem}_debug.png"
    # Pillow plutôt que cv2.imwrite : ce dernier échoue sur les chemins accentués.
    Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)).save(out)
    print(f"Image annotée : {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
