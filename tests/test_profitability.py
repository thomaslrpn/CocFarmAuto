"""Tests de la fiche village et du score de rentabilité."""
import json
from datetime import datetime

import numpy as np
import pytest
from pydantic import ValidationError

from app.analysis.profitability import Recommendation, compute_profitability
from app.analysis.scoring import PREFERENCES_FILE, Priority, ScoringPreferences, load_preferences
from app.analysis.village_analysis import Loot, build_sheet, sheet_from_frame
from app.analyze_cli import load_observations
from app.observer import ScoutRecorder
from app.vision.frame import FrameAnalysis
from app.vision.models import Box, ElementType
from app.vision.resources import ResourceReading
from app.vision.screen_state import GameScreen, ScreenDetection

TARGET = Loot(gold=600_000, elixir=600_000, dark_elixir=10_000)


def sheet(gold=0, elixir=0, dark=0, confidence=0.9):
    return build_sheet(Loot(gold=gold, elixir=elixir, dark_elixir=dark), confidence, datetime(2026, 11, 5))


# --- Fiche village -----------------------------------------------------------


def test_sheet_gold_share_and_unknown_fields():
    s = sheet(gold=300_000, elixir=100_000)
    assert s.gold_share == pytest.approx(0.75)
    assert s.difficulty is None and s.town_hall_level is None  # jamais inventés


def test_sheet_from_frame_only_on_scout():
    readings = [ResourceReading(r, Box(0, 0, 1, 1), [], v, c) for r, v, c in
                zip((ElementType.GOLD, ElementType.ELIXIR, ElementType.DARK_ELIXIR), (1, 2, 3), (0.9, 0.7, 0.8))]
    scout = FrameAnalysis(ScreenDetection(GameScreen.SCOUT, 1.0), [], readings)
    s = sheet_from_frame(scout)
    assert s.loot == Loot(gold=1, elixir=2, dark_elixir=3) and s.detection_confidence == 0.7
    assert sheet_from_frame(FrameAnalysis(ScreenDetection(GameScreen.HOME, 1.0), [], [])) is None


# --- Score -------------------------------------------------------------------


def test_score_reaching_every_target_is_100():
    result = compute_profitability(sheet(600_000, 600_000, 10_000))
    assert result.score == 100 and result.recommendation is Recommendation.VERY_GOOD


def test_empty_village_is_skipped():
    result = compute_profitability(sheet())
    assert result.score == 0 and result.recommendation is Recommendation.SKIP


def test_loot_above_target_is_capped():
    assert compute_profitability(sheet(10_000_000, 0, 0)).score == 40  # poids de l'or (équilibré)


def test_score_formula_matches_documented_example():
    # Or 300 000 / 600 000 = 50 % x 40 pts = 20 ; élixir 50 % x 40 = 20 ; noir 50 % x 20 = 10
    assert compute_profitability(sheet(300_000, 300_000, 5_000)).score == 50


def test_priority_changes_ranking():
    gold_rich, elixir_rich = sheet(600_000, 100_000), sheet(100_000, 600_000)
    gold_prefs = ScoringPreferences(priority=Priority.GOLD)
    assert compute_profitability(gold_rich, gold_prefs).score > compute_profitability(elixir_rich, gold_prefs).score


def test_army_cost_gives_net_profitability():
    prefs = ScoringPreferences(army_cost=Loot(elixir=300_000))
    gross = compute_profitability(sheet(0, 600_000, 0)).score
    net = compute_profitability(sheet(0, 600_000, 0), prefs).score
    assert (gross, net) == (40, 20)
    assert not any("non configuré" in w for w in compute_profitability(sheet(), prefs).warnings)


def test_dark_elixir_importance():
    village = sheet(0, 0, 10_000)
    assert compute_profitability(village, ScoringPreferences(dark_elixir_importance=0)).score == 0
    assert compute_profitability(village, ScoringPreferences(dark_elixir_importance=2)).score > 20


def test_minimum_loot_forces_skip():
    prefs = ScoringPreferences(min_gold_elixir=2_000_000)
    result = compute_profitability(sheet(600_000, 600_000, 10_000), prefs)
    assert result.score == 100 and result.recommendation is Recommendation.SKIP


def test_explanation_lists_every_criterion():
    text = "\n".join(compute_profitability(sheet(300_000, 300_000, 5_000, confidence=0.3)).explain())
    for word in ("Or", "Élixir", "Élixir noir", "Difficulté", "Temps", "Trophées", "non disponible",
                 "incertaine", "non configuré"):
        assert word in text


def test_invalid_preferences_rejected():
    with pytest.raises(ValidationError):
        ScoringPreferences(very_good_threshold=30, good_threshold=60)
    with pytest.raises(ValidationError):
        ScoringPreferences(target_loot=Loot(gold=0, elixir=1, dark_elixir=1))


def test_load_preferences_file_and_fallback(tmp_path):
    assert load_preferences(tmp_path) == ScoringPreferences()  # pas de fichier
    (tmp_path / PREFERENCES_FILE).write_text(json.dumps({"priority": "gold"}), encoding="utf-8")
    assert load_preferences(tmp_path).priority is Priority.GOLD
    (tmp_path / PREFERENCES_FILE).write_text("{ invalide", encoding="utf-8")
    assert load_preferences(tmp_path) == ScoringPreferences()  # fichier corrompu : défauts


# --- Intégration avec le mode observation ------------------------------------


def test_observations_are_loaded_and_scored(tmp_path):
    readings = [ResourceReading(r, Box(0, 0, 1, 1), [], v, 0.9) for r, v in
                zip((ElementType.GOLD, ElementType.ELIXIR, ElementType.DARK_ELIXIR), (600_000, 600_000, 10_000))]
    analysis = FrameAnalysis(ScreenDetection(GameScreen.SCOUT, 1.0), [], readings)
    ScoutRecorder(tmp_path, stable_frames=1).process(np.zeros((4, 4, 3), np.uint8), analysis)
    sheets = load_observations(tmp_path)
    assert len(sheets) == 1 and compute_profitability(sheets[0]).score == 100
