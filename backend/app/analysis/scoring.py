"""Paramètres personnalisables du score de rentabilité (cahier des charges §8).

Les préférences sont lues depuis `%LOCALAPPDATA%\\CoCAutoFarm\\preferences.json`
si le fichier existe (sinon valeurs par défaut). La page Paramètres du dashboard
(phase 6) écrira ce même fichier / la base.
"""
from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, model_validator

from app.analysis.village_analysis import Loot, Resource
from app.config import load_user_json

PREFERENCES_FILE = "preferences.json"


class Priority(str, Enum):
    BALANCED = "balanced"
    GOLD = "gold"
    ELIXIR = "elixir"
    DARK_ELIXIR = "dark_elixir"


# Importance relative de chaque ressource selon la priorité choisie (somme = 1).
PRIORITY_WEIGHTS: dict[Priority, dict[Resource, float]] = {
    Priority.BALANCED: {Resource.GOLD: 0.4, Resource.ELIXIR: 0.4, Resource.DARK_ELIXIR: 0.2},
    Priority.GOLD: {Resource.GOLD: 0.6, Resource.ELIXIR: 0.25, Resource.DARK_ELIXIR: 0.15},
    Priority.ELIXIR: {Resource.GOLD: 0.25, Resource.ELIXIR: 0.6, Resource.DARK_ELIXIR: 0.15},
    Priority.DARK_ELIXIR: {Resource.GOLD: 0.2, Resource.ELIXIR: 0.2, Resource.DARK_ELIXIR: 0.6},
}


class ScoringPreferences(BaseModel):
    """Réglages du score. Toutes les valeurs par défaut sont modifiables."""

    priority: Priority = Priority.BALANCED
    # Butin qui donne le maximum de points pour une ressource. Valeurs par défaut
    # choisies d'après les villages réellement rencontrés (HDV élevé) : à adapter.
    target_loot: Loot = Loot(gold=600_000, elixir=600_000, dark_elixir=10_000)
    # Coût de l'armée, déduit du butin (rentabilité NETTE). 0 = non configuré.
    army_cost: Loot = Loot()
    # Multiplie l'importance de l'élixir noir (1.0 = celle de la priorité choisie).
    dark_elixir_importance: float = Field(default=1.0, ge=0.0, le=5.0)
    # En dessous de ce butin (or + élixir), le village est à passer quel que soit le score.
    min_gold_elixir: int = Field(default=0, ge=0)
    # Seuils de recommandation (score sur 100).
    very_good_threshold: int = Field(default=80, ge=0, le=100)
    good_threshold: int = Field(default=60, ge=0, le=100)
    average_threshold: int = Field(default=40, ge=0, le=100)

    @model_validator(mode="after")
    def _check(self) -> "ScoringPreferences":
        if not self.very_good_threshold >= self.good_threshold >= self.average_threshold:
            raise ValueError("seuils attendus : très intéressant >= intéressant >= moyen")
        if any(self.target_loot.get(r) <= 0 for r in Resource):
            raise ValueError("le butin visé doit être > 0 pour chaque ressource")
        return self

    def weights(self) -> dict[Resource, float]:
        """Poids normalisés (somme = 1) après application de l'importance de l'élixir noir."""
        raw = dict(PRIORITY_WEIGHTS[self.priority])
        raw[Resource.DARK_ELIXIR] *= self.dark_elixir_importance
        total = sum(raw.values())
        return {r: w / total for r, w in raw.items()} if total else raw

    def loot_value(self, gold: float, elixir: float, dark_elixir: float) -> float:
        """Valeur d'un butin sur l'échelle du score, SANS plafond (peut dépasser 100).

        Sert à départager des villages qui ont tous 100/100, et à comparer des
        butins nets (qui peuvent être négatifs) dans la simulation.
        """
        weights = self.weights()
        amounts = {Resource.GOLD: gold, Resource.ELIXIR: elixir, Resource.DARK_ELIXIR: dark_elixir}
        return sum(100 * weights[r] * amounts[r] / self.target_loot.get(r) for r in Resource)


def load_preferences(data_dir: Path) -> ScoringPreferences:
    """Charge les préférences de l'utilisateur ; valeurs par défaut si absent ou invalide."""
    return load_user_json(data_dir, PREFERENCES_FILE, ScoringPreferences)
