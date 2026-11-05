"""Lecture des compteurs de ressources (or, élixir, élixir noir).

Fonctionne pour toute zone définie dans `regions.py` : ressources du joueur
(en haut à droite) ou butin disponible chez l'adversaire (en haut à gauche).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import cv2
import numpy as np

from app.vision.digits import DigitTemplates
from app.vision.models import Box, Detection, ElementType
from app.vision.preprocess import crop, segment_characters, white_text_mask
from app.vision.regions import REFERENCE_HEIGHT, RelativeRegion

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResourceReading:
    """Résultat pour un compteur : zone analysée, chiffres trouvés, valeur lue."""

    resource: ElementType
    region: Box
    characters: list[Box]  # coordonnées dans l'image entière
    value: int | None = None  # None si aucun modèle fourni ou rien trouvé
    confidence: float = 0.0  # confiance du chiffre le MOINS sûr

    @property
    def text_box(self) -> Box | None:
        """Rectangle englobant tous les chiffres, ou None si rien trouvé."""
        if not self.characters:
            return None
        x0 = min(b.x for b in self.characters)
        y0 = min(b.y for b in self.characters)
        x1 = max(b.right for b in self.characters)
        y1 = max(b.bottom for b in self.characters)
        return Box(x0, y0, x1 - x0, y1 - y0)

    def to_detection(self) -> Detection | None:
        """Convertit en `Detection` (format commun du module vision)."""
        box = self.text_box
        if box is None or self.value is None:
            return None
        return Detection.from_box(self.resource, box, confidence=self.confidence, value=self.value)


def _scale_box(box: Box, factor: float) -> Box:
    return Box(round(box.x * factor), round(box.y * factor),
               max(1, round(box.width * factor)), max(1, round(box.height * factor)))


def extract_characters(bgr: np.ndarray, region: Box) -> list[tuple[Box, np.ndarray]]:
    """Découpe les caractères d'une zone. Retourne (boîte dans l'image, masque du caractère).

    Petite fenêtre : la zone est d'abord agrandie à l'échelle de référence (fenêtre
    haute de REFERENCE_HEIGHT pixels), pour que les seuils de découpe (hauteur
    minimale d'un chiffre...) s'appliquent à l'identique. Les boîtes renvoyées sont
    remises à l'échelle de l'image.
    """
    patch = crop(bgr, region)
    scale = REFERENCE_HEIGHT / bgr.shape[0]
    if scale > 1.0 and patch.size:
        patch = cv2.resize(patch, None, fx=scale, fy=scale, interpolation=cv2.INTER_LANCZOS4)
    else:
        scale = 1.0  # fenêtre de référence ou plus grande : lecture directe (mesurée fiable)
    mask = white_text_mask(patch)
    return [
        (_scale_box(b, 1 / scale).offset(region.x, region.y), crop(mask, b))
        for b in segment_characters(mask)
    ]


def read_resource_counters(
    bgr: np.ndarray,
    regions: dict[ElementType, RelativeRegion],
    templates: DigitTemplates | None = None,
) -> list[ResourceReading]:
    """Localise (et lit, si `templates` est fourni) chaque compteur de `regions`."""
    height, width = bgr.shape[:2]
    readings: list[ResourceReading] = []
    for resource, relative in regions.items():
        region = relative.to_box(width, height)
        chars = extract_characters(bgr, region)
        value, confidence = None, 0.0
        if templates is not None:
            value, confidence = templates.read_number([m for _, m in chars])
        logger.debug("%s : %d caractère(s), valeur=%s (%.2f)", resource.value, len(chars), value, confidence)
        readings.append(ResourceReading(resource, region, [b for b, _ in chars], value, confidence))
    return readings
