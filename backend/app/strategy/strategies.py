"""Stratégies de farm théoriques et hypothèses de simulation (cahier des charges §9).

Une stratégie = une façon de CHOISIR les villages à attaquer :
- une ressource prioritaire (pondère le score de rentabilité) ;
- un score minimal pour attaquer (sinon on passe au suivant).

Tout ce que l'on ne sait pas mesurer est regroupé dans `SimulationAssumptions`
et affiché comme HYPOTHÈSE dans les résultats : rien n'est présenté comme exact.
"""
from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from app.analysis.scoring import Priority
from app.config import load_user_json

ASSUMPTIONS_FILE = "simulation.json"


class CaptureRates(BaseModel):
    """Part du butin disponible réellement récupérée lors d'une attaque (0 à 1)."""

    gold: float = Field(default=0.75, ge=0.0, le=1.0)
    elixir: float = Field(default=0.75, ge=0.0, le=1.0)
    dark_elixir: float = Field(default=0.75, ge=0.0, le=1.0)


class SimulationAssumptions(BaseModel):
    """Paramètres de simulation. Chaque champ indique s'il est OBSERVÉ ou SUPPOSÉ."""

    # SUPPOSÉ : part du butin récupérée (dépend de l'armée et du joueur).
    capture_rates: CaptureRates = CaptureRates()
    # SUPPOSÉ : durée totale d'une attaque (un combat dure 3 min au maximum).
    attack_duration_s: float = Field(default=180.0, gt=0)
    # SUPPOSÉ : attente entre deux attaques (entraînement de l'armée) ; 0 = armée boostée / prête.
    army_ready_delay_s: float = Field(default=0.0, ge=0)
    # OBSERVÉ : coût en or d'une recherche (affiché sur le bouton « Suivant » : 1 500).
    search_cost_gold: int = Field(default=1500, ge=0)
    # OBSERVÉ si possible : temps entre deux villages. None = mesuré sur les observations.
    search_time_s: float | None = Field(default=None, gt=0)

    def describe(self, measured_search_time_s: float) -> list[str]:
        """Liste lisible des hypothèses utilisées (affichée avec les résultats)."""
        r = self.capture_rates
        source = "réglé" if self.search_time_s is not None else "mesuré sur tes observations"
        return [
            f"[supposé] butin récupéré : or {r.gold:.0%}, élixir {r.elixir:.0%}, noir {r.dark_elixir:.0%}",
            f"[supposé] durée d'une attaque : {self.attack_duration_s:.0f} s"
            + (f" + {self.army_ready_delay_s:.0f} s d'attente d'armée" if self.army_ready_delay_s else ""),
            f"[observé] coût d'une recherche : {self.search_cost_gold} or",
            f"[{'observé' if self.search_time_s is None else 'réglé'}] temps par village vu : "
            f"{measured_search_time_s:.1f} s ({source})",
            "[supposé] la séquence de villages rencontrés aurait été la même pour chaque stratégie",
        ]


class Strategy(BaseModel):
    key: str
    label: str
    description: str
    priority: Priority
    min_score: int = Field(ge=0, le=100)


DEFAULT_STRATEGIES: tuple[Strategy, ...] = (
    Strategy(key="gold", label="Farm or", priority=Priority.GOLD, min_score=70,
             description="Attaque les villages riches en or, passe les autres."),
    Strategy(key="elixir", label="Farm élixir", priority=Priority.ELIXIR, min_score=70,
             description="Attaque les villages riches en élixir."),
    Strategy(key="dark_elixir", label="Farm élixir noir", priority=Priority.DARK_ELIXIR, min_score=70,
             description="Attaque les villages riches en élixir noir."),
    Strategy(key="balanced", label="Farm équilibré", priority=Priority.BALANCED, min_score=70,
             description="Attaque les villages au bon butin global."),
    Strategy(key="no_skip", label="Sans tri (référence)", priority=Priority.BALANCED, min_score=0,
             description="Attaque chaque village : sert de point de comparaison."),
)


def load_assumptions(data_dir: Path) -> SimulationAssumptions:
    """Hypothèses de simulation de l'utilisateur (`simulation.json`), sinon valeurs par défaut."""
    return load_user_json(data_dir, ASSUMPTIONS_FILE, SimulationAssumptions)
