"""Modèles de données du module vision.

`Box` sert aux calculs internes (léger) ; `Detection` est le résultat « public »
d'une reconnaissance, validé par Pydantic et prêt à être stocké / envoyé à l'API.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field


@dataclass(frozen=True)
class Box:
    """Rectangle en pixels (origine en haut à gauche)."""

    x: int
    y: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height

    def offset(self, dx: int, dy: int) -> "Box":
        """Même rectangle décalé (pour repasser d'un recadrage à l'image entière)."""
        return Box(self.x + dx, self.y + dy, self.width, self.height)


class ElementType(str, Enum):
    """Types d'éléments reconnaissables (cahier des charges §6)."""

    GOLD = "gold"
    ELIXIR = "elixir"
    DARK_ELIXIR = "dark_elixir"
    GOLD_STORAGE = "gold_storage"
    ELIXIR_STORAGE = "elixir_storage"
    DARK_ELIXIR_STORAGE = "dark_elixir_storage"
    GOLD_MINE = "gold_mine"
    ELIXIR_COLLECTOR = "elixir_collector"
    DARK_ELIXIR_DRILL = "dark_elixir_drill"
    TOWN_HALL = "town_hall"
    DEFENSE = "defense"


class Detection(BaseModel):
    """Un élément reconnu dans une capture."""

    type: ElementType
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    confidence: float = Field(ge=0.0, le=1.0)
    value: int | None = Field(default=None, ge=0, description="Quantité lue, si applicable")
    level: int | None = Field(default=None, ge=1, description="Niveau apparent, si applicable")
    manually_corrected: bool = False  # pour la correction manuelle prévue au §6

    @classmethod
    def from_box(cls, type_: ElementType, box: Box, confidence: float, **extra: object) -> "Detection":
        return cls(type=type_, x=box.x, y=box.y, width=box.width, height=box.height, confidence=confidence, **extra)
