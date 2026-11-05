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


@dataclass(frozen=True)
class GameWindow:
    """Fenêtre trouvée : son handle Win32 (pour PrintWindow) et sa zone cliente à l'écran."""

    hwnd: int
    title: str
    rect: WindowRect


def ensure_dpi_awareness() -> None:
    """Rend le processus « DPI aware » pour obtenir des coordonnées en vrais pixels.

    Sans ça, avec une mise à l'échelle Windows de 125 % / 150 %, Windows renvoie
    des tailles « virtuelles » et la capture serait décalée ou floue.
    """
    if sys.platform != "win32":
        return
    import ctypes

    try:
        # -4 = DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 (Windows 10 1703+)
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except (AttributeError, OSError):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            logger.debug("Impossible de régler la DPI awareness", exc_info=True)


def find_window(title_fragment: str) -> GameWindow | None:
    """Retourne la 1re fenêtre visible (non réduite) dont le titre contient
    `title_fragment` (insensible à la casse), ou None si introuvable."""
    if sys.platform != "win32":
        raise WindowNotSupportedError("find_window nécessite Windows")

    import ctypes
    from ctypes import wintypes

    ensure_dpi_awareness()
    user32 = ctypes.windll.user32
    needle = title_fragment.lower()
    found: list[GameWindow] = []

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
                found.append(GameWindow(int(hwnd), buf.value, WindowRect(origin.x, origin.y, w, h)))
                return False  # stop l'énumération
        return True

    user32.EnumWindows(_callback, 0)
    if not found:
        logger.warning("Fenêtre '%s' introuvable", title_fragment)
        return None
    return found[0]
