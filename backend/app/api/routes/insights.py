"""État du moteur, statistiques, comparaison des stratégies, réglages."""
from __future__ import annotations

import sqlite3
from typing import Any, TypeVar

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analysis.village_analysis import Resource
from app.api.deps import AppContext, get_context, get_session, get_user_settings
from app.api.schemas import (
    DayStatistics,
    StatisticsOverview,
    Status,
    StrategyComparison,
    UserSettingsModel,
    UserSettingsUpdate,
)
from app.capture.window import WindowNotSupportedError, find_window
from app.config import APP_NAME, APP_VERSION
from app.database.migrations import backup_database
from app.database.models import Village
from app.database.repository import count_villages, daily_statistics, village_to_sheet
from app.strategy.simulator import compare_strategies
from app.strategy.strategies import DEFAULT_STRATEGIES
from app.user_settings import UserSettings, save_user_settings

router = APIRouter()
ModelT = TypeVar("ModelT", bound=BaseModel)


def _game_window_state(title: str) -> str:
    try:
        return "found" if find_window(title) else "not_found"
    except WindowNotSupportedError:
        return "unsupported"


@router.get("/status", response_model=Status, tags=["moteur"], summary="État du moteur")
def get_status(session: Session = Depends(get_session), context: AppContext = Depends(get_context)) -> Status:
    s = context.settings
    return Status(
        app=APP_NAME,
        version=APP_VERSION,
        data_dir=str(s.data_dir),
        database=str(s.database_path),
        villages_count=count_villages(session),
        vision_ready=context.vision_ready,
        game_window=_game_window_state(s.game_window_title),
    )


@router.get("/statistics", response_model=StatisticsOverview, tags=["statistiques"],
            summary="Totaux et statistiques par jour")
def get_statistics(session: Session = Depends(get_session)) -> StatisticsOverview:
    count, gold, elixir, dark, avg = session.execute(select(
        func.count(Village.id),
        func.coalesce(func.sum(Village.gold), 0),
        func.coalesce(func.sum(Village.elixir), 0),
        func.coalesce(func.sum(Village.dark_elixir), 0),
        func.avg(Village.profitability_score),
    )).one()
    return StatisticsOverview(
        villages_count=count, total_gold=gold, total_elixir=elixir, total_dark_elixir=dark,
        average_score=round(avg, 1) if avg is not None else None,
        days=[DayStatistics.model_validate(d, from_attributes=True) for d in daily_statistics(session)],
    )


@router.get("/strategies/compare", response_model=StrategyComparison, tags=["stratégies"],
            summary="Simulation théorique des stratégies sur les villages enregistrés")
def compare(session: Session = Depends(get_session),
            user: UserSettings = Depends(get_user_settings)) -> StrategyComparison:
    sheets = [village_to_sheet(v) for v in session.scalars(select(Village))]
    prefs, assumptions = user.preferences, user.simulation
    results, search_time = (compare_strategies(DEFAULT_STRATEGIES, sheets, prefs, assumptions)
                            if sheets else ([], assumptions.search_time_s or 0.0))
    return StrategyComparison(
        villages_count=len(sheets),
        search_time_s=search_time,
        assumptions=assumptions.describe(search_time),
        army_cost_configured=any(prefs.army_cost.get(r) for r in Resource),
        results=results,
    )


@router.get("/settings", response_model=UserSettingsModel, tags=["paramètres"], summary="Réglages actuels")
def get_settings(user: UserSettings = Depends(get_user_settings)) -> UserSettingsModel:
    return UserSettingsModel(preferences=user.preferences, simulation=user.simulation, app=user.app)


def _deep_merge(current: dict[str, Any], changes: dict[str, Any], path: tuple[str, ...]) -> dict[str, Any]:
    """Fusionne `changes` dans `current`, y compris dans les sous-objets.

    Un champ inconnu (faute de frappe : « priorty ») est refusé plutôt qu'ignoré.
    """
    merged = dict(current)
    for key, value in changes.items():
        if key not in current:
            raise RequestValidationError([{
                "type": "extra_forbidden", "loc": ("body", *path, key),
                "msg": f"Champ inconnu : '{key}'", "input": value,
            }])
        if isinstance(value, dict) and isinstance(current[key], dict):
            merged[key] = _deep_merge(current[key], value, (*path, key))
        else:
            merged[key] = value
    return merged


def _apply(model: ModelT, changes: dict[str, Any] | None, section: str) -> ModelT:
    """Applique des modifications partielles puis REVALIDE l'ensemble (422 si incohérent)."""
    if not changes:
        return model
    merged = _deep_merge(model.model_dump(mode="json"), changes, (section,))
    try:
        return type(model).model_validate(merged)
    except ValidationError as exc:
        errors = [{**e, "loc": ("body", section, *e["loc"])} for e in exc.errors(include_url=False)]
        raise RequestValidationError(errors) from exc


@router.put("/settings", response_model=UserSettingsModel, tags=["paramètres"],
            summary="Modifier les réglages (seuls les champs envoyés changent)")
def update_settings(
    update: UserSettingsUpdate,
    session: Session = Depends(get_session),
    user: UserSettings = Depends(get_user_settings),
) -> UserSettingsModel:
    new = UserSettings(
        preferences=_apply(user.preferences, update.preferences, "preferences"),
        simulation=_apply(user.simulation, update.simulation, "simulation"),
        app=_apply(user.app, update.app, "app"),
    )
    save_user_settings(session, new)
    return UserSettingsModel(preferences=new.preferences, simulation=new.simulation, app=new.app)


@router.post("/shutdown", tags=["moteur"], status_code=202,
             summary="Arrêter proprement le moteur (utilisé par l'application de bureau)")
def shutdown(background: BackgroundTasks, context: AppContext = Depends(get_context)) -> dict[str, str]:
    if context.request_shutdown is None:
        raise HTTPException(409, "Arrêt à distance indisponible pour ce moteur")
    # Après l'envoi de la réponse : l'appelant reçoit sa confirmation avant l'arrêt.
    background.add_task(context.request_shutdown)
    return {"status": "stopping"}


@router.post("/database/backup", tags=["moteur"],
             summary="Sauvegarder la base (fait automatiquement avant une mise à jour)")
def backup(
    label: str = Query("manuel", pattern=r"^[A-Za-z0-9._-]{1,40}$",
                       description="Suffixe du fichier de sauvegarde, ex. avant-maj-0.2.0"),
    context: AppContext = Depends(get_context),
) -> dict[str, str]:
    s = context.settings
    try:
        path = backup_database(s.database_path, s.backups_dir, label)
    except (OSError, sqlite3.Error) as exc:
        raise HTTPException(500, f"Sauvegarde impossible : {exc}") from exc
    return {"path": str(path)}
