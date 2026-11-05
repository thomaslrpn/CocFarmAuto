"""Journalisation centralisée (cahier des charges §14 : logs structurés).

Chaque événement part vers :
- la console (lisible) ;
- `logs/autofarm.log` : une ligne JSON par événement, rotation à 1 Mo x 5 fichiers ;
- une mémoire des derniers événements, lue par l'API (page Logs du dashboard).

Ajouter des données à un événement : logger.info("...", extra={"duration_ms": 12.5}).
"""
from __future__ import annotations

import json
import logging
import threading
from collections import deque
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from pydantic import BaseModel

LOG_FILE = "autofarm.log"
MEMORY_SIZE = 500
# Attributs standards d'un LogRecord : tout le reste vient de `extra=` et est conservé.
_STANDARD_ATTRS = set(vars(logging.makeLogRecord({}))) | {"message", "asctime"}


class LogEntry(BaseModel):
    id: int  # croissant : permet au dashboard de ne demander que les nouveaux
    time: datetime
    level: str
    category: str  # capture, vision, observer, database, api, ...
    logger: str
    message: str
    data: dict = {}


def _category(logger_name: str) -> str:
    """app.capture.screen -> capture ; app.observer_service -> observer_service."""
    parts = logger_name.split(".")
    return parts[1] if len(parts) > 1 and parts[0] == "app" else parts[0]


def _extra(record: logging.LogRecord) -> dict:
    return {k: v for k, v in vars(record).items() if k not in _STANDARD_ATTRS}


class MemoryLogHandler(logging.Handler):
    """Garde les derniers événements en mémoire (thread-safe)."""

    def __init__(self, capacity: int = MEMORY_SIZE) -> None:
        super().__init__()
        self._entries: deque[LogEntry] = deque(maxlen=capacity)
        self._next_id = 1
        self._lock_entries = threading.Lock()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = record.getMessage()
            if record.exc_info:
                message += f" ({record.exc_info[1]!r})"
            with self._lock_entries:
                self._entries.append(LogEntry(
                    id=self._next_id, time=datetime.fromtimestamp(record.created), level=record.levelname,
                    category=_category(record.name), logger=record.name, message=message,
                    data={k: v for k, v in _extra(record).items() if isinstance(v, (str, int, float, bool))},
                ))
                self._next_id += 1
        except Exception:  # un log ne doit jamais faire planter l'application
            self.handleError(record)

    def entries(self, after_id: int = 0, min_level: int = logging.NOTSET, limit: int = 200) -> list[LogEntry]:
        with self._lock_entries:
            selected = [e for e in self._entries
                        if e.id > after_id and logging.getLevelName(e.level) >= min_level]
        return selected[-limit:]


class JsonLineFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "time": datetime.fromtimestamp(record.created).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            **{k: v for k, v in _extra(record).items() if isinstance(v, (str, int, float, bool, type(None)))},
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


_memory_handler = MemoryLogHandler()


def memory_handler() -> MemoryLogHandler:
    return _memory_handler


def configure_logging(logs_dir: Path | None, level: int = logging.INFO, console_level: int = logging.INFO) -> None:
    """À appeler une fois au démarrage (API ou commande). Ré-appel sans effet de doublon."""
    root = logging.getLogger()
    root.setLevel(min(level, console_level))
    for handler in list(root.handlers):  # évite les doublons si appelé deux fois
        root.removeHandler(handler)

    console = logging.StreamHandler()
    console.setLevel(console_level)
    console.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s", "%H:%M:%S"))
    root.addHandler(console)

    _memory_handler.setLevel(level)
    root.addHandler(_memory_handler)

    if logs_dir is not None:
        logs_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(logs_dir / LOG_FILE, maxBytes=1_000_000, backupCount=5, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(JsonLineFormatter())
        root.addHandler(file_handler)

    # Bibliothèques trop bavardes au niveau INFO
    for noisy in ("uvicorn.access", "httpx", "PIL"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
