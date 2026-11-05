"""Récapitulatif d'attaque : combien de butin récupéré, sur combien de disponible.

Pendant un combat, Clash of Clans affiche en haut à gauche le « Butin disponible »
RESTANT, qui diminue à mesure que tu pilles. Donc :

    récupéré = butin au début du combat - butin restant à la fin

- Butin au début : celui lu pendant la recherche (écran calme, lecture la plus sûre),
  si le combat suit directement la recherche de ce village. Sinon (observation lancée
  en plein combat, revanche...) : première lecture fiable pendant le combat.
- Butin restant : la valeur la plus récente lue AU MOINS DEUX FOIS parmi les dernières
  lectures fiables (à la fin du combat, le compteur ne bouge plus). Les effets visuels
  (sorts, explosions) peuvent fausser une image : une lecture isolée erronée n'est donc
  pas retenue, et une lecture supérieure au butin de départ est ignorée. À défaut de
  valeur confirmée, la dernière lecture est utilisée.

Simple observation de l'écran : rien n'est envoyé au jeu.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from pydantic import BaseModel

from app.analysis.profitability import compute_profitability
from app.analysis.scoring import ScoringPreferences
from app.analysis.village_analysis import Loot, build_sheet
from app.observation_models import ObservedVillage
from app.vision.digits import MIN_RELIABLE_CONFIDENCE
from app.vision.models import ElementType
from app.vision.resources import ResourceReading

RESOURCES = (ElementType.GOLD, ElementType.ELIXIR, ElementType.DARK_ELIXIR)
LAST_READINGS = 5  # lectures conservées pour estimer le butin restant
# Le combat est rattaché au village de la recherche s'il commence peu après.
MAX_SCOUT_TO_BATTLE = timedelta(minutes=3)
BATTLE, SCOUT = "battle", "scout"


class AttackSummary(BaseModel):
    """Résultat d'une attaque. `gained_*` vaut None si la ressource n'a pas pu être lue."""

    village_id: int | None  # village de la recherche, None si le combat n'a pas pu y être rattaché
    started_at: datetime
    ended_at: datetime
    available_gold: int
    available_elixir: int
    available_dark_elixir: int
    gained_gold: int | None
    gained_elixir: int | None
    gained_dark_elixir: int | None
    # Note du farm : même calcul que le score d'un village, appliqué au butin RÉCUPÉRÉ
    # (ressource prioritaire, butin visé, coût de l'armée). None tant que non notée.
    farm_score: int | None = None
    farm_rating: str | None = None


@dataclass
class _Battle:
    started_at: datetime
    village_id: int | None
    available: dict[ElementType, int | None]
    readings: dict[ElementType, deque[int]] = field(
        default_factory=lambda: {r: deque(maxlen=LAST_READINGS) for r in RESOURCES})


class AttackTracker:
    """Suit les combats image par image. `update` renvoie un résumé quand un combat se termine."""

    def __init__(self) -> None:
        self._battle: _Battle | None = None
        self._previous_screen: str | None = None

    def update(
        self,
        confirmed_screen: str | None,
        loot: list[ResourceReading],
        last_village: ObservedVillage | None,
        now: datetime,
    ) -> AttackSummary | None:
        previous, self._previous_screen = self._previous_screen, confirmed_screen
        if confirmed_screen == BATTLE:
            if self._battle is None:
                self._battle = self._start(previous, last_village, now)
            self._record(loot)
            return None
        if self._battle is not None:  # l'écran de combat vient de disparaître : fin du combat
            battle, self._battle = self._battle, None
            return self._finish(battle, now)
        return None

    @staticmethod
    def _start(previous: str | None, village: ObservedVillage | None, now: datetime) -> _Battle:
        from_scout = (previous == SCOUT and village is not None
                      and now - village.analyzed_at <= MAX_SCOUT_TO_BATTLE)
        if from_scout:
            assert village is not None
            return _Battle(now, village.village_id, {
                ElementType.GOLD: village.gold,
                ElementType.ELIXIR: village.elixir,
                ElementType.DARK_ELIXIR: village.dark_elixir,
            })
        return _Battle(now, None, {r: None for r in RESOURCES})  # départ lu pendant le combat

    def _record(self, loot: list[ResourceReading]) -> None:
        assert self._battle is not None
        for reading in loot:
            if reading.value is None or reading.confidence < MIN_RELIABLE_CONFIDENCE:
                continue
            available = self._battle.available.get(reading.resource)
            if available is None:  # combat non rattaché : la première lecture fiable sert de départ
                self._battle.available[reading.resource] = reading.value
            elif reading.value > available:
                continue  # impossible (le butin ne fait que baisser) : lecture erronée
            self._battle.readings[reading.resource].append(reading.value)

    @staticmethod
    def _finish(battle: _Battle, now: datetime) -> AttackSummary | None:
        gained: dict[ElementType, int | None] = {}
        for resource in RESOURCES:
            available, last = battle.available[resource], battle.readings[resource]
            gained[resource] = (max(0, available - remaining_estimate(last))
                                if available is not None and last else None)
        if all(value is None for value in gained.values()):
            return None  # rien de lisible pendant le combat : pas de récapitulatif
        return AttackSummary(
            village_id=battle.village_id, started_at=battle.started_at, ended_at=now,
            available_gold=battle.available[ElementType.GOLD] or 0,
            available_elixir=battle.available[ElementType.ELIXIR] or 0,
            available_dark_elixir=battle.available[ElementType.DARK_ELIXIR] or 0,
            gained_gold=gained[ElementType.GOLD],
            gained_elixir=gained[ElementType.ELIXIR],
            gained_dark_elixir=gained[ElementType.DARK_ELIXIR],
        )


def remaining_estimate(readings: deque[int]) -> int:
    """Butin restant : dernière valeur lue au moins deux fois, sinon la toute dernière lecture."""
    values = list(readings)
    for value in reversed(values):
        if values.count(value) >= 2:
            return value
    return values[-1]


# Appréciation d'une attaque selon sa note (mêmes seuils que les recommandations de village).
FARM_RATINGS = ("excellent", "bon", "moyen", "faible")


def rate_attack(attack: AttackSummary, prefs: ScoringPreferences) -> AttackSummary:
    """Ajoute la note du farm : le butin récupéré est noté comme le butin d'un village.

    Une ressource non lue compte pour 0 (note prudente). Exemple, priorité élixir noir et
    10 000 visés : récupérer 8 000 d'élixir noir vaut 64 points sur les 80 de cette ressource.
    """
    gained = Loot(gold=attack.gained_gold or 0, elixir=attack.gained_elixir or 0,
                  dark_elixir=attack.gained_dark_elixir or 0)
    score = compute_profitability(build_sheet(gained, 1.0), prefs).score
    if score >= prefs.very_good_threshold:
        rating = "excellent"
    elif score >= prefs.good_threshold:
        rating = "bon"
    elif score >= prefs.average_threshold:
        rating = "moyen"
    else:
        rating = "faible"
    return attack.model_copy(update={"farm_score": score, "farm_rating": rating})
