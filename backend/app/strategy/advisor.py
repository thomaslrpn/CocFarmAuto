"""Évaluation complète d'un village : score + stratégie recommandée.

Point d'entrée unique utilisé par le mode observation, l'import et (bientôt) l'API,
pour que tous calculent exactement de la même façon.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from app.analysis.profitability import ProfitabilityResult, compute_profitability
from app.analysis.scoring import ScoringPreferences
from app.analysis.village_analysis import VillageSheet
from app.strategy.strategies import DEFAULT_STRATEGIES, Strategy


@dataclass(frozen=True)
class VillageEvaluation:
    sheet: VillageSheet
    result: ProfitabilityResult  # score selon les préférences de l'utilisateur
    strategy: Strategy | None  # None = aucune stratégie n'attaquerait : à passer


def recommend_strategy(
    sheet: VillageSheet,
    prefs: ScoringPreferences,
    strategies: Sequence[Strategy] = DEFAULT_STRATEGIES,
) -> Strategy | None:
    """Parmi les stratégies qui TRIENT (score minimal > 0), celle qui note le mieux ce village,
    à condition qu'elle l'attaque (score >= son minimum)."""
    best: tuple[int, Strategy] | None = None
    for strategy in strategies:
        if strategy.min_score <= 0:  # « sans tri » : référence, jamais recommandée
            continue
        score = compute_profitability(sheet, prefs.model_copy(update={"priority": strategy.priority})).score
        if score >= strategy.min_score and (best is None or score > best[0]):
            best = (score, strategy)
    return best[1] if best else None


def evaluate_village(sheet: VillageSheet, prefs: ScoringPreferences) -> VillageEvaluation:
    return VillageEvaluation(sheet, compute_profitability(sheet, prefs), recommend_strategy(sheet, prefs))
