"""Configuration centrale de CoC AutoFarm.

Principe clé : les DONNÉES UTILISATEUR (captures, base SQLite, logs) vivent
dans un dossier séparé des fichiers de l'application, pour que les mises à
jour ne les écrasent jamais (cahier des charges §13.6).
"""
from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)
ModelT = TypeVar("ModelT", bound=BaseModel)

APP_NAME = "CoC AutoFarm"
APP_VERSION = "0.2.1-beta.2"
# Fragment du titre de la fenêtre Google Play Games pour Clash of Clans.
GAME_WINDOW_TITLE = "Clash of Clans"


def user_data_dir() -> Path:
    """Dossier de données utilisateur, propre à chaque installation.

    Windows : %LOCALAPPDATA%/CoCAutoFarm. Variable COC_AUTOFARM_DATA_DIR
    permet de surcharger (dev, tests).
    """
    override = os.environ.get("COC_AUTOFARM_DATA_DIR")
    if override:
        return Path(override)
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:  # dev sur macOS/Linux uniquement
        base = Path.home() / ".local" / "share"
    return base / "CoCAutoFarm"


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    screenshots_dir: Path
    observations_dir: Path  # écrans de recherche enregistrés par le mode observation
    database_path: Path  # base SQLite de l'utilisateur
    backups_dir: Path  # sauvegardes automatiques de la base (avant migration)
    logs_dir: Path  # journaux (JSON, rotation)
    game_window_title: str = GAME_WINDOW_TITLE
    observe_interval_s: float = 1.0  # délai entre deux analyses en mode observation

    @classmethod
    def load(cls) -> "Settings":
        data_dir = user_data_dir()
        return cls(
            data_dir=data_dir,
            screenshots_dir=data_dir / "screenshots",
            observations_dir=data_dir / "observations",
            database_path=data_dir / "autofarm.db",
            backups_dir=data_dir / "backups",
            logs_dir=data_dir / "logs",
        )


def load_user_json(data_dir: Path, filename: str, model: type[ModelT]) -> ModelT:
    """Charge un réglage utilisateur (JSON validé par Pydantic) depuis le dossier de données.

    Fichier absent ou invalide -> valeurs par défaut du modèle (l'erreur est journalisée :
    un fichier corrompu ne doit jamais empêcher le logiciel de démarrer).
    """
    path = data_dir / filename
    if not path.is_file():
        return model()
    try:
        return model.model_validate_json(path.read_text(encoding="utf-8"))
    except (ValidationError, ValueError, OSError) as exc:
        logger.error("Réglages invalides dans %s, valeurs par défaut utilisées : %s", path, exc)
        return model()
