"""Génère tous les modèles de la vision : `python -m app.build_templates [labels.json]`.

- chiffres  -> backend/app/vision/templates/digits/*.png
- écrans    -> backend/app/vision/templates/screens/*.png

À relancer après avoir ajouté des captures annotées dans `datasets/`. Les modèles
produits sont versionnés et livrés avec l'application : l'utilisateur final n'a
pas besoin des captures.
"""
from __future__ import annotations

import argparse
import logging
from collections import Counter
from pathlib import Path

from PIL import Image

from app.vision.dataset import digit_samples, load_labels, load_screen_labels
from app.vision.digits import DEFAULT_TEMPLATES_DIR as DIGITS_DIR
from app.vision.digits import DigitTemplates
from app.vision.preprocess import to_bgr
from app.vision.screen_state import DEFAULT_TEMPLATES_DIR as SCREENS_DIR
from app.vision.screen_state import ScreenTemplates

DEFAULT_LABELS = Path(__file__).resolve().parents[2] / "datasets" / "labels.json"


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Construit les modèles de la vision")
    parser.add_argument("labels", nargs="?", type=Path, default=DEFAULT_LABELS)
    args = parser.parse_args()

    samples = list(digit_samples(load_labels(args.labels)))
    print("Chiffres - exemples par chiffre :", dict(sorted(Counter(d for _, d in samples).items())))

    screen_labels = load_screen_labels(args.labels)
    print("Écrans - captures par écran :", dict(Counter(s.value for _, s in screen_labels)))

    try:
        digits = DigitTemplates.build(samples)
        screens = ScreenTemplates.build((to_bgr(Image.open(p)), s) for p, s in screen_labels)
    except ValueError as exc:
        print(f"Erreur : {exc}")
        return 1
    digits.save(DIGITS_DIR)
    screens.save(SCREENS_DIR)
    print(f"Modèles enregistrés dans {DIGITS_DIR.parent}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
