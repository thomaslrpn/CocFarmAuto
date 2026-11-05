"""Capture du CONTENU d'une fenêtre via l'API Win32 PrintWindow.

Contrairement à une capture d'écran classique, PrintWindow demande à la fenêtre
de se dessiner elle-même dans une image en mémoire : le résultat est correct
même si une autre fenêtre la recouvre (mais pas si elle est réduite).

Limite connue : certains jeux DirectX renvoient une image noire. Le module
`screen.py` détecte ce cas et se replie sur la capture d'écran classique.
"""
from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

from PIL import Image

PW_CLIENTONLY = 0x1  # uniquement la zone cliente (sans barre de titre)
PW_RENDERFULLCONTENT = 0x2  # Windows 8.1+ : nécessaire pour les contenus DirectX
DIB_RGB_COLORS = 0
BI_RGB = 0


class PrintWindowError(RuntimeError):
    """PrintWindow a échoué ou n'est pas disponible."""


class _BitmapInfoHeader(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


def _win32_api():  # type: ignore[no-untyped-def]
    """Charge user32/gdi32 avec des signatures explicites.

    Indispensable en 64 bits : sans `restype`/`argtypes`, ctypes tronque les
    handles (HDC, HBITMAP) à 32 bits et provoque des plantages aléatoires.
    """
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)

    user32.GetDC.restype = wintypes.HDC
    user32.GetDC.argtypes = [wintypes.HWND]
    user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
    user32.PrintWindow.restype = wintypes.BOOL
    user32.PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, wintypes.UINT]

    gdi32.CreateCompatibleDC.restype = wintypes.HDC
    gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
    gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
    gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
    gdi32.SelectObject.restype = wintypes.HGDIOBJ
    gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
    gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
    gdi32.DeleteDC.argtypes = [wintypes.HDC]
    gdi32.GetDIBits.restype = ctypes.c_int
    gdi32.GetDIBits.argtypes = [
        wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT,
        ctypes.c_void_p, ctypes.POINTER(_BitmapInfoHeader), wintypes.UINT,
    ]
    return user32, gdi32


def print_window(hwnd: int, width: int, height: int) -> Image.Image:
    """Retourne le contenu de la zone cliente de `hwnd` (taille `width` x `height`)."""
    if sys.platform != "win32":
        raise PrintWindowError("PrintWindow nécessite Windows")
    if width <= 0 or height <= 0:
        raise PrintWindowError(f"Taille invalide : {width}x{height}")

    user32, gdi32 = _win32_api()
    window_dc = user32.GetDC(hwnd)
    if not window_dc:
        raise PrintWindowError("GetDC a échoué (fenêtre fermée ?)")
    mem_dc = gdi32.CreateCompatibleDC(window_dc)
    bitmap = gdi32.CreateCompatibleBitmap(window_dc, width, height)
    previous = gdi32.SelectObject(mem_dc, bitmap)
    try:
        if not user32.PrintWindow(hwnd, mem_dc, PW_CLIENTONLY | PW_RENDERFULLCONTENT):
            raise PrintWindowError(f"PrintWindow a échoué (code {ctypes.get_last_error()})")

        header = _BitmapInfoHeader()
        header.biSize = ctypes.sizeof(_BitmapInfoHeader)
        header.biWidth = width
        header.biHeight = -height  # négatif = lignes de haut en bas
        header.biPlanes = 1
        header.biBitCount = 32
        header.biCompression = BI_RGB
        buffer = ctypes.create_string_buffer(width * height * 4)
        lines = gdi32.GetDIBits(mem_dc, bitmap, 0, height, buffer, ctypes.byref(header), DIB_RGB_COLORS)
        if lines != height:
            raise PrintWindowError(f"GetDIBits n'a copié que {lines}/{height} lignes")
    finally:
        # Libération systématique des ressources GDI (sinon fuite à chaque capture).
        gdi32.SelectObject(mem_dc, previous)
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(mem_dc)
        user32.ReleaseDC(hwnd, window_dc)

    return Image.frombuffer("RGB", (width, height), buffer.raw, "raw", "BGRX", 0, 1)
