"""Tests de la lecture des chiffres (template matching)."""
from pathlib import Path

import cv2
import numpy as np
import pytest
from PIL import Image

from app.vision.dataset import digit_samples, load_labels
from app.vision.digits import GLYPH_SIZE, DigitTemplates, TemplatesNotFoundError, normalize_glyph
from app.vision.preprocess import segment_characters, to_bgr
from app.vision.regions import REGION_SETS
from app.vision.resources import read_resource_counters

LABELS = Path(__file__).resolve().parents[1] / "datasets" / "labels.json"


def _draw_digit(digit: int) -> np.ndarray:
    """Masque binaire d'un chiffre dessiné avec une police OpenCV (données synthétiques)."""
    img = np.zeros((30, 24), np.uint8)
    cv2.putText(img, str(digit), (2, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.9, 1, 2)
    ys, xs = np.nonzero(img)
    return img[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]


@pytest.fixture(scope="module")
def synthetic_templates() -> DigitTemplates:
    return DigitTemplates.build((_draw_digit(d), d) for d in range(10))


def test_normalize_glyph_keeps_proportions():
    thin = normalize_glyph(np.ones((13, 4), np.uint8))
    wide = normalize_glyph(np.ones((13, 11), np.uint8))
    assert thin.shape == wide.shape == (GLYPH_SIZE, GLYPH_SIZE)
    assert thin.sum() < wide.sum()  # un « 1 » reste plus fin qu'un « 0 »


def test_classify_synthetic_digits(synthetic_templates):
    for d in range(10):
        digit, score = synthetic_templates.classify(_draw_digit(d))
        assert digit == d and score > 0.99


def test_read_number(synthetic_templates):
    value, confidence = synthetic_templates.read_number([_draw_digit(d) for d in (4, 0, 7)])
    assert value == 407 and 0.0 <= confidence <= 1.0
    assert synthetic_templates.read_number([]) == (None, 0.0)


def test_build_requires_all_digits():
    with pytest.raises(ValueError, match="9"):
        DigitTemplates.build((_draw_digit(d), d) for d in range(9))


def test_save_and_load_roundtrip(tmp_path, synthetic_templates):
    synthetic_templates.save(tmp_path)
    loaded = DigitTemplates.load(tmp_path)
    assert loaded.classify(_draw_digit(3))[0] == 3


def test_load_missing_templates(tmp_path):
    with pytest.raises(TemplatesNotFoundError):
        DigitTemplates.load(tmp_path)


def test_shipped_templates_exist():
    """Les modèles livrés avec l'application doivent être présents."""
    assert len(DigitTemplates.load().templates) == 10


# --- Captures réelles : évaluation « leave-one-out » -------------------------


@pytest.mark.skipif(not LABELS.exists(), reason="datasets/labels.json absent")
def test_real_captures_leave_one_out():
    """Pour chaque image : modèles construits SANS elle, puis lecture de ses compteurs.

    Mesure la lecture sur des captures jamais vues (plus honnête que de tester
    sur les images ayant servi à construire les modèles).
    """
    counters = load_labels(LABELS)
    images = sorted({c.image_path for c in counters})
    if len(images) < 2:
        pytest.skip("au moins 2 captures annotées nécessaires")

    errors = []
    for image in images:
        templates = DigitTemplates.build(digit_samples([c for c in counters if c.image_path != image]))
        bgr = to_bgr(Image.open(image))
        for c in (c for c in counters if c.image_path == image):
            region = {c.resource: REGION_SETS[c.region_set][c.resource]}
            reading = read_resource_counters(bgr, region, templates)[0]
            if reading.value != c.expected:
                errors.append(f"{image.name}/{c.region_set}/{c.resource.value}: {reading.value} != {c.expected}")
    assert not errors, errors


def test_segment_then_read_synthetic_counter(synthetic_templates):
    """Chaîne complète sur image synthétique : découpage puis lecture."""
    canvas = np.zeros((30, 90), np.uint8)
    for i, d in enumerate((2, 6, 9)):
        glyph = _draw_digit(d)
        canvas[3 : 3 + glyph.shape[0], 5 + i * 26 : 5 + i * 26 + glyph.shape[1]] = glyph
    boxes = segment_characters(canvas, max_aspect=1.2)
    value, _ = synthetic_templates.read_number([canvas[b.y : b.bottom, b.x : b.right] for b in boxes])
    assert value == 269
