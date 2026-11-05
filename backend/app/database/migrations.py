"""Migrations du schéma SQLite.

Principe (volontairement simple, sans Alembic) :
- SQLite stocke un numéro de version dans la base : `PRAGMA user_version`.
- `MIGRATIONS[i]` fait passer la base de la version i à i+1.
- Au démarrage, on applique dans l'ordre les migrations manquantes, chacune dans
  une transaction : en cas d'erreur, la base reste dans l'état précédent.
- Avant de migrer une base EXISTANTE, une copie de sauvegarde est faite.

Règle : on n'édite JAMAIS une migration déjà publiée ; on en ajoute une nouvelle.
"""
from __future__ import annotations

import logging
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

MAX_BACKUPS = 5

_V1_INITIAL_SCHEMA = """
CREATE TABLE villages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analyzed_at DATETIME NOT NULL,
    gold INTEGER NOT NULL,
    elixir INTEGER NOT NULL,
    dark_elixir INTEGER NOT NULL,
    profitability_score INTEGER NOT NULL,
    recommendation VARCHAR NOT NULL,
    recommended_strategy VARCHAR,
    estimated_difficulty FLOAT,
    town_hall_level INTEGER,
    detection_confidence FLOAT NOT NULL,
    source_image VARCHAR UNIQUE
);
CREATE INDEX ix_villages_analyzed_at ON villages (analyzed_at);

CREATE TABLE analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    village_id INTEGER NOT NULL REFERENCES villages (id) ON DELETE CASCADE,
    analyzed_at DATETIME NOT NULL,
    result TEXT NOT NULL,
    detection_confidence FLOAT NOT NULL,
    app_version VARCHAR NOT NULL
);
CREATE INDEX ix_analyses_village_id ON analyses (village_id);

CREATE TABLE daily_statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day DATE NOT NULL UNIQUE,
    villages_count INTEGER NOT NULL,
    total_gold INTEGER NOT NULL,
    total_elixir INTEGER NOT NULL,
    total_dark_elixir INTEGER NOT NULL,
    average_score FLOAT NOT NULL
);

CREATE TABLE settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL UNIQUE,
    value TEXT NOT NULL
);
"""

# Index i : script SQL faisant passer de la version i à la version i+1.
MIGRATIONS: tuple[str, ...] = (_V1_INITIAL_SCHEMA,)
LATEST_VERSION = len(MIGRATIONS)


class MigrationError(RuntimeError):
    """Une migration a échoué : la base est restée dans son état précédent."""


def schema_version(conn: sqlite3.Connection) -> int:
    return int(conn.execute("PRAGMA user_version").fetchone()[0])


def backup_database(db_path: Path, backups_dir: Path, label: str) -> Path:
    """Copie la base dans `backups_dir` et ne garde que les MAX_BACKUPS plus récentes."""
    backups_dir.mkdir(parents=True, exist_ok=True)
    target = backups_dir / f"{db_path.stem}_{datetime.now():%Y%m%d_%H%M%S_%f}_{label}.db"
    shutil.copy2(db_path, target)
    for old in sorted(backups_dir.glob(f"{db_path.stem}_*.db"))[:-MAX_BACKUPS]:
        old.unlink()
    logger.info("Sauvegarde de la base : %s", target)
    return target


def migrate(db_path: Path, backups_dir: Path) -> int:
    """Met la base à jour. Retourne le nombre de migrations appliquées."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    existed = db_path.is_file() and db_path.stat().st_size > 0
    # isolation_level=None : on gère les transactions nous-mêmes (BEGIN / COMMIT).
    conn = sqlite3.connect(db_path, isolation_level=None)
    try:
        current = schema_version(conn)
        if current > LATEST_VERSION:
            raise MigrationError(
                f"Base en version {current}, plus récente que le logiciel (version {LATEST_VERSION}) : "
                "mets à jour CoC AutoFarm."
            )
        if current == LATEST_VERSION:
            return 0
        if existed:
            conn.close()
            backup_database(db_path, backups_dir, f"v{current}")
            conn = sqlite3.connect(db_path, isolation_level=None)
        for version in range(current, LATEST_VERSION):
            try:
                conn.execute("BEGIN")
                for statement in _split_sql(MIGRATIONS[version]):
                    conn.execute(statement)
                conn.execute(f"PRAGMA user_version = {version + 1}")
                conn.execute("COMMIT")
            except sqlite3.Error as exc:
                conn.execute("ROLLBACK")
                raise MigrationError(f"Migration {version} -> {version + 1} échouée : {exc}") from exc
            logger.info("Base migrée en version %d", version + 1)
        return LATEST_VERSION - current
    finally:
        conn.close()


def _split_sql(script: str) -> list[str]:
    """Découpe un script en instructions (conn.executescript ferait un COMMIT implicite)."""
    return [s.strip() for s in script.split(";") if s.strip()]
