"""Capture d'écran (MSS) : fenêtre du jeu ou région, avec horodatage."""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import mss
from PIL import Image

from app.capture.window import WindowRect

logger = logging.getLogger(__name__)


class CaptureError(RuntimeError):
    """Échec de capture (région invalide, écran indisponible...)."""


def grab_region(rect: WindowRect) -> Image.Image:
    """Capture une région de l'écran et la retourne en image RGB."""
    if rect.width <= 0 or rect.height <= 0:
        raise CaptureError(f"Région invalide : {rect}")
    try:
        with mss.mss() as sct:
            shot = sct.grab(rect.as_mss_region())
    except Exception as exc:  # mss lève des exceptions variées selon l'OS
        raise CaptureError(f"Capture impossible : {exc}") from exc
    return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")


def grab_primary_monitor() -> Image.Image:
    """Capture le moniteur principal (repli quand la fenêtre est introuvable)."""
    try:
        with mss.mss() as sct:
            mon = sct.monitors[1]
            shot = sct.grab(mon)
    except Exception as exc:
        raise CaptureError(f"Capture impossible : {exc}") from exc
    return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")


def save_capture(image: Image.Image, directory: Path) -> Path:
    """Enregistre l'image en PNG horodaté dans `directory` et retourne son chemin."""
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = directory / f"capture_{stamp}.png"
    image.save(path, format="PNG")
    logger.info("Capture enregistrée : %s (%dx%d)", path, *image.size)
    return path
