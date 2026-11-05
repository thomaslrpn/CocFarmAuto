"""Tests du mode observation (sans jeu : analyses fabriquées)."""
import json
from datetime import datetime

import numpy as np
import pytest

from app.observer import ObservationRecord, ScoutRecorder, loot_key
from app.vision.frame import FrameAnalysis
from app.vision.models import Box, ElementType
from app.vision.resources import ResourceReading
from app.vision.screen_state import GameScreen, ScreenDetection

FRAME = np.zeros((20, 30, 3), np.uint8)
RESOURCES = (ElementType.GOLD, ElementType.ELIXIR, ElementType.DARK_ELIXIR)


def _readings(values) -> list[ResourceReading]:
    return [ResourceReading(res, Box(0, 0, 1, 1), [], v, 0.9) for res, v in zip(RESOURCES, values)]


def make_analysis(screen=GameScreen.SCOUT, loot=(1000, 2000, 30)) -> FrameAnalysis:
    has_loot = screen in (GameScreen.SCOUT, GameScreen.BATTLE)
    return FrameAnalysis(
        screen=ScreenDetection(screen, 0.99),
        player_resources=_readings((5, 6, 7)),
        loot=_readings(loot) if has_loot else [],
    )


@pytest.fixture
def recorder(tmp_path) -> ScoutRecorder:
    return ScoutRecorder(tmp_path, stable_frames=2, now=lambda: datetime(2026, 11, 5, 10, 0, 0))


def test_loot_key_only_on_readable_scout_screen():
    assert loot_key(make_analysis()) == (1000, 2000, 30)
    assert loot_key(make_analysis(GameScreen.HOME)) is None
    assert loot_key(make_analysis(GameScreen.BATTLE)) is None  # combat : pas un nouveau village
    assert loot_key(make_analysis(loot=(1000, None, 30))) is None


def test_saves_only_after_stable_frames(recorder):
    assert recorder.process(FRAME, make_analysis()) is None  # 1re vue : on attend
    assert recorder.process(FRAME, make_analysis()) is not None  # 2e vue identique : enregistré


def test_same_village_saved_once(recorder):
    for _ in range(5):
        recorder.process(FRAME, make_analysis())
    assert len(list(recorder.output_dir.glob("*.json"))) == 1


def test_changing_reading_resets_stability(recorder):
    recorder.process(FRAME, make_analysis(loot=(1, 2, 3)))
    assert recorder.process(FRAME, make_analysis(loot=(9, 9, 9))) is None  # valeur différente
    assert recorder.process(FRAME, make_analysis(GameScreen.HOME)) is None
    assert recorder.process(FRAME, make_analysis(loot=(9, 9, 9))) is None  # remise à zéro par l'écran village


def test_next_village_is_saved(tmp_path):
    times = iter([datetime(2026, 11, 5, 10, 0, s) for s in range(10)])
    rec = ScoutRecorder(tmp_path, stable_frames=1, now=lambda: next(times))
    assert rec.process(FRAME, make_analysis(loot=(1, 2, 3))) is not None
    assert rec.process(FRAME, make_analysis(loot=(4, 5, 6))) is not None
    assert len(list(tmp_path.glob("*.png"))) == 2


def test_saved_files_content(recorder):
    recorder.process(FRAME, make_analysis())
    json_path = recorder.process(FRAME, make_analysis())
    record = ObservationRecord.model_validate(json.loads(json_path.read_text(encoding="utf-8")))
    assert record.screen is GameScreen.SCOUT
    assert record.loot["gold"].value == 1000 and record.loot["dark_elixir"].value == 30
    assert record.player_resources["elixir"].value == 6
    assert (json_path.parent / record.image).is_file()
