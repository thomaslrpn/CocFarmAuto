"""Lecture / écriture d'images sur disque.

On passe par Pillow et non par cv2.imread / cv2.imwrite : sous Windows, OpenCV
échoue SILENCIEUSEMENT sur les chemins contenant des accents (ex. « Développement »,
ou un nom de session « Hélène »).
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image


class TemplatesNotFoundError(FileNotFoundError):
    """Des modèles (chiffres, écrans) n'ont pas encore été générés."""


def save_array(array: np.ndarray, path: Path) -> None:
    """Enregistre un tableau OpenCV : niveaux de gris (H, W) ou BGR (H, W, 3).

    Les tableaux float (0.0 à 1.0) sont convertis en 0-255.
    """
    if array.dtype != np.uint8:
        array = np.clip(np.round(array * 255), 0, 255).astype(np.uint8)
    if array.ndim == 3:
        array = cv2.cvtColor(array, cv2.COLOR_BGR2RGB)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(array).save(path)


def load_array(path: Path, grayscale: bool = False) -> np.ndarray:
    """Charge une image en float32 (0.0 à 1.0) : niveaux de gris ou BGR."""
    image = Image.open(path)
    if grayscale:
        return np.asarray(image.convert("L"), np.float32) / 255.0
    rgb = np.asarray(image.convert("RGB"))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR).astype(np.float32) / 255.0
