"""Tests de la reconnaissance d'écran et de l'analyse complète d'une capture."""
from collections import Counter
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from app.vision.dataset import load_screen_labels
from app.vision.frame import VisionModels, analyze_frame
from app.vision.image_io import load_array, save_array
from app.vision.preprocess import to_bgr
from app.vision.screen_state import SIGNATURES, GameScreen, ScreenTemplates

LABELS = Path(__file__).resolve().parents[1] / "datasets" / "labels.json"
W, H = 1323, 744


def _synthetic_screen(screen: GameScreen, seed: int = 0) -> np.ndarray:
    """Fond aléatoire + motif propre à `screen` dans les zones de SES signatures."""
    rng = np.random.default_rng(seed)
    img = rng.integers(0, 255, (H, W, 3), dtype=np.uint8)
    pattern_rng = np.random.default_rng(1000 + list(GameScreen).index(screen))
    for sig in SIGNATURES:
        if sig.screen is screen:
            box = sig.region.to_box(W, H)
            img[box.y : box.bottom, box.x : box.right] = pattern_rng.integers(
                0, 255, (box.height, box.width, 3), dtype=np.uint8
            )
    return img


@pytest.fixture(scope="module")
def synthetic_templates() -> ScreenTemplates:
    screens = (GameScreen.HOME, GameScreen.SCOUT, GameScreen.BATTLE)
    return ScreenTemplates.build((_synthetic_screen(s), s) for s in screens)


@pytest.mark.parametrize("screen", [GameScreen.HOME, GameScreen.SCOUT, GameScreen.BATTLE])
def test_detect_synthetic_screens(synthetic_templates, screen):
    result = synthetic_templates.detect(_synthetic_screen(screen, seed=42))
    assert result.screen is screen and result.confidence > 0.95


def test_unrecognized_screen_is_unknown(synthetic_templates):
    black = np.zeros((H, W, 3), np.uint8)
    assert synthetic_templates.detect(black).screen is GameScreen.UNKNOWN


def test_detection_works_at_another_resolution(synthetic_templates):
    """Les zones sont relatives : une capture 2x plus grande doit être reconnue."""
    big = np.kron(_synthetic_screen(GameScreen.SCOUT, seed=7), np.ones((2, 2, 1), np.uint8))
    assert synthetic_templates.detect(big).screen is GameScreen.SCOUT


def test_build_requires_every_screen():
    with pytest.raises(ValueError):
        ScreenTemplates.build([(_synthetic_screen(GameScreen.HOME), GameScreen.HOME)])


def test_image_io_handles_accented_paths(tmp_path):
    """Régression : cv2.imwrite échouait silencieusement sur « Développement »."""
    path = tmp_path / "Développement" / "modèle.png"
    array = np.random.default_rng(0).random((8, 6, 3)).astype(np.float32)
    save_array(array, path)
    assert np.allclose(load_array(path), array, atol=1 / 255)


def test_shipped_screen_templates_exist():
    assert len(ScreenTemplates.load().templates) == len(SIGNATURES)


# --- Captures réelles --------------------------------------------------------

requires_dataset = pytest.mark.skipif(not LABELS.exists(), reason="datasets/labels.json absent")


@requires_dataset
def test_real_screens_leave_one_out():
    """Pour chaque capture dont l'écran a au moins 2 exemples : modèles construits
    SANS elle, puis reconnaissance."""
    labels = load_screen_labels(LABELS)
    per_screen = Counter(s for _, s in labels)
    images = {p: to_bgr(Image.open(p)) for p, _ in labels}
    tested = 0
    for path, expected in labels:
        if per_screen[expected] < 2:
            continue  # un seul exemple (ex. combat) : impossible de l'exclure
        templates = ScreenTemplates.build((images[p], s) for p, s in labels if p != path)
        assert templates.detect(images[path]).screen is expected, path.name
        tested += 1
    if tested == 0:
        pytest.skip("pas assez de captures annotées")


@requires_dataset
def test_real_frames_full_analysis():
    """Modèles livrés : bon écran, ressources du joueur lues hors écran inconnu,
    butin lu seulement en recherche / combat."""
    models = VisionModels.load()
    for path, expected in load_screen_labels(LABELS):
        analysis = analyze_frame(to_bgr(Image.open(path)), models)
        assert analysis.screen.screen is expected, path.name
        has_player = expected is not GameScreen.UNKNOWN
        assert (len(analysis.player_resources) == 3) == has_player, path.name
        has_loot = expected in (GameScreen.SCOUT, GameScreen.BATTLE)
        assert (len(analysis.loot) == 3) == has_loot, path.name
