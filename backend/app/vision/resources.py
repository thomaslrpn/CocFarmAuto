"""Localisation des compteurs de ressources (or, élixir, élixir noir).

Étape 2.1 : on LOCALISE les chiffres de chaque compteur (position, nombre de
caractères). La LECTURE des chiffres (template matching) arrive à l'étape 2.2 :
d'ici là, `ResourceReading.value` reste à None — rien n'est simulé.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

from app.vision.models import Box, ElementType
from app.vision.preprocess import crop, segment_characters, white_text_mask
from app.vision.regions import RelativeRegion

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResourceReading:
    """Résultat pour un compteur : zone analysée et chiffres trouvés (coordonnées image)."""

    resource: ElementType
    region: Box
    characters: list[Box]
    value: int | None = None  # rempli à l'étape 2.2

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


def locate_resource_counters(
    bgr: np.ndarray, regions: dict[ElementType, RelativeRegion]
) -> list[ResourceReading]:
    """Localise les chiffres de chaque compteur de ressource défini dans `regions`."""
    height, width = bgr.shape[:2]
    readings: list[ResourceReading] = []
    for resource, relative in regions.items():
        region = relative.to_box(width, height)
        mask = white_text_mask(crop(bgr, region))
        chars = [b.offset(region.x, region.y) for b in segment_characters(mask)]
        logger.debug("%s : %d caractère(s) dans %s", resource.value, len(chars), region)
        readings.append(ResourceReading(resource, region, chars))
    return readings
