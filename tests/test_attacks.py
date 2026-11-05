"""Récapitulatif d'attaque : butin récupéré = butin de départ - butin restant à la fin du combat."""
import time
from collections import deque
from datetime import datetime, timedelta

import numpy as np

from app.analysis.scoring import Priority, ScoringPreferences
from app.attacks import AttackSummary, AttackTracker, rate_attack, remaining_estimate
from app.config import Settings
from app.database.database import Database
from app.database.repository import attack_for_village
from app.observation_models import ObservedVillage
from app.observer_service import ObserverService
from app.vision.frame import FrameAnalysis
from app.vision.models import Box, ElementType
from app.vision.resources import ResourceReading
from app.vision.screen_state import GameScreen, ScreenDetection

T0 = datetime(2026, 11, 5, 16, 0, 0)
RES = (ElementType.GOLD, ElementType.ELIXIR, ElementType.DARK_ELIXIR)
VILLAGE = ObservedVillage(village_id=3, analyzed_at=T0, gold=650_000, elixir=720_000, dark_elixir=5_000,
                          score=91, recommendation="très intéressant", strategy="Farm élixir")


def loot(gold, elixir, dark, confidence=0.9):
    return [ResourceReading(r, Box(0, 0, 1, 1), [], v, confidence) for r, v in zip(RES, (gold, elixir, dark))]


def run(tracker, frames, village=VILLAGE):
    """frames : (écran confirmé, lectures) ; une seconde entre deux images. Renvoie les résumés produits."""
    results = []
    for i, (screen, readings) in enumerate(frames):
        result = tracker.update(screen, readings, village, T0 + timedelta(seconds=10 + i))
        if result is not None:
            results.append(result)
    return results


def test_gain_is_start_minus_remaining_at_the_end():
    frames = [("scout", loot(650_000, 720_000, 5_000)),
              ("battle", loot(600_000, 700_000, 5_000)),
              ("battle", loot(300_000, 200_000, 2_000)),
              ("battle", loot(130_000, 144_000, 1_000)),
              ("battle", loot(130_000, 144_000, 1_000)),
              ("unknown", [])]
    [summary] = run(AttackTracker(), frames)
    assert summary.village_id == 3
    assert (summary.available_gold, summary.gained_gold) == (650_000, 520_000)
    assert (summary.available_elixir, summary.gained_elixir) == (720_000, 576_000)
    assert summary.gained_dark_elixir == 4_000
    assert (summary.ended_at - summary.started_at).total_seconds() == 4


def test_misreadings_are_ignored():
    frames = [("scout", []),
              ("battle", loot(400_000, 400_000, 0)),
              ("battle", loot(200_000, 9_999_999, 0)),        # élixir impossible (> départ) : ignoré
              ("battle", loot(20_000, 300_000, 0)),           # or : chiffre perdu, lecture isolée
              ("battle", loot(200_000, 300_000, 0, confidence=0.3)),  # lecture peu fiable : ignorée
              ("battle", loot(200_000, 300_000, 0)),
              ("home", [])]
    [summary] = run(AttackTracker(), frames)
    assert summary.gained_gold == 650_000 - 200_000  # 200 000 lu deux fois ; 20 000 isolé écarté
    assert summary.gained_elixir == 720_000 - 300_000


def test_battle_without_scout_uses_first_reading_as_start():
    frames = [("home", []),
              ("battle", loot(500_000, 500_000, 3_000)),
              ("battle", loot(100_000, 250_000, 3_000)),
              ("home", [])]
    [summary] = run(AttackTracker(), frames)
    assert summary.village_id is None  # pas rattaché à un village de la recherche
    assert (summary.available_gold, summary.gained_gold) == (500_000, 400_000)


def test_old_scout_is_not_linked_to_the_battle():
    old = VILLAGE.model_copy(update={"analyzed_at": T0 - timedelta(minutes=30)})
    frames = [("scout", []), ("battle", loot(100, 100, 0)), ("home", [])]
    [summary] = run(AttackTracker(), frames, village=old)
    assert summary.village_id is None


def test_no_summary_when_nothing_was_readable():
    frames = [("scout", []), ("battle", []), ("battle", loot(None, None, None)), ("home", [])]
    assert run(AttackTracker(), frames) == []


def test_observer_records_attack_end_to_end(tmp_path):
    """Recherche -> combat -> retour au village, à travers le vrai service d'observation."""
    settings = Settings(data_dir=tmp_path, screenshots_dir=tmp_path / "s", observations_dir=tmp_path / "o",
                        database_path=tmp_path / "t.db", backups_dir=tmp_path / "b", logs_dir=tmp_path / "l",
                        observe_interval_s=0.2)
    db = Database.open(settings.database_path, settings.backups_dir)
    script = ([FrameAnalysis(ScreenDetection(GameScreen.SCOUT, 1.0), [], loot(600_000, 600_000, 10_000))] * 3
              + [FrameAnalysis(ScreenDetection(GameScreen.BATTLE, 1.0), [], loot(150_000, 90_000, 4_000))] * 4
              + [FrameAnalysis(ScreenDetection(GameScreen.HOME, 1.0), [], [])])
    frames = iter(script)
    service = ObserverService(settings, db, lambda: np.zeros((8, 8, 3), np.uint8),
                              lambda _bgr: next(frames, script[-1]))
    service.start(interval_s=0.2)
    try:
        deadline = time.monotonic() + 10
        while service.status().last_attack is None and time.monotonic() < deadline:
            time.sleep(0.05)
    finally:
        service.stop()
    attack = service.status().last_attack
    assert (attack.gained_gold, attack.gained_elixir, attack.gained_dark_elixir) == (450_000, 510_000, 6_000)
    with db.session() as session:
        stored = attack_for_village(session, attack.village_id)
        assert stored is not None and stored.gained_gold == 450_000
    db.close()


def test_remaining_estimate():
    assert remaining_estimate(deque([500, 300, 300])) == 300
    assert remaining_estimate(deque([300, 30, 300])) == 300  # lecture isolée écartée
    assert remaining_estimate(deque([500, 100])) == 100  # rien de confirmé : dernière lecture


def test_farm_score_follows_the_priority():
    attack = AttackSummary(village_id=1, started_at=T0, ended_at=T0, available_gold=650_000,
                           available_elixir=720_000, available_dark_elixir=16_000, gained_gold=600_000,
                           gained_elixir=600_000, gained_dark_elixir=2_000)
    balanced = rate_attack(attack, ScoringPreferences())
    dark = rate_attack(attack, ScoringPreferences(priority=Priority.DARK_ELIXIR))
    assert (balanced.farm_score, balanced.farm_rating) == (84, "excellent")  # 40 + 40 + 20 x 20 %
    assert (dark.farm_score, dark.farm_rating) == (36, "faible")  # 10 + 10 + 80 x 20 %
