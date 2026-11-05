"""Tests du service d'observation, de son API et des logs (sans le jeu : images simulées)."""
import json
import logging
import time

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.analysis.scoring import Priority, ScoringPreferences
from app.api.app import create_app
from app.api.deps import AppContext
from app.capture.window import WindowNotSupportedError
from app.config import Settings
from app.database.database import Database
from app.database.repository import count_villages
from app.logging_setup import LOG_FILE, configure_logging, memory_handler
from app.observer_service import ObserverError, ObserverService
from app.vision.frame import FrameAnalysis
from app.vision.models import Box, ElementType
from app.vision.resources import ResourceReading
from app.vision.screen_state import GameScreen, ScreenDetection

FRAME = np.zeros((8, 8, 3), np.uint8)
TOKEN = "t"
AUTH = {"Authorization": f"Bearer {TOKEN}"}


def scout(loot=(600_000, 600_000, 10_000)) -> FrameAnalysis:
    readings = [ResourceReading(r, Box(0, 0, 1, 1), [], v, 0.9)
                for r, v in zip((ElementType.GOLD, ElementType.ELIXIR, ElementType.DARK_ELIXIR), loot)]
    return FrameAnalysis(ScreenDetection(GameScreen.SCOUT, 1.0), [], readings)


def wait_until(condition, timeout=5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(0.02)
    return False


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        data_dir=tmp_path, screenshots_dir=tmp_path / "s", observations_dir=tmp_path / "observations",
        database_path=tmp_path / "t.db", backups_dir=tmp_path / "b", logs_dir=tmp_path / "logs",
        observe_interval_s=0.2,
    )


@pytest.fixture
def db(settings):
    database = Database.open(settings.database_path, settings.backups_dir)
    yield database
    database.close()


def make_service(settings, db, frames=lambda: FRAME, analyzer=lambda _bgr: scout(), **kw) -> ObserverService:
    return ObserverService(settings, db, frames, analyzer, **kw)


# --- Service --------------------------------------------------------------------


def test_observes_and_saves_village_in_database(settings, db):
    seen = []
    service = make_service(settings, db, on_village=seen.append)
    service.start()
    try:
        assert wait_until(lambda: service.status().villages_saved == 1)
    finally:
        service.stop()
    status = service.status()
    assert status.running is False and status.frames >= 2 and status.last_screen == "scout"
    assert status.last_village.score == 100 and seen[0].village_id == status.last_village.village_id
    with db.session() as session:
        assert count_villages(session) == 1  # même village vu plusieurs fois : enregistré une fois
    assert len(list(settings.observations_dir.glob("*.png"))) == 1


def test_cannot_start_twice_or_too_fast(settings, db):
    service = make_service(settings, db)
    with pytest.raises(ObserverError):
        service.start(interval_s=0.01)
    service.start()
    try:
        with pytest.raises(ObserverError, match="déjà"):
            service.start()
    finally:
        service.stop()
    service.start()  # redémarrage possible après un arrêt
    service.stop()


def test_stop_is_prompt_even_with_long_interval(settings, db):
    service = make_service(settings, db)
    service.start(interval_s=30)
    assert wait_until(lambda: service.status().frames == 1)
    started = time.monotonic()
    service.stop()
    assert time.monotonic() - started < 2 and not service.status().running


def test_missing_window_is_counted(settings, db):
    service = make_service(settings, db, frames=lambda: None)
    service.start()
    assert wait_until(lambda: service.status().missing_window >= 2)
    service.stop()
    assert service.status().frames == 0


def test_unexpected_errors_do_not_stop_observation(settings, db):
    calls = {"n": 0}

    def flaky(_bgr):
        calls["n"] += 1
        if calls["n"] == 1:
            raise ValueError("image corrompue")
        return scout()

    service = make_service(settings, db, analyzer=flaky)
    service.start()
    assert wait_until(lambda: service.status().villages_saved == 1)
    service.stop()
    assert service.status().errors == 1 and "image corrompue" in service.status().last_error


def test_unsupported_platform_stops_observation(settings, db):
    def unsupported():
        raise WindowNotSupportedError("pas Windows")

    service = make_service(settings, db, frames=unsupported)
    service.start()
    assert wait_until(lambda: not service.status().running)
    assert service.status().last_error == "pas Windows"


# --- API ------------------------------------------------------------------------


@pytest.fixture
def client(settings, db):
    service = make_service(settings, db)
    context = AppContext(settings=settings, db=db, token=TOKEN, vision_ready=True, observer=service)
    with TestClient(create_app(context)) as c:
        yield c
    service.stop()


def test_api_start_status_stop(client):
    assert client.get("/api/observer", headers=AUTH).json()["running"] is False
    started = client.post("/api/observer/start", headers=AUTH, json={"interval_s": 0.2})
    assert started.status_code == 200 and started.json()["running"] is True
    assert client.post("/api/observer/start", headers=AUTH).status_code == 409  # déjà en cours
    assert wait_until(lambda: client.get("/api/observer", headers=AUTH).json()["villages_saved"] == 1)
    stopped = client.post("/api/observer/stop", headers=AUTH).json()
    assert stopped["running"] is False and stopped["last_village"]["score"] == 100
    assert client.post("/api/observer/start", headers=AUTH, json={"interval_s": 0.01}).status_code == 422


def test_api_observer_requires_token(client):
    assert client.post("/api/observer/start").status_code == 401


def test_api_without_vision_models(settings, db):
    context = AppContext(settings=settings, db=db, token=TOKEN, vision_ready=False, observer=None)
    with TestClient(create_app(context)) as c:
        assert c.get("/api/observer", headers=AUTH).json()["running"] is False
        assert c.post("/api/observer/start", headers=AUTH).status_code == 409


# --- Logs -----------------------------------------------------------------------


def test_logs_memory_file_and_api(settings, client):
    configure_logging(settings.logs_dir, console_level=logging.CRITICAL)
    log = logging.getLogger("app.capture.test")
    last_id = max((e.id for e in memory_handler().entries(limit=500)), default=0)
    log.info("capture faite", extra={"duration_ms": 12.5})
    log.error("capture ratée")

    entries = client.get(f"/api/logs?after_id={last_id}", headers=AUTH).json()
    assert [e["message"] for e in entries] == ["capture faite", "capture ratée"]
    assert entries[0]["category"] == "capture" and entries[0]["data"] == {"duration_ms": 12.5}
    errors = client.get(f"/api/logs?after_id={last_id}&level=ERROR", headers=AUTH).json()
    assert [e["message"] for e in errors] == ["capture ratée"]

    lines = (settings.logs_dir / LOG_FILE).read_text(encoding="utf-8").splitlines()
    record = json.loads(next(line for line in lines if "capture faite" in line))
    assert record["level"] == "INFO" and record["duration_ms"] == 12.5
    for handler in logging.getLogger().handlers[:]:  # ferme le fichier (Windows) ; n'affecte pas les autres tests
        handler.close()
        logging.getLogger().removeHandler(handler)


def test_screen_changes_are_logged_once(settings, db):
    configure_logging(None, console_level=logging.CRITICAL)
    last_id = max((e.id for e in memory_handler().entries(limit=500)), default=0)
    # Village, puis 1 image « inconnue » isolée (transition nuageuse), puis recherche
    screens = iter([GameScreen.HOME] * 5 + [GameScreen.UNKNOWN] + [GameScreen.SCOUT] * 50)

    def analyzer(_bgr):
        return FrameAnalysis(ScreenDetection(next(screens), 1.0), [], [])

    service = make_service(settings, db, analyzer=analyzer)
    service.start()
    assert wait_until(lambda: service.status().frames >= 9)
    service.stop()
    messages = [e.message for e in memory_handler().entries(after_id=last_id) if "Écran" in e.message]
    assert messages == ["Écran détecté : home", "Écran détecté : scout"]
    for handler in logging.getLogger().handlers[:]:
        handler.close()
        logging.getLogger().removeHandler(handler)


def test_api_start_uses_frequency_setting(client):
    client.put("/api/settings", headers=AUTH, json={"app": {"observe_interval_s": 0.7}})
    started = client.post("/api/observer/start", headers=AUTH).json()
    assert started["interval_s"] == 0.7
    client.post("/api/observer/stop", headers=AUTH)


def test_warns_once_when_game_window_is_too_small(settings, db, caplog):
    service = make_service(settings, db)
    with caplog.at_level(logging.WARNING, logger="app.observer_service"):
        for _ in range(3):
            service._check_window_size(np.zeros((450, 800, 3), np.uint8))
        service._check_window_size(np.zeros((744, 1323, 3), np.uint8))  # taille correcte : rien
    warnings = [r for r in caplog.records if "trop petite" in r.getMessage()]
    assert len(warnings) == 1 and "800x450" in warnings[0].getMessage()


def test_last_village_is_rescored_when_priority_changes(settings, db):
    """Mini-fenêtre : changer la priorité recalcule tout de suite le village affiché."""
    service = make_service(settings, db, analyzer=lambda _bgr: scout((1_400_000, 1_400_000, 0)))
    service.start()
    try:
        assert wait_until(lambda: service.status().villages_saved == 1)
    finally:
        service.stop()
    assert service.status().last_village.score == 80  # équilibré : or + élixir au maximum
    service.rescore_last_village(ScoringPreferences(priority=Priority.DARK_ELIXIR))
    village = service.status().last_village
    assert (village.score, village.recommendation) == (20, "à passer")  # pas d'élixir noir
