"""Modèles partagés par le mode observation, les alertes et les récapitulatifs d'attaque."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ObservedVillage(BaseModel):
    village_id: int
    analyzed_at: datetime
    gold: int
    elixir: int
    dark_elixir: int
    score: int
    recommendation: str
    strategy: str
