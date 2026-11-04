"""Configuration centrale de CoC AutoFarm.

Principe clé : les DONNÉES UTILISATEUR (captures, base SQLite, logs) vivent
dans un dossier séparé des fichiers de l'application, pour que les mises à
jour ne les écrasent jamais (cahier des charges §13.6).
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

APP_NAME = "CoC AutoFarm"
APP_VERSION = "0.1.0"
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
    game_window_title: str = GAME_WINDOW_TITLE

    @classmethod
    def load(cls) -> "Settings":
        data_dir = user_data_dir()
        return cls(data_dir=data_dir, screenshots_dir=data_dir / "screenshots")
