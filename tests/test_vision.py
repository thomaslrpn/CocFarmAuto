"""Tests du module vision : images synthétiques + (si présente) une capture réelle."""
from pathlib import Path

import cv2
import numpy as np
import pytest
from PIL import Image
from pydantic import ValidationError

from app.vision.models import Box, Detection, ElementType
from app.vision.preprocess import segment_characters, to_bgr, white_text_mask
from app.vision.regions import HOME_RESOURCE_REGIONS, RelativeRegion
from app.vision.resources import locate_resource_counters

# Captures réelles (dossier ignoré par Git : données personnelles).
DATASETS_DIR = Path(__file__).resolve().parents[1] / "datasets"

# --- Régions relatives -------------------------------------------------------


def test_relative_region_scales_with_resolution():
    region = RelativeRegion(0.5, 0.5, 1.0, 1.0)
    assert region.to_box(200, 100) == Box(100, 50, 100, 50)
    assert region.to_box(1920, 1080) == Box(960, 540, 960, 540)


def test_relative_region_rejects_invalid_values():
    with pytest.raises(ValueError):
        RelativeRegion(0.8, 0.1, 0.2, 0.5)  # gauche > droite


# --- Modèle Detection --------------------------------------------------------


def test_detection_from_box_and_validation():
    det = Detection.from_box(ElementType.GOLD, Box(10, 20, 30, 40), confidence=0.9, value=1500)
    assert (det.x, det.y, det.width, det.height, det.value) == (10, 20, 30, 40, 1500)
    with pytest.raises(ValidationError):
        Detection.from_box(ElementType.GOLD, Box(0, 0, 5, 5), confidence=1.5)


# --- Segmentation sur image synthétique -------------------------------------


def _synthetic_counter(digits: int, with_icon: bool = True) -> np.ndarray:
    """Fond coloré (barre d'or) + `digits` rectangles blancs 8x13 + une « icône » large."""
    img = np.zeros((30, 200, 3), np.uint8)
    img[:] = (0, 190, 230)  # jaune en BGR, saturé : ne doit pas être pris pour du texte
    for i in range(digits):
        x = 40 + i * 12
        cv2.rectangle(img, (x, 8), (x + 7, 20), (255, 255, 255), -1)
    if with_icon:
        cv2.rectangle(img, (5, 9), (25, 20), (255, 255, 255), -1)  # plus large que haute
    return img


def test_white_text_mask_ignores_colored_background():
    img = _synthetic_counter(0, with_icon=False)
    assert white_text_mask(img).sum() == 0


def test_segment_characters_counts_and_orders_digits():
    boxes = segment_characters(white_text_mask(_synthetic_counter(6)))
    assert len(boxes) == 6  # l'icône large est écartée
    assert [b.x for b in boxes] == sorted(b.x for b in boxes)
    assert all(b.height == 13 for b in boxes)


def test_segment_characters_on_empty_mask():
    assert segment_characters(np.zeros((20, 50), np.uint8)) == []


# --- Capture réelle (optionnelle, données locales non versionnées) ----------

REAL_HOME = DATASETS_DIR / "home_village_1323x744.png"


@pytest.mark.skipif(not REAL_HOME.exists(), reason=f"capture réelle absente : {REAL_HOME}")
def test_real_home_village_counters():
    """Capture réelle : or 23 371 657, élixir 22 440 000, élixir noir 324 143."""
    readings = locate_resource_counters(to_bgr(Image.open(REAL_HOME)), HOME_RESOURCE_REGIONS)
    counts = {r.resource: len(r.characters) for r in readings}
    assert counts == {ElementType.GOLD: 8, ElementType.ELIXIR: 8, ElementType.DARK_ELIXIR: 6}
