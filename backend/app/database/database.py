"""Connexion à la base SQLite de l'utilisateur.

Usage :
    db = Database.open(settings.database_path, settings.backups_dir)
    with db.session() as session:
        ...  # validé (commit) à la fin du bloc, annulé (rollback) en cas d'erreur
"""
from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.database.migrations import migrate

logger = logging.getLogger(__name__)


def _configure_sqlite(dbapi_connection, _record) -> None:  # type: ignore[no-untyped-def]
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")  # SQLite ne vérifie pas les clés étrangères par défaut
    cursor.execute("PRAGMA journal_mode = WAL")  # lectures possibles pendant une écriture (API + observation)
    cursor.close()


class Database:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self._sessions = sessionmaker(bind=engine, expire_on_commit=False)

    @classmethod
    def open(cls, db_path: Path, backups_dir: Path) -> "Database":
        """Applique les migrations manquantes puis ouvre la base."""
        applied = migrate(db_path, backups_dir)
        if applied:
            logger.info("%d migration(s) appliquée(s) sur %s", applied, db_path)
        engine = create_engine(f"sqlite:///{db_path.as_posix()}")
        event.listen(engine, "connect", _configure_sqlite)
        return cls(engine)

    @contextmanager
    def session(self) -> Iterator[Session]:
        session = self._sessions()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self) -> None:
        self.engine.dispose()
