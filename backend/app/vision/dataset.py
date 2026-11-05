"""Captures réelles annotées (`datasets/labels.json`).

Format : {"captures": {"<fichier>.png": {"screen": "<écran>", "<jeu de zones>": {"<ressource>": valeur}}}}
où l'écran est une valeur de `GameScreen` (home, scout, battle) et le jeu de
zones une clé de `REGION_SETS` ("home", "loot").
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
from app.vision.screen_state import GameScreen

logger = logging.getLogger(__name__)

SCREEN_KEY = "screen"


@dataclass(frozen=True)
class LabeledCounter:
    """Un compteur annoté : quelle image, quelle zone, quelle valeur attendue."""

    image_path: Path
    region_set: str
    resource: ElementType
    expected: int


def _available_captures(labels_path: Path) -> Iterator[tuple[Path, dict]]:
    """(chemin, annotations) de chaque capture présente sur le disque."""
    data = json.loads(labels_path.read_text(encoding="utf-8"))
    for filename, annotations in data["captures"].items():
        image_path = labels_path.parent / filename
        if not image_path.is_file():
            logger.warning("Capture annotée absente : %s", image_path)
            continue
        yield image_path, annotations


def load_screen_labels(labels_path: Path) -> list[tuple[Path, GameScreen]]:
    """(capture, écran attendu) pour chaque capture annotée avec la clé « screen »."""
    return [
        (path, GameScreen(annotations[SCREEN_KEY]))
        for path, annotations in _available_captures(labels_path)
        if SCREEN_KEY in annotations
    ]


def load_labels(labels_path: Path) -> list[LabeledCounter]:
    """Compteurs de ressources annotés. Ignore (avec un avertissement) les images absentes."""
    counters: list[LabeledCounter] = []
    for image_path, annotations in _available_captures(labels_path):
        filename = image_path.name
        for region_set, values in annotations.items():
            if region_set == SCREEN_KEY:
                continue
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
