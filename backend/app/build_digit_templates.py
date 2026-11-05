"""Génère les modèles de chiffres : `python -m app.build_digit_templates [labels.json]`.

À relancer quand on ajoute des captures annotées dans `datasets/`. Les modèles
produits (backend/app/vision/templates/digits/*.png) sont versionnés et livrés
avec l'application : l'utilisateur final n'a pas besoin des captures.
"""
from __future__ import annotations

import argparse
import logging
from collections import Counter
from pathlib import Path

from app.vision.dataset import digit_samples, load_labels
from app.vision.digits import DEFAULT_TEMPLATES_DIR, DigitTemplates

DEFAULT_LABELS = Path(__file__).resolve().parents[2] / "datasets" / "labels.json"


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Construit les modèles de chiffres")
    parser.add_argument("labels", nargs="?", type=Path, default=DEFAULT_LABELS)
    args = parser.parse_args()

    samples = list(digit_samples(load_labels(args.labels)))
    per_digit = Counter(d for _, d in samples)
    print("Exemples par chiffre :", dict(sorted(per_digit.items())))
    try:
        templates = DigitTemplates.build(samples)
    except ValueError as exc:
        print(f"Erreur : {exc}")
        return 1
    templates.save(DEFAULT_TEMPLATES_DIR)
    print(f"Modèles enregistrés dans {DEFAULT_TEMPLATES_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
