"""Score de rentabilité d'un village, sur 100, EXPLIQUÉ (cahier des charges §8).

Calcul, pour chaque ressource :
    butin net    = butin disponible - coût de l'armée (pas en dessous de 0)
    atteinte     = butin net / butin visé (plafonné à 100 %)
    points       = 100 x poids de la ressource x atteinte
Score = somme des points. Exemple : or net 300 000 pour 600 000 visés, poids 40 %
-> 50 % x 40 = 20 points.

Les critères pas encore mesurables (difficulté, temps, trophées) apparaissent
dans l'explication comme « non disponible » et n'influencent pas le score.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from app.analysis.scoring import ScoringPreferences
from app.analysis.village_analysis import RESOURCE_LABELS, Resource, VillageSheet
from app.vision.digits import MIN_RELIABLE_CONFIDENCE


class Recommendation(str, Enum):
    VERY_GOOD = "très intéressant"
    GOOD = "intéressant"
    AVERAGE = "moyen"
    SKIP = "à passer"


class ScoreFactor(BaseModel):
    """Une ligne de l'explication du score."""

    label: str
    detail: str
    points: float = 0.0
    max_points: float = 0.0
    available: bool = True


class ProfitabilityResult(BaseModel):
    score: int
    recommendation: Recommendation
    factors: list[ScoreFactor]
    warnings: list[str]

    def explain(self) -> list[str]:
        """Explication lisible, ligne par ligne."""
        lines = [f"Score : {self.score}/100 -> {self.recommendation.value}"]
        for f in self.factors:
            if f.available:
                lines.append(f"  {f.label:<12} {f.points:5.1f} / {f.max_points:4.1f} pts  {f.detail}")
            else:
                lines.append(f"  {f.label:<12}   non disponible  {f.detail}")
        lines += [f"  ! {w}" for w in self.warnings]
        return lines


def _fmt(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def _resource_factor(sheet: VillageSheet, prefs: ScoringPreferences, resource: Resource, weight: float) -> ScoreFactor:
    available = sheet.loot.get(resource)
    cost = prefs.army_cost.get(resource)
    target = prefs.target_loot.get(resource)
    net = max(0, available - cost)
    reach = min(1.0, net / target)
    max_points = 100 * weight
    detail = f"{_fmt(net)} / {_fmt(target)} visés ({reach:.0%}), poids {weight:.0%}"
    if cost:
        detail = f"{_fmt(available)} - {_fmt(cost)} armée = " + detail
    return ScoreFactor(label=RESOURCE_LABELS[resource], detail=detail, points=max_points * reach, max_points=max_points)


# Critères du cahier des charges qui nécessitent la détection des bâtiments.
_NOT_YET_MEASURED = (
    ("Difficulté", "nécessite la détection des défenses"),
    ("Temps", "nécessite la détection des bâtiments"),
    ("Trophées", "nécessite la détection de l'hôtel de ville"),
)


def compute_profitability(sheet: VillageSheet, prefs: ScoringPreferences | None = None) -> ProfitabilityResult:
    prefs = prefs or ScoringPreferences()
    weights = prefs.weights()
    factors = [_resource_factor(sheet, prefs, r, weights[r]) for r in Resource]
    factors += [ScoreFactor(label=label, detail=why, available=False) for label, why in _NOT_YET_MEASURED]
    score = round(sum(f.points for f in factors))

    warnings: list[str] = []
    if not any(prefs.army_cost.get(r) for r in Resource):
        warnings.append("coût de l'armée non configuré : rentabilité brute (army_cost dans preferences.json)")
    if sheet.detection_confidence < MIN_RELIABLE_CONFIDENCE:
        warnings.append(f"lecture du butin incertaine (confiance {sheet.detection_confidence:.2f})")

    below_minimum = sheet.loot.gold + sheet.loot.elixir < prefs.min_gold_elixir
    if below_minimum:
        warnings.append(f"or + élixir sous le minimum de {_fmt(prefs.min_gold_elixir)}")
    return ProfitabilityResult(
        score=score,
        recommendation=Recommendation.SKIP if below_minimum else _recommend(score, prefs),
        factors=factors,
        warnings=warnings,
    )


def _recommend(score: int, prefs: ScoringPreferences) -> Recommendation:
    if score >= prefs.very_good_threshold:
        return Recommendation.VERY_GOOD
    if score >= prefs.good_threshold:
        return Recommendation.GOOD
    if score >= prefs.average_threshold:
        return Recommendation.AVERAGE
    return Recommendation.SKIP
