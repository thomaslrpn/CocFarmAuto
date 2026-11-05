"""Lecture de chiffres par comparaison avec des modèles (template matching).

Principe :
1. Chaque caractère détecté (masque binaire) est « normalisé » : mis à une
   hauteur fixe en gardant ses proportions, puis centré dans un carré.
   Un « 1 » reste fin, un « 0 » reste large : la forme est conservée.
2. On le compare aux 10 modèles (0 à 9) par corrélation normalisée
   (cv2.TM_CCOEFF_NORMED) : 1.0 = identique, 0 = sans rapport.
3. Le meilleur score donne le chiffre ; le score sert de niveau de confiance.

Les modèles sont construits à partir de captures réelles annotées
(voir `app.build_templates`) et livrés avec l'application.
"""
from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from app.vision.image_io import TemplatesNotFoundError, load_array, save_array
from app.vision.preprocess import similarity

logger = logging.getLogger(__name__)

GLYPH_SIZE = 20  # côté du carré de normalisation, en pixels
# En dessous, une lecture est jugée incertaine (sur captures réelles : 0.73 à 0.92).
MIN_RELIABLE_CONFIDENCE = 0.6
DEFAULT_TEMPLATES_DIR = Path(__file__).parent / "templates" / "digits"


def normalize_glyph(mask: np.ndarray, size: int = GLYPH_SIZE) -> np.ndarray:
    """Met un masque de caractère à hauteur `size` (proportions gardées), centré.

    Retourne un tableau float32 (size x size) de valeurs 0.0 à 1.0.
    """
    h, w = mask.shape[:2]
    if h == 0 or w == 0:
        return np.zeros((size, size), np.float32)
    new_w = max(1, min(size, round(w * size / h)))
    resized = cv2.resize(mask.astype(np.float32), (new_w, size), interpolation=cv2.INTER_AREA)
    canvas = np.zeros((size, size), np.float32)
    x0 = (size - new_w) // 2
    canvas[:, x0 : x0 + new_w] = resized
    return canvas


@dataclass(frozen=True)
class DigitTemplates:
    """Les 10 modèles de chiffres, indexés de 0 à 9."""

    templates: dict[int, np.ndarray]

    def classify(self, mask: np.ndarray) -> tuple[int, float]:
        """Retourne (chiffre le plus ressemblant, score de confiance)."""
        glyph = normalize_glyph(mask)
        scores = {digit: similarity(glyph, tpl) for digit, tpl in self.templates.items()}
        best = max(scores, key=scores.__getitem__)
        return best, scores[best]

    def read_number(self, masks: Sequence[np.ndarray]) -> tuple[int | None, float]:
        """Lit une suite de caractères. Retourne (valeur, confiance minimale)."""
        if not masks:
            return None, 0.0
        results = [self.classify(m) for m in masks]
        value = int("".join(str(d) for d, _ in results))
        return value, min(score for _, score in results)

    # --- Construction / persistance -------------------------------------

    @classmethod
    def build(cls, samples: Iterable[tuple[np.ndarray, int]]) -> "DigitTemplates":
        """Crée les modèles en faisant la MOYENNE des exemples de chaque chiffre."""
        groups: dict[int, list[np.ndarray]] = {}
        for mask, digit in samples:
            groups.setdefault(digit, []).append(normalize_glyph(mask))
        missing = sorted(set(range(10)) - groups.keys())
        if missing:
            raise ValueError(f"Aucun exemple pour le(s) chiffre(s) : {missing}")
        return cls({d: np.mean(g, axis=0).astype(np.float32) for d, g in sorted(groups.items())})

    def save(self, directory: Path = DEFAULT_TEMPLATES_DIR) -> None:
        for digit, tpl in self.templates.items():
            save_array(tpl, directory / f"{digit}.png")

    @classmethod
    def load(cls, directory: Path = DEFAULT_TEMPLATES_DIR) -> "DigitTemplates":
        templates: dict[int, np.ndarray] = {}
        for digit in range(10):
            path = directory / f"{digit}.png"
            if not path.is_file():
                raise TemplatesNotFoundError(f"Modèle manquant : {path} (lancer app.build_templates)")
            templates[digit] = load_array(path, grayscale=True)
        return cls(templates)
