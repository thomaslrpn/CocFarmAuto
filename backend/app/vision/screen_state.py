"""Reconnaissance de l'écran affiché : village, recherche d'adversaire, combat.

Principe : chaque écran possède des boutons FIXES qui lui sont propres
(« Suivant » en recherche, « Capituler » en combat, « Combat » + « Construire »
au village). On découpe leur emplacement dans la capture et on compare avec
des modèles (corrélation normalisée). L'écran le plus ressemblant l'emporte,
s'il dépasse un seuil ; sinon l'écran est « inconnu » (menu, chargement...).
"""
from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import cv2
import numpy as np

from app.vision.image_io import TemplatesNotFoundError, load_array, save_array
from app.vision.preprocess import crop, similarity
from app.vision.regions import RelativeRegion

logger = logging.getLogger(__name__)

DEFAULT_TEMPLATES_DIR = Path(__file__).parent / "templates" / "screens"
# Mesures sur captures réelles : bon écran 0.93-1.00, mauvais écran 0.40 au plus.
MIN_SCREEN_CONFIDENCE = 0.75
REF_W, REF_H = 1323, 744  # taille des captures où les boutons ont été mesurés


class GameScreen(str, Enum):
    HOME = "home"  # village du joueur
    SCOUT = "scout"  # recherche d'adversaire (butin visible, combat pas commencé)
    BATTLE = "battle"  # combat en cours
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Signature:
    """Un élément visuel fixe qui identifie un écran."""

    name: str
    screen: GameScreen
    region: RelativeRegion


SIGNATURES: tuple[Signature, ...] = (
    Signature("next_button", GameScreen.SCOUT, RelativeRegion.from_pixels(1140, 528, 1312, 602, REF_W, REF_H)),
    Signature("surrender_button", GameScreen.BATTLE, RelativeRegion.from_pixels(15, 565, 143, 608, REF_W, REF_H)),
    Signature("attack_button", GameScreen.HOME, RelativeRegion.from_pixels(15, 618, 130, 730, REF_W, REF_H)),
    Signature("build_button", GameScreen.HOME, RelativeRegion.from_pixels(1193, 620, 1311, 730, REF_W, REF_H)),
)


@dataclass(frozen=True)
class ScreenDetection:
    screen: GameScreen
    confidence: float
    scores: dict[GameScreen, float] = field(default_factory=dict)  # score de chaque écran (diagnostic)


def _signature_patch(bgr: np.ndarray, signature: Signature, size: tuple[int, int] | None = None) -> np.ndarray:
    """Découpe la zone d'une signature (float 0-1), redimensionnée à `size` (largeur, hauteur) si fourni."""
    patch = crop(bgr, signature.region.to_box(bgr.shape[1], bgr.shape[0])).astype(np.float32) / 255.0
    if size is not None and (patch.shape[1], patch.shape[0]) != size:
        patch = cv2.resize(patch, size, interpolation=cv2.INTER_AREA)
    return patch


@dataclass(frozen=True)
class ScreenTemplates:
    """Un modèle (image BGR float 0-1) par signature."""

    templates: dict[str, np.ndarray]

    def detect(self, bgr: np.ndarray) -> ScreenDetection:
        per_screen: dict[GameScreen, list[float]] = {}
        for sig in SIGNATURES:
            tpl = self.templates[sig.name]
            patch = _signature_patch(bgr, sig, (tpl.shape[1], tpl.shape[0]))
            per_screen.setdefault(sig.screen, []).append(similarity(patch, tpl))
        # Score d'un écran = moyenne de ses signatures (toutes doivent être présentes).
        scores = {screen: float(np.mean(values)) for screen, values in per_screen.items()}
        best = max(scores, key=scores.__getitem__)
        if scores[best] < MIN_SCREEN_CONFIDENCE:
            return ScreenDetection(GameScreen.UNKNOWN, scores[best], scores)
        return ScreenDetection(best, scores[best], scores)

    # --- Construction / persistance -------------------------------------

    @classmethod
    def build(cls, captures: Iterable[tuple[np.ndarray, GameScreen]]) -> "ScreenTemplates":
        """Modèle de chaque signature = moyenne de sa zone sur les captures de son écran."""
        captures = list(captures)
        templates: dict[str, np.ndarray] = {}
        for sig in SIGNATURES:
            sources = [bgr for bgr, screen in captures if screen is sig.screen]
            if not sources:
                raise ValueError(f"Aucune capture annotée '{sig.screen.value}' pour '{sig.name}'")
            first = _signature_patch(sources[0], sig)
            size = (first.shape[1], first.shape[0])
            templates[sig.name] = np.mean([_signature_patch(b, sig, size) for b in sources], axis=0)
        return cls(templates)

    def save(self, directory: Path = DEFAULT_TEMPLATES_DIR) -> None:
        for name, tpl in self.templates.items():
            save_array(tpl, directory / f"{name}.png")

    @classmethod
    def load(cls, directory: Path = DEFAULT_TEMPLATES_DIR) -> "ScreenTemplates":
        templates: dict[str, np.ndarray] = {}
        for sig in SIGNATURES:
            path = directory / f"{sig.name}.png"
            if not path.is_file():
                raise TemplatesNotFoundError(f"Modèle manquant : {path} (lancer app.build_templates)")
            templates[sig.name] = load_array(path)
        return cls(templates)
