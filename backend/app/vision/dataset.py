"""Captures réelles annotées (`datasets/labels.json`).

Format : {"captures": {"<fichier>.png": {"<jeu de zones>": {"<ressource>": valeur}}}}
où le jeu de zones est une clé de `REGION_SETS` ("home", "loot").
"""
from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from app.vision.models import ElementType
from app.vision.preprocess import to_bgr
from app.vision.regions import REGION_SETS
from app.vision.resources import extract_characters

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LabeledCounter:
    """Un compteur annoté : quelle image, quelle zone, quelle valeur attendue."""

    image_path: Path
    region_set: str
    resource: ElementType
    expected: int


def load_labels(labels_path: Path) -> list[LabeledCounter]:
    """Lit le fichier d'annotations. Ignore (avec un avertissement) les images absentes."""
    data = json.loads(labels_path.read_text(encoding="utf-8"))
    counters: list[LabeledCounter] = []
    for filename, sets in data["captures"].items():
        image_path = labels_path.parent / filename
        if not image_path.is_file():
            logger.warning("Capture annotée absente : %s", image_path)
            continue
        for region_set, values in sets.items():
            if region_set not in REGION_SETS:
                raise ValueError(f"{filename} : jeu de zones inconnu '{region_set}'")
            for resource, expected in values.items():
                counters.append(LabeledCounter(image_path, region_set, ElementType(resource), int(expected)))
    return counters


def digit_samples(counters: list[LabeledCounter]) -> Iterator[tuple[np.ndarray, int]]:
    """Produit des couples (masque d'un caractère, chiffre attendu).

    Un compteur n'est utilisé que si le nombre de caractères découpés correspond
    au nombre de chiffres attendus : sinon l'association serait fausse.
    """
    images: dict[Path, np.ndarray] = {}
    for c in counters:
        if c.image_path not in images:
            images[c.image_path] = to_bgr(Image.open(c.image_path))
        bgr = images[c.image_path]
        region = REGION_SETS[c.region_set][c.resource].to_box(bgr.shape[1], bgr.shape[0])
        chars = extract_characters(bgr, region)
        digits = str(c.expected)
        if len(chars) != len(digits):
            logger.warning(
                "%s/%s/%s : %d caractère(s) découpé(s) pour '%s' -> ignoré",
                c.image_path.name, c.region_set, c.resource.value, len(chars), digits,
            )
            continue
        for (_box, mask), digit in zip(chars, digits):
            yield mask, int(digit)
