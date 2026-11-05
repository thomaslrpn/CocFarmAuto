"""Simulation des stratégies, rejouée sur les villages réellement observés.

Pour une stratégie, on parcourt la séquence de villages vus par le joueur :
- chaque village vu coûte une recherche (or + temps) ;
- si son score (pondéré selon la stratégie) atteint le minimum, on « attaque » :
  butin récupéré = butin disponible x part récupérée (hypothèse), moins le coût
  de l'armée, plus la durée de l'attaque.

Pour COMPARER des stratégies qui visent des ressources différentes, on convertit
le butin net en « points » avec les préférences de l'utilisateur (même échelle
que le score : 100 points = butin visé atteint pour chaque ressource).
"""
from __future__ import annotations

import statistics
from collections.abc import Sequence

from pydantic import BaseModel

from app.analysis.profitability import compute_profitability
from app.analysis.scoring import ScoringPreferences
from app.analysis.village_analysis import Loot, Resource, VillageSheet
from app.strategy.strategies import SimulationAssumptions, Strategy

DEFAULT_SEARCH_TIME_S = 5.0  # repli si aucune mesure possible (valeur médiane observée le 2026-11-05)
MAX_SEARCH_GAP_S = 60.0  # au-delà, deux observations ne sont pas des recherches consécutives


class SignedLoot(BaseModel):
    """Comme `Loot`, mais peut être négatif (bilan net)."""

    gold: float = 0.0
    elixir: float = 0.0
    dark_elixir: float = 0.0

    def get(self, resource: Resource) -> float:
        return getattr(self, resource.value)


class SimulationResult(BaseModel):
    strategy: Strategy
    villages_seen: int
    attacks: int
    gross_loot: SignedLoot  # butin récupéré
    costs: SignedLoot  # armée + recherches
    net_loot: SignedLoot
    duration_s: float
    net_per_hour: SignedLoot
    points_per_hour: float  # valeur du butin net selon les préférences, par heure

    @property
    def skip_rate(self) -> float:
        return 1 - self.attacks / self.villages_seen if self.villages_seen else 0.0


def measure_search_time(sheets: Sequence[VillageSheet]) -> float | None:
    """Temps médian entre deux villages consécutifs (écarts > 60 s ignorés)."""
    times = sorted(s.analyzed_at for s in sheets)
    gaps = [(b - a).total_seconds() for a, b in zip(times, times[1:])]
    gaps = [g for g in gaps if 0 < g <= MAX_SEARCH_GAP_S]
    return statistics.median(gaps) if gaps else None


def loot_points(loot: SignedLoot, prefs: ScoringPreferences) -> float:
    """Valeur d'un butin sur l'échelle du score (non plafonnée, peut être négative)."""
    weights = prefs.weights()
    return sum(100 * weights[r] * loot.get(r) / prefs.target_loot.get(r) for r in Resource)


def simulate(
    strategy: Strategy,
    sheets: Sequence[VillageSheet],
    prefs: ScoringPreferences,
    assumptions: SimulationAssumptions,
    search_time_s: float,
) -> SimulationResult:
    strategy_prefs = prefs.model_copy(update={"priority": strategy.priority})
    rates = assumptions.capture_rates
    gross = {r: 0.0 for r in Resource}
    attacks = 0
    for sheet in sheets:
        if compute_profitability(sheet, strategy_prefs).score >= strategy.min_score:
            attacks += 1
            for r in Resource:
                gross[r] += sheet.loot.get(r) * getattr(rates, r.value)

    army: Loot = prefs.army_cost
    costs = {r: attacks * army.get(r) for r in Resource}
    costs[Resource.GOLD] += len(sheets) * assumptions.search_cost_gold
    net = {r: gross[r] - costs[r] for r in Resource}

    attack_time = assumptions.attack_duration_s + assumptions.army_ready_delay_s
    duration = len(sheets) * search_time_s + attacks * attack_time
    hours = duration / 3600 if duration else 0.0
    net_loot = SignedLoot(**{r.value: v for r, v in net.items()})
    per_hour = SignedLoot(**{r.value: (v / hours if hours else 0.0) for r, v in net.items()})
    return SimulationResult(
        strategy=strategy,
        villages_seen=len(sheets),
        attacks=attacks,
        gross_loot=SignedLoot(**{r.value: v for r, v in gross.items()}),
        costs=SignedLoot(**{r.value: v for r, v in costs.items()}),
        net_loot=net_loot,
        duration_s=duration,
        net_per_hour=per_hour,
        points_per_hour=loot_points(per_hour, prefs),
    )


def compare_strategies(
    strategies: Sequence[Strategy],
    sheets: Sequence[VillageSheet],
    prefs: ScoringPreferences | None = None,
    assumptions: SimulationAssumptions | None = None,
) -> tuple[list[SimulationResult], float]:
    """Simule chaque stratégie ; résultats triés du meilleur au moins bon rendement.

    Retourne aussi le temps par village utilisé (réglé, mesuré, ou repli).
    """
    prefs = prefs or ScoringPreferences()
    assumptions = assumptions or SimulationAssumptions()
    ordered = sorted(sheets, key=lambda s: s.analyzed_at)
    search_time = assumptions.search_time_s or measure_search_time(ordered) or DEFAULT_SEARCH_TIME_S
    results = [simulate(s, ordered, prefs, assumptions, search_time) for s in strategies]
    return sorted(results, key=lambda r: -r.points_per_hour), search_time
