"""Capture d'écran : fenêtre du jeu (PrintWindow ou MSS) ou région, avec horodatage."""
from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from pathlib import Path

import mss
import numpy as np
from PIL import Image

from app.capture.printwindow import PrintWindowError, print_window
from app.capture.window import GameWindow, WindowRect

logger = logging.getLogger(__name__)

# En dessous de cette luminosité maximale, on considère l'image comme « noire ».
BLANK_MAX_BRIGHTNESS = 8


class CaptureError(RuntimeError):
    """Échec de capture (région invalide, écran indisponible...)."""


class CaptureMethod(str, Enum):
    """Méthode de capture de la fenêtre du jeu."""

    AUTO = "auto"  # PrintWindow, puis repli sur l'écran si échec / image noire
    WINDOW = "window"  # PrintWindow uniquement (fonctionne si la fenêtre est recouverte)
    SCREEN = "screen"  # pixels de l'écran à l'emplacement de la fenêtre (MSS)


def is_blank(image: Image.Image) -> bool:
    """Vrai si l'image est (quasi) entièrement noire : signe d'un PrintWindow raté."""
    return int(np.asarray(image.convert("L")).max()) <= BLANK_MAX_BRIGHTNESS


def grab_window(window: GameWindow, method: CaptureMethod = CaptureMethod.AUTO) -> tuple[Image.Image, CaptureMethod]:
    """Capture la fenêtre du jeu. Retourne l'image et la méthode réellement utilisée."""
    rect = window.rect
    if method in (CaptureMethod.AUTO, CaptureMethod.WINDOW):
        try:
            image = print_window(window.hwnd, rect.width, rect.height)
            if not is_blank(image):
                return image, CaptureMethod.WINDOW
            reason = "image noire (rendu DirectX non capturé)"
        except PrintWindowError as exc:
            reason = str(exc)
        if method is CaptureMethod.WINDOW:
            raise CaptureError(f"PrintWindow inutilisable : {reason}")
        logger.warning("PrintWindow inutilisable (%s) -> capture écran", reason)
    return grab_region(rect), CaptureMethod.SCREEN


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
