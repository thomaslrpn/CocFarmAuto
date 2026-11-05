"""Reconnaissance à plusieurs tailles de fenêtre.

Les captures annotées (1323x744) sont redimensionnées aux tailles courantes de la
fenêtre du jeu, puis relues : écran et valeurs doivent être exacts. Taille minimale
prise en charge : 960x540 (en dessous, les chiffres font moins de 10 pixels).
Les captures ne sont pas versionnées : le test est ignoré si elles sont absentes.
"""
import json
from pathlib import Path

import cv2
import numpy as np
import pytest
from PIL import Image

from app.vision.frame import VisionModels, analyze_frame
from app.vision.models import Box
from app.vision.preprocess import to_bgr
from app.vision.resources import extract_characters

DATASETS_DIR = Path(__file__).resolve().parents[1] / "datasets"
LABELS = DATASETS_DIR / "labels.json"
SIZES = [(960, 540), (1280, 720), (1600, 900), (1920, 1080), (2560, 1440)]


def _labeled_captures() -> list[tuple[Path, dict]]:
    if not LABELS.exists():
        return []
    captures = json.loads(LABELS.read_text(encoding="utf-8"))["captures"]
    return [(DATASETS_DIR / name, ann) for name, ann in captures.items() if (DATASETS_DIR / name).exists()]


CAPTURES = _labeled_captures()


@pytest.fixture(scope="module")
def models() -> VisionModels:
    return VisionModels.load()


@pytest.mark.skipif(not CAPTURES, reason="captures annotées absentes (datasets/ non versionné)")
@pytest.mark.parametrize("size", SIZES, ids=lambda s: f"{s[0]}x{s[1]}")
def test_reading_is_exact_at_common_window_sizes(models, size):
    errors = []
    for path, annotations in CAPTURES:
        bgr = to_bgr(Image.open(path))
        interpolation = cv2.INTER_AREA if size[0] < bgr.shape[1] else cv2.INTER_CUBIC
        frame = analyze_frame(cv2.resize(bgr, size, interpolation=interpolation), models)
        if "screen" in annotations and frame.screen.screen.value != annotations["screen"]:
            errors.append(f"{path.name}: écran {frame.screen.screen.value}")
        for key, readings in (("home", frame.player_resources), ("loot", frame.loot)):
            values = {r.resource.value: r.value for r in readings}
            for resource, expected in annotations.get(key, {}).items():
                if values.get(resource) != expected:
                    errors.append(f"{path.name}/{key}/{resource}: {values.get(resource)} au lieu de {expected}")
    assert not errors, errors


def test_small_window_boxes_are_in_image_coordinates():
    """Petite fenêtre : la zone est agrandie pour la lecture, mais les boîtes renvoyées
    restent dans les coordonnées de l'image d'origine."""
    image = np.zeros((372, 662, 3), np.uint8)  # moitié de la référence 1323x744
    cv2.rectangle(image, (110, 50), (114, 60), (255, 255, 255), -1)  # « 1 » de 11 px de haut
    cv2.rectangle(image, (120, 50), (126, 60), (255, 255, 255), -1)
    region = Box(100, 40, 40, 30)
    chars = extract_characters(image, region)
    assert len(chars) == 2
    first = chars[0][0]
    assert abs(first.x - 110) <= 1 and abs(first.y - 50) <= 1 and abs(first.height - 11) <= 1
