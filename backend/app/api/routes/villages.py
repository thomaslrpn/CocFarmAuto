"""Villages : historique filtrable, fiche détaillée, capture."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analysis.profitability import ProfitabilityResult
from app.analysis.relative import RelativeRanker
from app.analysis.scoring import ScoringPreferences
from app.api.deps import AppContext, get_context, get_session, get_user_settings
from app.api.schemas import VillageDetail, VillagePage, VillageSummary
from app.database.models import Village
from app.database.repository import loot_rows
from app.strategy.strategies import strategy_label
from app.user_settings import UserSettings

router = APIRouter(prefix="/villages", tags=["villages"])

NO_STRATEGY = "none"  # filtre « villages à passer »


def _image_path(context: AppContext, village: Village) -> Path | None:
    """Chemin de la capture, uniquement si c'est un simple nom de fichier PNG présent."""
    name = village.source_image
    if not name or Path(name).name != name or not name.endswith(".png"):  # pas de « ../ »
        return None
    path = context.settings.observations_dir / name
    return path if path.is_file() else None


def _summary(village: Village, prefs: ScoringPreferences, ranker: RelativeRanker,
             context: AppContext) -> VillageSummary:
    value = prefs.loot_value(village.gold, village.elixir, village.dark_elixir)
    return VillageSummary(
        id=village.id,
        analyzed_at=village.analyzed_at,
        gold=village.gold,
        elixir=village.elixir,
        dark_elixir=village.dark_elixir,
        profitability_score=village.profitability_score,
        recommendation=village.recommendation,
        recommended_strategy=village.recommended_strategy,
        recommended_strategy_label=strategy_label(village.recommended_strategy),
        detection_confidence=village.detection_confidence,
        loot_value=round(value, 1),
        relative_rank=ranker.percentile(value),
        has_image=_image_path(context, village) is not None,
    )


def _ranker(session: Session, prefs: ScoringPreferences) -> RelativeRanker:
    return RelativeRanker([prefs.loot_value(*row) for row in loot_rows(session)])


@router.get("", response_model=VillagePage, summary="Historique des villages")
def list_villages(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    min_score: int | None = Query(None, ge=0, le=100),
    strategy: str | None = Query(None, description=f"clé de stratégie, ou '{NO_STRATEGY}' (à passer)"),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    sort: Literal["date", "score", "value"] = "date",
    session: Session = Depends(get_session),
    user: UserSettings = Depends(get_user_settings),
    context: AppContext = Depends(get_context),
) -> VillagePage:
    query = select(Village)
    if min_score is not None:
        query = query.where(Village.profitability_score >= min_score)
    if strategy == NO_STRATEGY:
        query = query.where(Village.recommended_strategy.is_(None))
    elif strategy:
        query = query.where(Village.recommended_strategy == strategy)
    if date_from:
        query = query.where(Village.analyzed_at >= date_from)
    if date_to:
        query = query.where(Village.analyzed_at <= date_to)

    prefs = user.preferences
    ranker = _ranker(session, prefs)
    # Volume personnel (quelques milliers de villages) : tri et pagination en Python,
    # ce qui permet de trier aussi par valeur non plafonnée (calculée, pas stockée).
    items = [_summary(v, prefs, ranker, context) for v in session.scalars(query)]
    sort_key = {"date": lambda s: s.analyzed_at, "score": lambda s: (s.profitability_score, s.loot_value),
                "value": lambda s: s.loot_value}[sort]
    items.sort(key=sort_key, reverse=True)
    return VillagePage(total=len(items), limit=limit, offset=offset, items=items[offset: offset + limit])


def _get_village(session: Session, village_id: int) -> Village:
    village = session.get(Village, village_id)
    if village is None:
        raise HTTPException(404, f"Village {village_id} introuvable")
    return village


@router.get("/{village_id}", response_model=VillageDetail, summary="Fiche détaillée d'un village")
def get_village(
    village_id: int,
    session: Session = Depends(get_session),
    user: UserSettings = Depends(get_user_settings),
    context: AppContext = Depends(get_context),
) -> VillageDetail:
    village = _get_village(session, village_id)
    summary = _summary(village, user.preferences, _ranker(session, user.preferences), context)
    latest = max(village.analyses, key=lambda a: a.analyzed_at, default=None)
    result, prefs_used = None, None
    if latest is not None:
        stored = json.loads(latest.result)
        result = ProfitabilityResult.model_validate(stored["profitability"])
        prefs_used = ScoringPreferences.model_validate(stored["preferences"])
    return VillageDetail(
        **summary.model_dump(),
        town_hall_level=village.town_hall_level,
        estimated_difficulty=village.estimated_difficulty,
        explanation=result.explain() if result else [],
        factors=result.factors if result else [],
        warnings=result.warnings if result else [],
        preferences_used=prefs_used,
        image_url=f"/api/villages/{village.id}/image" if summary.has_image else None,
    )


@router.get("/{village_id}/image", summary="Capture du village (PNG)",
            response_class=FileResponse, responses={200: {"content": {"image/png": {}}}})
def get_village_image(
    village_id: int,
    session: Session = Depends(get_session),
    context: AppContext = Depends(get_context),
) -> FileResponse:
    path = _image_path(context, _get_village(session, village_id))
    if path is None:
        raise HTTPException(404, "Capture introuvable")
    return FileResponse(path, media_type="image/png")
