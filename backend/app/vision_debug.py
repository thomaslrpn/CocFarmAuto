"""Outil de diagnostic : `python -m app.vision_debug [image.png]`.

Analyse une capture (par défaut la plus récente), affiche l'écran reconnu et
les valeurs lues, et enregistre une copie annotée :
- rectangles bleus : zones analysées ; verts : caractères détectés ;
- encadré en haut au centre : écran reconnu et valeurs (rouge = incertain).
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from app.config import Settings
from app.vision.digits import MIN_RELIABLE_CONFIDENCE
from app.vision.frame import FrameAnalysis, VisionModels, analyze_frame
from app.vision.image_io import TemplatesNotFoundError, save_array
from app.vision.preprocess import to_bgr
from app.vision.resources import ResourceReading

BLUE, GREEN, RED, WHITE = (255, 120, 0), (0, 220, 0), (0, 0, 255), (255, 255, 255)  # BGR


def latest_capture(directory: Path) -> Path | None:
    captures = sorted(directory.glob("capture_*.png"))
    return captures[-1] if captures else None


def fmt(value: int | None) -> str:
    return "-" if value is None else f"{value:,}".replace(",", " ")


def summary_lines(analysis: FrameAnalysis) -> list[tuple[str, bool]]:
    """Lignes de résumé (texte, fiable ?) : partagées entre console et image."""
    s = analysis.screen
    lines = [(f"ecran: {s.screen.value} ({s.confidence:.2f})", s.screen.value != "unknown")]
    for label, readings in (("joueur", analysis.player_resources), ("butin", analysis.loot)):
        for r in readings:
            ok = r.confidence >= MIN_RELIABLE_CONFIDENCE
            lines.append((f"{label} {r.resource.value:<11} {fmt(r.value):>11}  ({r.confidence:.2f})", ok))
    return lines


def draw_regions(bgr: np.ndarray, readings: list[ResourceReading]) -> None:
    for reading in readings:
        r = reading.region
        cv2.rectangle(bgr, (r.x, r.y), (r.right, r.bottom), BLUE, 1)
        for c in reading.characters:
            cv2.rectangle(bgr, (c.x, c.y), (c.right - 1, c.bottom - 1), GREEN, 1)


def draw_panel(bgr: np.ndarray, lines: list[tuple[str, bool]]) -> None:
    """Encadré semi-transparent en haut au centre (OpenCV : texte ASCII uniquement)."""
    x0, y0, line_h = bgr.shape[1] // 2 - 170, 70, 16
    overlay = bgr.copy()
    cv2.rectangle(overlay, (x0, y0), (x0 + 340, y0 + 8 + line_h * len(lines)), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, bgr, 0.4, 0, dst=bgr)
    for i, (text, ok) in enumerate(lines):
        cv2.putText(bgr, text, (x0 + 8, y0 + line_h * (i + 1)), cv2.FONT_HERSHEY_SIMPLEX, 0.42,
                    WHITE if ok else RED, 1, cv2.LINE_AA)


def main() -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Diagnostic de la reconnaissance visuelle")
    parser.add_argument("image", nargs="?", type=Path, help="capture à analyser (défaut : la plus récente)")
    args = parser.parse_args()

    settings = Settings.load()
    path = args.image or latest_capture(settings.screenshots_dir)
    if path is None or not path.is_file():
        print(f"Aucune capture trouvée ({path or settings.screenshots_dir})", file=sys.stderr)
        return 1
    try:
        models = VisionModels.load()
    except TemplatesNotFoundError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1

    bgr = to_bgr(Image.open(path))
    analysis = analyze_frame(bgr, models)
    lines = summary_lines(analysis)

    print(f"Analyse de {path.name}")
    for text, ok in lines:
        print(f"  {text}{'' if ok else '  <- incertain'}")

    draw_regions(bgr, analysis.player_resources + analysis.loot)
    draw_panel(bgr, lines)
    out = settings.data_dir / "debug" / f"{path.stem}_debug.png"
    save_array(bgr, out)
    print(f"Image annotée : {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
