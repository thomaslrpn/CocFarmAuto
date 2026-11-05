"""Traitements d'image génériques (OpenCV / NumPy).

Convention : les images OpenCV sont des tableaux NumPy en BGR (Bleu, Vert, Rouge),
de forme (hauteur, largeur, 3). PIL travaille en RGB : on convertit à l'entrée.
"""
from __future__ import annotations

import cv2
import numpy as np
from PIL import Image

from app.vision.models import Box


def to_bgr(image: Image.Image) -> np.ndarray:
    """Convertit une image PIL en tableau OpenCV BGR."""
    return cv2.cvtColor(np.asarray(image.convert("RGB")), cv2.COLOR_RGB2BGR)


def crop(image: np.ndarray, box: Box) -> np.ndarray:
    """Découpe `box` dans l'image (bornée aux dimensions de l'image)."""
    h, w = image.shape[:2]
    x0, y0 = max(0, box.x), max(0, box.y)
    x1, y1 = min(w, box.right), min(h, box.bottom)
    return image[y0:y1, x0:x1]


def white_text_mask(bgr: np.ndarray, min_value: int = 200, max_saturation: int = 60) -> np.ndarray:
    """Masque binaire (0/1) des pixels « blanc texte » : très clairs et peu colorés.

    Les nombres de CoC sont blancs avec un contour sombre : en HSV, ils ont une
    valeur (luminosité) élevée et une saturation faible, ce qui les sépare des
    barres colorées (or jaune, élixir rose) situées derrière.
    """
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask = (hsv[..., 2] >= min_value) & (hsv[..., 1] <= max_saturation)
    return mask.astype(np.uint8)


def segment_characters(
    mask: np.ndarray,
    min_height: int = 7,
    min_pixels: int = 8,
    max_aspect: float = 1.0,
    height_tolerance: float = 0.25,
) -> list[Box]:
    """Découpe un masque de texte en caractères, triés de gauche à droite.

    1. Composantes connexes : chaque « tache » blanche isolée = un candidat.
    2. On écarte le bruit : trop petit, ou plus large que haut (icônes, « + »...).
    3. On ne garde que les candidats de hauteur proche de la hauteur médiane
       (les chiffres d'un même nombre ont tous la même taille).
    """
    count, _labels, stats, _centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    candidates = [
        Box(int(x), int(y), int(w), int(h))
        for x, y, w, h, area in stats[1:]  # stats[0] = le fond
        if h >= min_height and area >= min_pixels and w <= h * max_aspect
    ]
    if not candidates:
        return []
    median_h = float(np.median([b.height for b in candidates]))
    kept = [b for b in candidates if abs(b.height - median_h) <= median_h * height_tolerance]
    return sorted(kept, key=lambda b: b.x)


def similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Ressemblance entre deux images de MÊME taille, de 0.0 (rien à voir) à 1.0 (identiques).

    Corrélation normalisée (cv2.TM_CCOEFF_NORMED) : insensible à un écart global
    de luminosité, ce qui tolère de petites variations d'affichage.
    """
    if a.std() == 0 or b.std() == 0:  # image uniforme : corrélation indéfinie
        return 0.0
    score = float(cv2.matchTemplate(a.astype(np.float32), b.astype(np.float32), cv2.TM_CCOEFF_NORMED)[0, 0])
    return max(0.0, score)
