"""Détection de la fenêtre Google Play Games (Windows uniquement).

Utilise l'API Win32 via ctypes (aucune dépendance externe). Sur un autre OS
(dev macOS), les fonctions lèvent `WindowNotSupportedError` : le reste du
code reste importable et testable.
"""
from __future__ import annotations

import logging
import sys
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class WindowNotSupportedError(RuntimeError):
    """La détection de fenêtre n'est disponible que sous Windows."""


@dataclass(frozen=True)
class WindowRect:
    """Zone écran d'une fenêtre, en pixels."""

    left: int
    top: int
    width: int
    height: int

    def as_mss_region(self) -> dict[str, int]:
        return {"left": self.left, "top": self.top, "width": self.width, "height": self.height}


def find_window(title_fragment: str) -> WindowRect | None:
    """Retourne la zone de la 1re fenêtre visible dont le titre contient
    `title_fragment` (insensible à la casse), ou None si introuvable."""
    if sys.platform != "win32":
        raise WindowNotSupportedError("find_window nécessite Windows")

    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    needle = title_fragment.lower()
    found: list[WindowRect] = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def _callback(hwnd, _lparam):  # type: ignore[no-untyped-def]
        if not user32.IsWindowVisible(hwnd) or user32.IsIconic(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return True
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        if needle in buf.value.lower():
            # Zone CLIENTE (sans barre de titre) convertie en coordonnées écran.
            rect = wintypes.RECT()
            user32.GetClientRect(hwnd, ctypes.byref(rect))
            origin = wintypes.POINT(0, 0)
            user32.ClientToScreen(hwnd, ctypes.byref(origin))
            w, h = rect.right - rect.left, rect.bottom - rect.top
            if w > 0 and h > 0:
                found.append(WindowRect(origin.x, origin.y, w, h))
                return False  # stop l'énumération
        return True

    user32.EnumWindows(_callback, 0)
    if not found:
        logger.warning("Fenêtre '%s' introuvable", title_fragment)
        return None
    return found[0]
