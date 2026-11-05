"""Tests des stratégies et du simulateur."""
import json
from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from app.analysis.scoring import Priority, ScoringPreferences
from app.analysis.village_analysis import Loot, build_sheet
from app.strategy.simulator import (
    DEFAULT_SEARCH_TIME_S,
    SignedLoot,
    compare_strategies,
    loot_points,
    measure_search_time,
    simulate,
)
from app.strategy.strategies import (
    ASSUMPTIONS_FILE,
    DEFAULT_STRATEGIES,
    CaptureRates,
    SimulationAssumptions,
    Strategy,
    load_assumptions,
)

T0 = datetime(2026, 11, 5, 10, 0, 0)
NO_SKIP = Strategy(key="all", label="Tout", description="", priority=Priority.BALANCED, min_score=0)
PICKY = Strategy(key="picky", label="Exigeant", description="", priority=Priority.BALANCED, min_score=90)
FULL_RATES = SimulationAssumptions(capture_rates=CaptureRates(gold=1, elixir=1, dark_elixir=1),
                                   search_cost_gold=0, attack_duration_s=100)


def village(gold, elixir, dark, seconds=0):
    return build_sheet(Loot(gold=gold, elixir=elixir, dark_elixir=dark), 0.9, T0 + timedelta(seconds=seconds))


RICH = village(600_000, 600_000, 10_000)  # score 100
POOR = village(60_000, 60_000, 1_000)  # score 10


def test_measure_search_time_ignores_long_gaps():
    sheets = [village(1, 1, 1, s) for s in (0, 4, 10, 15, 900, 905)]
    assert measure_search_time(sheets) == 5  # écarts 4, 6, 5, 5 (885 s ignoré)
    assert measure_search_time([RICH]) is None


def test_simulate_counts_loot_costs_and_time():
    prefs = ScoringPreferences(army_cost=Loot(elixir=100_000))
    result = simulate(NO_SKIP, [RICH, POOR], prefs, FULL_RATES, search_time_s=10)
    assert result.attacks == 2 and result.villages_seen == 2
    assert result.gross_loot.elixir == 660_000
    assert result.costs.elixir == 200_000 and result.net_loot.elixir == 460_000
    assert result.duration_s == 2 * 10 + 2 * 100


def test_threshold_skips_poor_villages():
    result = simulate(PICKY, [RICH, POOR], ScoringPreferences(), FULL_RATES, search_time_s=10)
    assert result.attacks == 1 and result.skip_rate == 0.5
    assert result.gross_loot.gold == 600_000


def test_search_cost_is_paid_for_every_village_seen():
    assumptions = SimulationAssumptions(search_cost_gold=1500)
    result = simulate(PICKY, [POOR] * 4, ScoringPreferences(), assumptions, search_time_s=5)
    assert result.attacks == 0 and result.net_loot.gold == -6000  # 4 recherches, aucun butin


def test_capture_rate_hypothesis_applies():
    half = SimulationAssumptions(capture_rates=CaptureRates(gold=0.5, elixir=0.5, dark_elixir=0.5))
    result = simulate(NO_SKIP, [RICH], ScoringPreferences(), half, search_time_s=5)
    assert result.gross_loot.gold == 300_000


def test_loot_points_matches_score_scale():
    target = SignedLoot(gold=600_000, elixir=600_000, dark_elixir=10_000)
    assert loot_points(target, ScoringPreferences()) == pytest.approx(100)


def test_compare_sorts_by_points_per_hour():
    sheets = [RICH if i % 3 == 0 else POOR for i in range(9)]
    sheets = [village(s.loot.gold, s.loot.elixir, s.loot.dark_elixir, i * 5) for i, s in enumerate(sheets)]
    results, search_time = compare_strategies([NO_SKIP, PICKY], sheets, assumptions=FULL_RATES)
    assert search_time == 5
    assert [r.strategy.key for r in results] == ["picky", "all"]  # trier les villages paie
    assert results[0].points_per_hour >= results[1].points_per_hour


def test_compare_uses_fallback_search_time():
    _, search_time = compare_strategies([NO_SKIP], [RICH])
    assert search_time == DEFAULT_SEARCH_TIME_S


def test_default_strategies_cover_the_specification():
    keys = {s.key for s in DEFAULT_STRATEGIES}
    assert {"gold", "elixir", "dark_elixir", "balanced"} <= keys


def test_assumptions_are_labelled():
    lines = SimulationAssumptions().describe(5.0)
    assert any(line.startswith("[supposé]") for line in lines)
    assert any(line.startswith("[observé]") for line in lines)


def test_assumptions_validation_and_file(tmp_path):
    with pytest.raises(ValidationError):
        CaptureRates(gold=1.5)
    assert load_assumptions(tmp_path) == SimulationAssumptions()
    (tmp_path / ASSUMPTIONS_FILE).write_text(json.dumps({"attack_duration_s": 120}), encoding="utf-8")
    assert load_assumptions(tmp_path).attack_duration_s == 120
