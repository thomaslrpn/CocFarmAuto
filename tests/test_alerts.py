"""Alertes : son et notification selon la recommandation et les réglages."""
import json
from datetime import datetime

import pytest

from app.alerts import EVENT_PREFIX, AlertService, emit_event
from app.database.database import Database
from app.observer_service import ObservedVillage
from app.user_settings import AppPreferences, load_user_settings, save_user_settings


def village(recommendation: str, score: int = 90) -> ObservedVillage:
    return ObservedVillage(village_id=7, analyzed_at=datetime(2026, 11, 5, 15, 0), gold=650_000, elixir=720_000,
                           dark_elixir=5_000, score=score, recommendation=recommendation, strategy="Farm or")


@pytest.fixture
def db(tmp_path):
    database = Database.open(tmp_path / "test.db", tmp_path / "backups")
    yield database
    database.close()


def make_service(db, tmp_path, **app_prefs):
    with db.session() as session:
        current = load_user_settings(session, tmp_path)
        save_user_settings(session, type(current)(current.preferences, current.simulation,
                                                  AppPreferences(**app_prefs)))
    calls: list[str] = []
    events: list[dict] = []
    service = AlertService(db, tmp_path, play_sound=lambda: calls.append("son"), emit=events.append)
    return service, calls, events


def test_sound_only_by_default_for_very_interesting_village(db, tmp_path):
    service, sounds, events = make_service(db, tmp_path)
    service.on_village(village("très intéressant"))
    assert sounds == ["son"] and events == []  # pas de notification Windows par défaut


def test_notification_when_enabled(db, tmp_path):
    service, _sounds, events = make_service(db, tmp_path, alert_notification=True)
    service.on_village(village("très intéressant"))
    assert events[0]["type"] == "village_alert" and events[0]["score"] == 90 and events[0]["gold"] == 650_000


def test_no_alert_below_threshold(db, tmp_path):
    service, sounds, events = make_service(db, tmp_path)
    service.on_village(village("intéressant", 70))
    assert sounds == [] and events == []


def test_interesting_level_and_channels(db, tmp_path):
    service, sounds, events = make_service(db, tmp_path, alert_level="interesting", alert_sound=False,
                                                alert_notification=True)
    service.on_village(village("intéressant", 70))
    assert sounds == [] and len(events) == 1  # notification seule


def test_alerts_off(db, tmp_path):
    service, sounds, events = make_service(db, tmp_path, alert_level="off")
    service.on_village(village("très intéressant"))
    assert sounds == [] and events == []


def test_failing_sound_never_breaks_observation(db, tmp_path):
    def broken_sound():
        raise OSError("pas de carte son")
    service = AlertService(db, tmp_path, play_sound=broken_sound, emit=lambda _e: None)
    service.on_village(village("très intéressant"))  # ne lève pas


def test_event_line_format(capsys):
    emit_event({"type": "village_alert", "score": 91, "recommendation": "très intéressant"})
    line = capsys.readouterr().out.strip()
    assert line.startswith(EVENT_PREFIX)
    assert json.loads(line[len(EVENT_PREFIX):])["recommendation"] == "très intéressant"


def test_test_alert_uses_current_settings(db, tmp_path):
    service, sounds, events = make_service(db, tmp_path, alert_sound=False)
    assert service.test() == {"sound": False, "notification": False}
    assert sounds == [] and events == []


def test_alert_sound_file_is_a_short_valid_wav():
    import wave

    from app.alerts import ALERT_SOUND

    with wave.open(str(ALERT_SOUND)) as wav:
        duration = wav.getnframes() / wav.getframerate()
        assert wav.getnchannels() == 1 and wav.getsampwidth() == 2
    assert 0.3 < duration < 2.0
