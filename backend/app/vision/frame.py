"""Analyse complète d'une capture : quel écran, puis quelles ressources.

C'est le point d'entrée du module vision pour le reste de l'application
(API, analyse de village) : une image en entrée, un `FrameAnalysis` en sortie.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from app.vision.digits import DEFAULT_TEMPLATES_DIR as DIGITS_DIR
from app.vision.digits import DigitTemplates
from app.vision.regions import HOME_RESOURCE_REGIONS, LOOT_RESOURCE_REGIONS
from app.vision.resources import ResourceReading, read_resource_counters
from app.vision.screen_state import DEFAULT_TEMPLATES_DIR as SCREENS_DIR
from app.vision.screen_state import GameScreen, ScreenDetection, ScreenTemplates

logger = logging.getLogger(__name__)

# Écrans où le « Butin disponible » de l'adversaire est affiché.
LOOT_SCREENS = frozenset({GameScreen.SCOUT, GameScreen.BATTLE})
# Écrans où les ressources du joueur sont affichées (en haut à droite).
HOME_COUNTER_SCREENS = frozenset({GameScreen.HOME, GameScreen.SCOUT, GameScreen.BATTLE})


@dataclass(frozen=True)
class VisionModels:
    """Tous les modèles nécessaires à la vision, chargés une seule fois."""

    digits: DigitTemplates
    screens: ScreenTemplates

    @classmethod
    def load(cls, digits_dir: Path = DIGITS_DIR, screens_dir: Path = SCREENS_DIR) -> "VisionModels":
        return cls(DigitTemplates.load(digits_dir), ScreenTemplates.load(screens_dir))


@dataclass(frozen=True)
class FrameAnalysis:
    screen: ScreenDetection
    player_resources: list[ResourceReading]  # vide si l'écran ne les affiche pas
    loot: list[ResourceReading]  # vide hors recherche / combat


def analyze_frame(bgr: np.ndarray, models: VisionModels) -> FrameAnalysis:
    """Identifie l'écran, puis lit uniquement les compteurs qu'il affiche."""
    screen = models.screens.detect(bgr)
    player = (
        read_resource_counters(bgr, HOME_RESOURCE_REGIONS, models.digits)
        if screen.screen in HOME_COUNTER_SCREENS else []
    )
    loot = (
        read_resource_counters(bgr, LOOT_RESOURCE_REGIONS, models.digits)
        if screen.screen in LOOT_SCREENS else []
    )
    logger.info("Écran %s (%.2f), %d compteur(s) joueur, %d compteur(s) butin",
                screen.screen.value, screen.confidence, len(player), len(loot))
    return FrameAnalysis(screen, player, loot)
