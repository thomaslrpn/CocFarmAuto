"""Réglages de l'utilisateur : préférences de score + hypothèses de simulation.

Ordre de lecture (le premier trouvé et valide l'emporte) :
1. la base (table `settings`) : écrite par l'API / la page Paramètres ;
2. les fichiers `preferences.json` / `simulation.json` (réglages manuels d'avant l'API) ;
3. les valeurs par défaut.
Une valeur invalide est journalisée puis ignorée : le logiciel démarre toujours.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session

from app.analysis.scoring import PREFERENCES_FILE, ScoringPreferences
from app.config import Settings, load_user_json
from app.database.database import Database
from app.database.repository import get_setting, set_setting
from app.strategy.strategies import ASSUMPTIONS_FILE, SimulationAssumptions

logger = logging.getLogger(__name__)

PREFERENCES_KEY = "scoring_preferences"
SIMULATION_KEY = "simulation_assumptions"
APP_KEY = "app_preferences"
ModelT = TypeVar("ModelT", bound=BaseModel)


class AppPreferences(BaseModel):
    """Préférences de fonctionnement de l'application."""

    observe_interval_s: float = Field(default=1.0, ge=0.2, le=60,
                                      description="secondes entre deux analyses en mode observation")


@dataclass(frozen=True)
class UserSettings:
    preferences: ScoringPreferences
    simulation: SimulationAssumptions
    app: AppPreferences = field(default_factory=AppPreferences)


def _load(session: Session, key: str, model: type[ModelT], data_dir: Path, filename: str) -> ModelT:
    raw = get_setting(session, key)
    if raw is not None:
        try:
            return model.model_validate(raw)
        except ValidationError as exc:
            logger.error("Réglage '%s' invalide en base, ignoré : %s", key, exc)
    return load_user_json(data_dir, filename, model)


def load_user_settings(session: Session, data_dir: Path) -> UserSettings:
    return UserSettings(
        preferences=_load(session, PREFERENCES_KEY, ScoringPreferences, data_dir, PREFERENCES_FILE),
        simulation=_load(session, SIMULATION_KEY, SimulationAssumptions, data_dir, ASSUMPTIONS_FILE),
        app=_load(session, APP_KEY, AppPreferences, data_dir, "app.json"),
    )


def save_user_settings(session: Session, settings: UserSettings) -> None:
    set_setting(session, PREFERENCES_KEY, settings.preferences.model_dump(mode="json"))
    set_setting(session, SIMULATION_KEY, settings.simulation.model_dump(mode="json"))
    set_setting(session, APP_KEY, settings.app.model_dump(mode="json"))


def load_from_app_settings(app_settings: Settings) -> UserSettings:
    """Raccourci pour les commandes : ouvre la base, lit les réglages, ferme."""
    db = Database.open(app_settings.database_path, app_settings.backups_dir)
    try:
        with db.session() as session:
            return load_user_settings(session, app_settings.data_dir)
    finally:
        db.close()
