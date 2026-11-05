"""Tests de la base SQLite : migrations, sauvegardes, enregistrement, import."""
import sqlite3
from datetime import date, datetime

import numpy as np
import pytest
from sqlalchemy import inspect

import app.database.migrations as migrations
from app.analysis.scoring import ScoringPreferences
from app.analysis.village_analysis import Loot, build_sheet
from app.database.database import Database
from app.database.importer import import_observations
from app.database.migrations import LATEST_VERSION, MAX_BACKUPS, MigrationError, backup_database, migrate
from app.database.models import Base, Village
from app.database.repository import (
    count_villages,
    daily_statistics,
    get_setting,
    recent_villages,
    refresh_daily_statistics,
    save_evaluation,
    set_setting,
)
from app.observer import ScoutRecorder
from app.strategy.advisor import evaluate_village, recommend_strategy
from app.vision.frame import FrameAnalysis
from app.vision.models import Box, ElementType
from app.vision.resources import ResourceReading
from app.vision.screen_state import GameScreen, ScreenDetection

PREFS = ScoringPreferences()


@pytest.fixture
def db(tmp_path):
    database = Database.open(tmp_path / "test.db", tmp_path / "backups")
    yield database
    database.close()


def sheet(gold, elixir, dark, when=datetime(2026, 11, 5, 10, 0), image=None):
    return build_sheet(Loot(gold=gold, elixir=elixir, dark_elixir=dark), 0.9, when, image)


def version_of(path) -> int:
    with sqlite3.connect(path) as conn:
        return conn.execute("PRAGMA user_version").fetchone()[0]


# --- Migrations ---------------------------------------------------------------


def test_migrate_new_database_then_nothing_to_do(tmp_path):
    path = tmp_path / "a.db"
    assert migrate(path, tmp_path / "bk") == LATEST_VERSION
    assert version_of(path) == LATEST_VERSION
    assert migrate(path, tmp_path / "bk") == 0
    assert not (tmp_path / "bk").exists()  # base neuve : pas de sauvegarde inutile


def test_orm_models_match_migrated_schema(db):
    """Garde-fou : modifier models.py sans écrire de migration fait échouer ce test."""
    inspector = inspect(db.engine)
    for table in Base.metadata.sorted_tables:
        db_cols = {c["name"]: c for c in inspector.get_columns(table.name)}
        assert set(db_cols) == {c.name for c in table.columns}, table.name
        for column in table.columns:
            if not column.primary_key:  # SQLite déclare « nullable » les INTEGER PRIMARY KEY
                assert db_cols[column.name]["nullable"] == column.nullable, f"{table.name}.{column.name}"


def test_existing_database_is_backed_up_before_migration(tmp_path):
    path = tmp_path / "old.db"
    with sqlite3.connect(path) as conn:  # base « version 0 » contenant déjà des données
        conn.execute("CREATE TABLE legacy (x INTEGER)")
    migrate(path, tmp_path / "bk")
    backups = list((tmp_path / "bk").glob("old_*_v0.db"))
    assert len(backups) == 1


def test_newer_database_is_refused(tmp_path):
    path = tmp_path / "future.db"
    with sqlite3.connect(path) as conn:
        conn.execute(f"PRAGMA user_version = {LATEST_VERSION + 1}")
    with pytest.raises(MigrationError, match="plus récente"):
        migrate(path, tmp_path / "bk")


def test_failed_migration_is_rolled_back(tmp_path, monkeypatch):
    path = tmp_path / "a.db"
    migrate(path, tmp_path / "bk")
    bad = "CREATE TABLE extra (x INTEGER); INSERT INTO table_inexistante VALUES (1)"
    monkeypatch.setattr(migrations, "MIGRATIONS", migrations.MIGRATIONS + (bad,))
    monkeypatch.setattr(migrations, "LATEST_VERSION", LATEST_VERSION + 1)
    with pytest.raises(MigrationError):
        migrate(path, tmp_path / "bk")
    assert version_of(path) == LATEST_VERSION
    with sqlite3.connect(path) as conn:  # la table « extra » n'a pas survécu
        assert not conn.execute("SELECT name FROM sqlite_master WHERE name='extra'").fetchall()


def test_backup_rotation(tmp_path):
    path = tmp_path / "a.db"
    migrate(path, tmp_path / "bk")
    for i in range(MAX_BACKUPS + 3):
        backup_database(path, tmp_path / "bk", f"t{i}")
    assert len(list((tmp_path / "bk").glob("*.db"))) == MAX_BACKUPS


# --- Enregistrement -----------------------------------------------------------


def test_save_evaluation_with_analysis(db):
    evaluation = evaluate_village(sheet(600_000, 600_000, 10_000, image="a.png"), PREFS)
    with db.session() as session:
        village = save_evaluation(session, evaluation, PREFS)
        assert village.id is not None and village.profitability_score == 100
        assert village.recommended_strategy is not None
        assert len(village.analyses) == 1 and '"score": 100' in village.analyses[0].result
        assert village.estimated_difficulty is None  # jamais inventée


def test_same_image_is_not_saved_twice(db):
    evaluation = evaluate_village(sheet(1, 1, 1, image="a.png"), PREFS)
    with db.session() as session:
        first = save_evaluation(session, evaluation, PREFS)
        second = save_evaluation(session, evaluation, PREFS)
        assert first.id == second.id and count_villages(session) == 1


def test_deleting_village_deletes_its_analyses(db):
    with db.session() as session:
        save_evaluation(session, evaluate_village(sheet(1, 1, 1), PREFS), PREFS)
    with db.session() as session:
        session.delete(recent_villages(session)[0])
    with sqlite3.connect(db.engine.url.database) as conn:
        assert conn.execute("SELECT COUNT(*) FROM analyses").fetchone()[0] == 0


def test_daily_statistics(db):
    day = date(2026, 11, 5)
    with db.session() as session:
        for gold in (100_000, 300_000):
            save_evaluation(session, evaluate_village(sheet(gold, 0, 0), PREFS), PREFS)
        save_evaluation(session, evaluate_village(sheet(999, 0, 0, datetime(2026, 11, 6, 9)), PREFS), PREFS)
        stats = refresh_daily_statistics(session, day)
        assert stats.villages_count == 2 and stats.total_gold == 400_000
        assert refresh_daily_statistics(session, date(2026, 1, 1)) is None
    with db.session() as session:
        assert [s.day for s in daily_statistics(session)] == [day]


def test_settings_roundtrip(db):
    with db.session() as session:
        assert get_setting(session, "theme", "dark") == "dark"
        set_setting(session, "seuil", {"min": 70})
        set_setting(session, "seuil", {"min": 75})
    with db.session() as session:
        assert get_setting(session, "seuil") == {"min": 75}


def test_session_rolls_back_on_error(db):
    with pytest.raises(RuntimeError):
        with db.session() as session:
            session.add(Village(analyzed_at=datetime.now(), gold=1, elixir=1, dark_elixir=1,
                                profitability_score=1, recommendation="x", detection_confidence=1))
            raise RuntimeError("boom")
    with db.session() as session:
        assert count_villages(session) == 0


# --- Stratégie recommandée et import -----------------------------------------


def test_recommend_strategy():
    # Priorité or : 60 + 12.5 + 7.5 = 80 pts (>= 70) ; équilibré : 70 ; élixir : 62.5
    assert recommend_strategy(sheet(900_000, 300_000, 5_000), PREFS).key == "gold"
    assert recommend_strategy(sheet(10_000, 10_000, 100), PREFS) is None  # village à passer


def test_import_observations_is_idempotent(db, tmp_path):
    obs_dir = tmp_path / "observations"
    recorder = ScoutRecorder(obs_dir, stable_frames=1)
    for loot in ((400_000, 500_000, 6_000), (100_000, 90_000, 800)):
        readings = [ResourceReading(r, Box(0, 0, 1, 1), [], v, 0.9)
                    for r, v in zip((ElementType.GOLD, ElementType.ELIXIR, ElementType.DARK_ELIXIR), loot)]
        recorder.process(np.zeros((4, 4, 3), np.uint8),
                         FrameAnalysis(ScreenDetection(GameScreen.SCOUT, 1.0), [], readings))

    first = import_observations(db, obs_dir, PREFS)
    second = import_observations(db, obs_dir, PREFS)
    assert (first.found, first.imported) == (2, 2)
    assert (second.imported, second.already_present) == (0, 2)
    with db.session() as session:
        assert count_villages(session) == 2 and len(daily_statistics(session)) == 1


def test_v2_database_with_attacks_gets_farm_score_columns(tmp_path, monkeypatch):
    """Base créée par la 1.0.0 de test (schéma v2, attaques sans note) : la migration 3 la complète."""
    path = tmp_path / "v2.db"
    monkeypatch.setattr(migrations, "MIGRATIONS", migrations.MIGRATIONS[:2])
    monkeypatch.setattr(migrations, "LATEST_VERSION", 2)
    migrate(path, tmp_path / "bk")
    with sqlite3.connect(path) as conn:
        conn.execute("INSERT INTO attacks (started_at, ended_at, available_gold, available_elixir, "
                     "available_dark_elixir, gained_gold) VALUES ('2026-11-05', '2026-11-05', 1, 2, 3, 1)")
    monkeypatch.undo()
    migrate(path, tmp_path / "bk")
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT gained_gold, farm_score, farm_rating FROM attacks").fetchone() == (1, None, None)
    assert version_of(path) == LATEST_VERSION
