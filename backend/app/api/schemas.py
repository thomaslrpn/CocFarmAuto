"""Formats des réponses de l'API (contrat avec le frontend).

Les types TypeScript du dashboard (phase 6) seront calqués sur ces modèles ;
la page /docs les affiche automatiquement.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.analysis.profitability import ScoreFactor
from app.analysis.scoring import ScoringPreferences
from app.strategy.simulator import SimulationResult
from app.strategy.strategies import SimulationAssumptions


class Health(BaseModel):
    status: str


class Status(BaseModel):
    app: str
    version: str
    data_dir: str
    database: str
    villages_count: int
    vision_ready: bool
    game_window: str  # "found" | "not_found" | "unsupported"


class VillageSummary(BaseModel):
    id: int
    analyzed_at: datetime
    gold: int
    elixir: int
    dark_elixir: int
    profitability_score: int
    recommendation: str
    recommended_strategy: str | None
    recommended_strategy_label: str
    detection_confidence: float
    loot_value: float  # valeur non plafonnée selon les préférences actuelles
    relative_rank: float | None  # % des autres villages battus ; None si un seul village
    has_image: bool


class VillagePage(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[VillageSummary]


class VillageDetail(VillageSummary):
    town_hall_level: int | None
    estimated_difficulty: float | None
    explanation: list[str]
    factors: list[ScoreFactor]
    warnings: list[str]
    preferences_used: ScoringPreferences | None
    image_url: str | None


class DayStatistics(BaseModel):
    day: date
    villages_count: int
    total_gold: int
    total_elixir: int
    total_dark_elixir: int
    average_score: float


class StatisticsOverview(BaseModel):
    villages_count: int
    total_gold: int
    total_elixir: int
    total_dark_elixir: int
    average_score: float | None
    days: list[DayStatistics]


class StrategyComparison(BaseModel):
    villages_count: int
    search_time_s: float
    assumptions: list[str]
    army_cost_configured: bool
    results: list[SimulationResult]  # du meilleur au moins bon (points/h)


class UserSettingsModel(BaseModel):
    preferences: ScoringPreferences
    simulation: SimulationAssumptions


class UserSettingsUpdate(BaseModel):
    """Modification PARTIELLE : seuls les champs envoyés changent, même dans les
    sous-objets (ex. {"preferences": {"army_cost": {"elixir": 250000}}} ne touche
    ni la priorité ni l'or/noir du coût d'armée). Le résultat est ensuite validé."""

    model_config = ConfigDict(json_schema_extra={"examples": [
        {"preferences": {"priority": "gold"}},
        {"preferences": {"target_loot": {"gold": 1000000, "elixir": 1000000, "dark_elixir": 15000},
                         "army_cost": {"elixir": 250000}},
         "simulation": {"attack_duration_s": 120}},
    ]})

    preferences: dict[str, Any] | None = Field(
        default=None, description="Champs de ScoringPreferences à modifier (voir GET /api/settings)")
    simulation: dict[str, Any] | None = Field(
        default=None, description="Champs de SimulationAssumptions à modifier")
