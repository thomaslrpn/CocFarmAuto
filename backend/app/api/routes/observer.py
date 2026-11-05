"""Pilotage du mode observation et journal des événements."""
from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.deps import AppContext, get_context, get_user_settings
from app.logging_setup import LogEntry, memory_handler
from app.observer_service import MIN_INTERVAL_S, ObserverError, ObserverService, ObserverStatus
from app.user_settings import UserSettings

router = APIRouter()


class StartRequest(BaseModel):
    interval_s: float | None = Field(
        default=None, ge=MIN_INTERVAL_S, le=60,
        description="secondes entre deux analyses (défaut : réglage « fréquence des analyses »)")


def _observer(context: AppContext) -> ObserverService:
    if context.observer is None:
        raise HTTPException(409, "Observation indisponible : modèles de vision absents")
    return context.observer


@router.get("/observer", response_model=ObserverStatus, tags=["observation"], summary="État de l'observation")
def observer_status(context: AppContext = Depends(get_context)) -> ObserverStatus:
    return context.observer.status() if context.observer else ObserverStatus(running=False)


@router.post("/observer/start", response_model=ObserverStatus, tags=["observation"],
             summary="Démarrer l'observation en tâche de fond (lecture seule)")
def observer_start(
    request: StartRequest | None = None,
    context: AppContext = Depends(get_context),
    user: UserSettings = Depends(get_user_settings),
) -> ObserverStatus:
    interval = request.interval_s if request and request.interval_s is not None else user.app.observe_interval_s
    try:
        return _observer(context).start(interval)
    except ObserverError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/observer/stop", response_model=ObserverStatus, tags=["observation"],
             summary="Arrêter l'observation (le cycle en cours se termine)")
def observer_stop(context: AppContext = Depends(get_context)) -> ObserverStatus:
    return _observer(context).stop()


@router.get("/logs", response_model=list[LogEntry], tags=["moteur"], summary="Derniers événements")
def get_logs(
    after_id: int = Query(0, ge=0, description="ne renvoyer que les événements plus récents que cet id"),
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO",
    limit: int = Query(200, ge=1, le=500),
) -> list[LogEntry]:
    return memory_handler().entries(after_id=after_id, min_level=logging.getLevelName(level), limit=limit)
