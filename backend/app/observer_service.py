"""Service d'observation : la boucle du mode observation, pilotable (démarrer / arrêter / état).

Utilisé par l'API (tâche de fond) ET par `observe_cli` (premier plan) : un seul code.
LECTURE SEULE : aucune action n'est envoyée au jeu.

Arrêt propre : la boucle vérifie un `threading.Event` entre deux cycles ; un cycle
en cours (capture, analyse, enregistrement en base) se termine toujours avant l'arrêt.
"""
from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from datetime import datetime

import numpy as np
from pydantic import BaseModel

from app.analysis.village_analysis import sheet_from_frame
from app.capture.screen import CaptureError, grab_window
from app.capture.window import WindowNotSupportedError, find_window
from app.config import Settings
from app.database.database import Database
from app.database.repository import refresh_daily_statistics, save_evaluation
from app.observer import ScoutRecorder
from app.strategy.advisor import VillageEvaluation, evaluate_village
from app.strategy.strategies import strategy_label
from app.user_settings import load_user_settings
from app.vision.frame import FrameAnalysis
from app.vision.preprocess import to_bgr

logger = logging.getLogger(__name__)

FrameSource = Callable[[], "np.ndarray | None"]  # None = fenêtre du jeu absente
Analyzer = Callable[[np.ndarray], FrameAnalysis]
MIN_INTERVAL_S = 0.2
# Un changement d'écran n'est journalisé que s'il se confirme sur N analyses de suite
# (les transitions nuageuses entre deux villages font sinon « clignoter » l'écran détecté).
SCREEN_CONFIRM_FRAMES = 2


class ObserverError(RuntimeError):
    """Démarrage impossible (déjà en cours, intervalle invalide...)."""


class ObservedVillage(BaseModel):
    village_id: int
    analyzed_at: datetime
    gold: int
    elixir: int
    dark_elixir: int
    score: int
    recommendation: str
    strategy: str


class ObserverStatus(BaseModel):
    running: bool
    started_at: datetime | None = None
    interval_s: float | None = None
    frames: int = 0
    villages_saved: int = 0
    missing_window: int = 0
    errors: int = 0
    last_screen: str | None = None
    last_cycle_ms: float | None = None
    last_village: ObservedVillage | None = None
    last_error: str | None = None


class _ScreenTracker:
    """Détecte les changements d'écran CONFIRMÉS sur SCREEN_CONFIRM_FRAMES analyses de suite."""

    def __init__(self) -> None:
        self.confirmed: str | None = None
        self._candidate: str | None = None
        self._count = 0

    def confirmed_change(self, screen: str) -> bool:
        if screen == self.confirmed:
            self._candidate, self._count = None, 0
            return False
        self._count = self._count + 1 if screen == self._candidate else 1
        self._candidate = screen
        if self._count < SCREEN_CONFIRM_FRAMES:
            return False
        self.confirmed, self._candidate, self._count = screen, None, 0
        return True


def game_window_frames(settings: Settings) -> FrameSource:
    """Source d'images réelle : la fenêtre du jeu (None si elle est introuvable)."""
    def grab() -> np.ndarray | None:
        window = find_window(settings.game_window_title)
        if window is None:
            return None
        image, _method = grab_window(window)
        return to_bgr(image)
    return grab


class ObserverService:
    def __init__(
        self,
        settings: Settings,
        db: Database,
        frame_source: FrameSource,
        analyzer: Analyzer,
        on_village: Callable[[ObservedVillage], None] | None = None,
    ) -> None:
        self._settings = settings
        self._db = db
        self._frames = frame_source
        self._analyze = analyzer
        self._on_village = on_village
        self._lock = threading.Lock()  # protège _status et _thread
        self._stop = threading.Event()
        self._screen_tracker = _ScreenTracker()
        self._thread: threading.Thread | None = None
        self._status = ObserverStatus(running=False)

    # --- Pilotage -----------------------------------------------------------

    def start(self, interval_s: float | None = None) -> ObserverStatus:
        interval = interval_s if interval_s is not None else self._settings.observe_interval_s
        if interval < MIN_INTERVAL_S:
            raise ObserverError(f"Intervalle trop court (minimum {MIN_INTERVAL_S} s)")
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                raise ObserverError("L'observation est déjà en cours")
            self._stop.clear()
            self._status = ObserverStatus(running=True, started_at=datetime.now(), interval_s=interval)
            self._screen_tracker = _ScreenTracker()
            self._thread = threading.Thread(target=self._run, args=(interval,), name="observer", daemon=True)
            self._thread.start()
        logger.info("Observation démarrée (intervalle %.1f s)", interval)
        return self.status()

    def stop(self, timeout_s: float = 10.0) -> ObserverStatus:
        self._stop.set()
        thread = self._thread
        if thread is not None:
            thread.join(timeout_s)
            if thread.is_alive():
                logger.error("L'observation ne s'est pas arrêtée en %.0f s", timeout_s)
        return self.status()

    def status(self) -> ObserverStatus:
        with self._lock:
            return self._status.model_copy()

    def _update(self, **changes: object) -> None:
        with self._lock:
            self._status = self._status.model_copy(update=changes)

    # --- Boucle ---------------------------------------------------------------

    def _run(self, interval: float) -> None:
        recorder = ScoutRecorder(self._settings.observations_dir)
        warned_missing = False
        try:
            while not self._stop.is_set():
                started = time.perf_counter()
                try:
                    found = self._cycle(recorder)
                    if not found and not warned_missing:
                        logger.warning("Fenêtre du jeu introuvable : nouvel essai à chaque cycle")
                    warned_missing = not found
                except WindowNotSupportedError as exc:
                    logger.error("Observation impossible : %s", exc)
                    self._update(errors=self.status().errors + 1, last_error=str(exc))
                    break
                except CaptureError as exc:
                    logger.warning("Capture impossible : %s", exc)
                    self._update(errors=self.status().errors + 1, last_error=str(exc))
                except Exception as exc:  # erreur imprévue : on la journalise et on continue
                    logger.exception("Erreur pendant l'observation")
                    self._update(errors=self.status().errors + 1, last_error=repr(exc))
                elapsed = time.perf_counter() - started
                self._update(last_cycle_ms=round(elapsed * 1000, 1))
                self._stop.wait(max(0.0, interval - elapsed))  # se réveille dès un stop()
        finally:
            self._update(running=False)
            logger.info("Observation arrêtée")

    def _cycle(self, recorder: ScoutRecorder) -> bool:
        """Un cycle. Retourne False si la fenêtre du jeu est absente."""
        bgr = self._frames()
        if bgr is None:
            self._update(missing_window=self.status().missing_window + 1)
            return False
        analysis = self._analyze(bgr)
        screen = analysis.screen.screen.value
        if self._screen_tracker.confirmed_change(screen):  # changements confirmés, pas chaque image
            logger.info("Écran détecté : %s", screen, extra={"screen": screen,
                        "confidence": round(analysis.screen.confidence, 2)})
        self._update(frames=self.status().frames + 1, last_screen=screen)
        json_path = recorder.process(bgr, analysis)
        if json_path is not None:
            sheet = sheet_from_frame(analysis, source_image=json_path.with_suffix(".png").name)
            if sheet is not None:
                self._store(sheet)
        return True

    def _store(self, sheet) -> None:  # type: ignore[no-untyped-def]
        started = time.perf_counter()
        with self._db.session() as session:
            prefs = load_user_settings(session, self._settings.data_dir).preferences  # réglages à jour
            evaluation: VillageEvaluation = evaluate_village(sheet, prefs)
            village = save_evaluation(session, evaluation, prefs)
            refresh_daily_statistics(session, sheet.analyzed_at.date())
            village_id = village.id
        result = evaluation.result
        observed = ObservedVillage(
            village_id=village_id, analyzed_at=sheet.analyzed_at,
            gold=sheet.loot.gold, elixir=sheet.loot.elixir, dark_elixir=sheet.loot.dark_elixir,
            score=result.score, recommendation=result.recommendation.value,
            strategy=strategy_label(evaluation.strategy.key if evaluation.strategy else None),
        )
        self._update(villages_saved=self.status().villages_saved + 1, last_village=observed)
        logger.info("Village enregistré : score %d/100 (%s)", result.score, observed.strategy,
                    extra={"village_id": village_id, "score": result.score,
                           "duration_ms": round((time.perf_counter() - started) * 1000, 1)})
        if self._on_village is not None:
            self._on_village(observed)
