"""Fiche d'analyse d'un village (cahier des charges §7).

Construite à partir de ce que la vision a lu. Les informations que l'on ne sait
pas ENCORE mesurer (difficulté, hôtel de ville, position des réserves...)
valent None : elles ne sont jamais inventées.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.vision.frame import FrameAnalysis
from app.vision.screen_state import GameScreen


class Resource(str, Enum):
    GOLD = "gold"
    ELIXIR = "elixir"
    DARK_ELIXIR = "dark_elixir"


RESOURCE_LABELS = {Resource.GOLD: "Or", Resource.ELIXIR: "Élixir", Resource.DARK_ELIXIR: "Élixir noir"}


class Loot(BaseModel):
    """Quantités de ressources (butin disponible, coût d'armée...)."""

    gold: int = Field(default=0, ge=0)
    elixir: int = Field(default=0, ge=0)
    dark_elixir: int = Field(default=0, ge=0)

    def get(self, resource: Resource) -> int:
        return getattr(self, resource.value)


class VillageSheet(BaseModel):
    """Fiche complète d'un village analysé."""

    analyzed_at: datetime
    loot: Loot
    # Part de chaque ressource dans (or + élixir) ; l'élixir noir, d'une autre
    # échelle, n'y est pas mélangé.
    gold_share: float = Field(ge=0.0, le=1.0)
    detection_confidence: float = Field(ge=0.0, le=1.0, description="confiance du chiffre le moins sûr")
    source_image: str | None = None
    # --- Pas encore mesurable (détection des bâtiments à venir) ---
    town_hall_level: int | None = None
    difficulty: float | None = None  # 0 (facile) à 1 (difficile)
    loot_in_collectors_share: float | None = None  # part du butin dans les mines/extracteurs


def build_sheet(
    loot: Loot,
    detection_confidence: float,
    analyzed_at: datetime | None = None,
    source_image: str | None = None,
) -> VillageSheet:
    total = loot.gold + loot.elixir
    return VillageSheet(
        analyzed_at=analyzed_at or datetime.now(),
        loot=loot,
        gold_share=loot.gold / total if total else 0.0,
        detection_confidence=detection_confidence,
        source_image=source_image,
    )


def sheet_from_frame(analysis: FrameAnalysis, source_image: str | None = None) -> VillageSheet | None:
    """Fiche à partir d'une analyse d'écran. None si ce n'est pas un écran de recherche lisible."""
    if analysis.screen.screen is not GameScreen.SCOUT or len(analysis.loot) != 3:
        return None
    if any(r.value is None for r in analysis.loot):
        return None
    values = {r.resource.value: r.value for r in analysis.loot}
    confidence = min(r.confidence for r in analysis.loot)
    return build_sheet(Loot(**values), confidence, source_image=source_image)
