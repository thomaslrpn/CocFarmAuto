"""Alertes : prévenir le joueur quand un village vaut le coup.

Appelé par le mode observation à chaque village enregistré. Selon les réglages
(Paramètres → Alertes) :
- son : carillon joué directement par le moteur, donc même si
  la fenêtre de l'application est cachée derrière le jeu ;
- notification Windows : le moteur écrit un événement sur sa sortie standard,
  lu par l'application de bureau qui affiche la notification (voir
  desktop/src-tauri/src/backend.rs). Sans application de bureau (mode
  développement en terminal), l'événement est simplement ignoré.

Rien n'est envoyé au jeu : c'est une alerte pour le joueur, pas une action.
"""
from __future__ import annotations

import json
import logging
import sys
from collections.abc import Callable
from pathlib import Path

from app.analysis.profitability import Recommendation
from app.database.database import Database
from app.observer_service import ObservedVillage
from app.user_settings import AppPreferences, load_user_settings

logger = logging.getLogger(__name__)

# Préfixe des lignes d'événement sur la sortie standard (protocole avec l'application Rust).
EVENT_PREFIX = "COCAF-EVENT "

# Recommandations qui déclenchent une alerte, selon le réglage `alert_level`.
ALERT_LEVELS: dict[str, frozenset[str]] = {
    "off": frozenset(),
    "very_interesting": frozenset({Recommendation.VERY_GOOD.value}),
    "interesting": frozenset({Recommendation.VERY_GOOD.value, Recommendation.GOOD.value}),
}


def should_alert(village: ObservedVillage, prefs: AppPreferences) -> bool:
    return village.recommendation in ALERT_LEVELS[prefs.alert_level]


# Carillon de l'application (généré par app/assets/make_alert_sound.py), livré avec le moteur.
ALERT_SOUND = Path(__file__).parent / "assets" / "alert.wav"


def play_alert_sound() -> None:
    """Joue le carillon des alertes, sans bloquer (aucun effet hors Windows)."""
    if sys.platform != "win32":
        return
    import winsound  # module standard, Windows uniquement

    winsound.PlaySound(str(ALERT_SOUND), winsound.SND_FILENAME | winsound.SND_ASYNC)


def emit_event(event: dict) -> None:
    """Écrit un événement pour l'application de bureau (une ligne JSON sur la sortie standard)."""
    if sys.stdout is None:  # exécutable sans console ni sortie redirigée
        return
    print(EVENT_PREFIX + json.dumps(event, ensure_ascii=False), flush=True)


class AlertService:
    """Décide et déclenche les alertes. Son et émission injectables pour les tests."""

    def __init__(
        self,
        db: Database,
        data_dir: Path,
        play_sound: Callable[[], None] = play_alert_sound,
        emit: Callable[[dict], None] = emit_event,
    ) -> None:
        self._db = db
        self._data_dir = data_dir
        self._play_sound = play_sound
        self._emit = emit

    def on_village(self, village: ObservedVillage) -> None:
        # Réglages relus à chaque village : une modification s'applique immédiatement.
        with self._db.session() as session:
            prefs = load_user_settings(session, self._data_dir).app
        if not should_alert(village, prefs):
            return
        logger.info("Alerte : village %s (%d/100)", village.recommendation, village.score,
                    extra={"village_id": village.village_id, "score": village.score})
        try:
            if prefs.alert_sound:
                self._play_sound()
            if prefs.alert_notification:
                self._emit({
                    "type": "village_alert",
                    "village_id": village.village_id,
                    "score": village.score,
                    "recommendation": village.recommendation,
                    "gold": village.gold,
                    "elixir": village.elixir,
                    "dark_elixir": village.dark_elixir,
                })
        except Exception:  # une alerte ratée ne doit jamais arrêter l'observation
            logger.exception("Alerte impossible")

    def test(self) -> dict[str, bool]:
        """Déclenche une alerte d'exemple avec les réglages actuels (bouton « Tester l'alerte »)."""
        with self._db.session() as session:
            prefs = load_user_settings(session, self._data_dir).app
        if prefs.alert_sound:
            self._play_sound()
        if prefs.alert_notification:
            self._emit({"type": "village_alert", "village_id": 0, "score": 95,
                        "recommendation": "très intéressant (test)",
                        "gold": 650_000, "elixir": 720_000, "dark_elixir": 5_000})
        return {"sound": prefs.alert_sound, "notification": prefs.alert_notification}
