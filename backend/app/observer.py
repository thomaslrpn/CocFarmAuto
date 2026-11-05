"""Mode observation : enregistre automatiquement chaque village rencontré.

LECTURE SEULE : le logiciel regarde l'écran, il n'envoie aucun clic ni aucune
touche au jeu. C'est l'utilisateur qui lance ses recherches.

Pour chaque nouvel écran de recherche, on enregistre :
- la capture (PNG) : futur jeu de données pour la détection des bâtiments ;
- un fichier JSON avec ce qui a été lu (butin, ressources, confiances).

Phase 5 : ces enregistrements iront aussi dans la base SQLite.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
from pydantic import BaseModel, ValidationError

from app.analysis.village_analysis import Loot, VillageSheet, build_sheet
from app.config import APP_VERSION
from app.vision.frame import FrameAnalysis
from app.vision.image_io import save_array
from app.vision.resources import ResourceReading
from app.vision.screen_state import GameScreen

logger = logging.getLogger(__name__)

# Nombre d'analyses consécutives avec le même butin avant d'enregistrer :
# évite de capturer un village encore en cours de chargement.
STABLE_FRAMES_REQUIRED = 2

LootKey = tuple[int, int, int]


class CounterValue(BaseModel):
    value: int | None
    confidence: float


class ObservationRecord(BaseModel):
    """Contenu du fichier JSON associé à chaque capture enregistrée."""

    captured_at: datetime
    app_version: str
    image: str
    screen: GameScreen
    screen_confidence: float
    loot: dict[str, CounterValue]
    player_resources: dict[str, CounterValue]


def _counters(readings: list[ResourceReading]) -> dict[str, CounterValue]:
    return {r.resource.value: CounterValue(value=r.value, confidence=round(r.confidence, 3)) for r in readings}


def loot_key(analysis: FrameAnalysis) -> LootKey | None:
    """Identifiant d'un village = son butin (or, élixir, noir). None si illisible."""
    if analysis.screen.screen is not GameScreen.SCOUT or len(analysis.loot) != 3:
        return None
    values = tuple(r.value for r in analysis.loot)
    if any(v is None for v in values):
        return None
    return values  # type: ignore[return-value]


class ScoutRecorder:
    """Décide quand un écran de recherche doit être enregistré, et l'enregistre."""

    def __init__(
        self,
        output_dir: Path,
        stable_frames: int = STABLE_FRAMES_REQUIRED,
        now: Callable[[], datetime] = datetime.now,
    ) -> None:
        self.output_dir = output_dir
        self.stable_frames = stable_frames
        self._now = now
        self._candidate: LootKey | None = None
        self._seen_count = 0
        self._last_saved: LootKey | None = None

    def process(self, bgr: np.ndarray, analysis: FrameAnalysis) -> Path | None:
        """Traite une analyse. Retourne le chemin du JSON si un village a été enregistré."""
        key = loot_key(analysis)
        if key is None:  # pas un écran de recherche lisible : on repart de zéro
            self._candidate, self._seen_count = None, 0
            return None
        if key == self._last_saved:  # même village, déjà enregistré
            return None
        if key == self._candidate:
            self._seen_count += 1
        else:
            self._candidate, self._seen_count = key, 1
        if self._seen_count < self.stable_frames:
            return None
        self._last_saved = key
        return self._save(bgr, analysis)

    def _save(self, bgr: np.ndarray, analysis: FrameAnalysis) -> Path:
        captured_at = self._now()
        stem = f"scout_{captured_at:%Y%m%d_%H%M%S_%f}"
        image_path = self.output_dir / f"{stem}.png"
        json_path = self.output_dir / f"{stem}.json"
        save_array(bgr, image_path)  # crée aussi le dossier si besoin
        record = ObservationRecord(
            captured_at=captured_at,
            app_version=APP_VERSION,
            image=image_path.name,
            screen=analysis.screen.screen,
            screen_confidence=round(analysis.screen.confidence, 3),
            loot=_counters(analysis.loot),
            player_resources=_counters(analysis.player_resources),
        )
        json_path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
        logger.info("Village enregistré : %s", json_path.name)
        return json_path


@dataclass
class ObserverStats:
    frames: int = 0
    missing_window: int = 0
    errors: int = 0
    saved: int = 0


# --- Relecture des observations enregistrées --------------------------------


def sheet_from_record(record: ObservationRecord) -> VillageSheet | None:
    """Fiche village depuis un enregistrement du mode observation (None si butin incomplet)."""
    values = {name: c.value for name, c in record.loot.items()}
    if len(values) != 3 or any(v is None for v in values.values()):
        return None
    confidence = min(c.confidence for c in record.loot.values())
    return build_sheet(Loot(**values), confidence, record.captured_at, record.image)


def load_observations(directory: Path) -> list[VillageSheet]:
    sheets: list[VillageSheet] = []
    for path in sorted(directory.glob("scout_*.json")):
        try:
            record = ObservationRecord.model_validate_json(path.read_text(encoding="utf-8"))
        except (ValidationError, OSError) as exc:
            logger.warning("Observation ignorée %s : %s", path.name, exc)
            continue
        sheet = sheet_from_record(record)
        if sheet is not None:
            sheets.append(sheet)
    return sheets
