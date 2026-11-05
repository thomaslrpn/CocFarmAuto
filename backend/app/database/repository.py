"""Opérations sur les données : le reste du code passe par ici, jamais par du SQL direct."""
from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analysis.scoring import ScoringPreferences
from app.config import APP_VERSION
from app.database.models import Analysis, DailyStatistics, Setting, Village
from app.strategy.advisor import VillageEvaluation


def find_by_source_image(session: Session, source_image: str) -> Village | None:
    return session.scalars(select(Village).where(Village.source_image == source_image)).first()


def save_evaluation(session: Session, evaluation: VillageEvaluation, prefs: ScoringPreferences) -> Village:
    """Enregistre un village et son analyse. Si l'image est déjà connue, retourne l'existant."""
    sheet, result = evaluation.sheet, evaluation.result
    if sheet.source_image:
        existing = find_by_source_image(session, sheet.source_image)
        if existing is not None:
            return existing
    village = Village(
        analyzed_at=sheet.analyzed_at,
        gold=sheet.loot.gold,
        elixir=sheet.loot.elixir,
        dark_elixir=sheet.loot.dark_elixir,
        profitability_score=result.score,
        recommendation=result.recommendation.value,
        recommended_strategy=evaluation.strategy.key if evaluation.strategy else None,
        estimated_difficulty=sheet.difficulty,
        town_hall_level=sheet.town_hall_level,
        detection_confidence=sheet.detection_confidence,
        source_image=sheet.source_image,
    )
    village.analyses.append(Analysis(
        analyzed_at=sheet.analyzed_at,
        result=json.dumps({"profitability": result.model_dump(mode="json"),
                           "preferences": prefs.model_dump(mode="json")}, ensure_ascii=False),
        detection_confidence=sheet.detection_confidence,
        app_version=APP_VERSION,
    ))
    session.add(village)
    session.flush()  # attribue l'id
    return village


def recent_villages(session: Session, limit: int = 50) -> list[Village]:
    return list(session.scalars(select(Village).order_by(Village.analyzed_at.desc()).limit(limit)))


def count_villages(session: Session) -> int:
    return session.scalar(select(func.count()).select_from(Village)) or 0


def refresh_daily_statistics(session: Session, day: date) -> DailyStatistics | None:
    """Recalcule les statistiques d'un jour à partir des villages (None si aucun village)."""
    start = datetime.combine(day, time.min)
    row = session.execute(
        select(
            func.count(Village.id),
            func.coalesce(func.sum(Village.gold), 0),
            func.coalesce(func.sum(Village.elixir), 0),
            func.coalesce(func.sum(Village.dark_elixir), 0),
            func.avg(Village.profitability_score),
        ).where(Village.analyzed_at >= start, Village.analyzed_at < start + timedelta(days=1))
    ).one()
    stats = session.scalars(select(DailyStatistics).where(DailyStatistics.day == day)).first()
    if row[0] == 0:
        if stats is not None:
            session.delete(stats)
        return None
    if stats is None:
        stats = DailyStatistics(day=day)
        session.add(stats)
    stats.villages_count, stats.total_gold, stats.total_elixir, stats.total_dark_elixir = row[:4]
    stats.average_score = float(row[4])
    return stats


def daily_statistics(session: Session) -> list[DailyStatistics]:
    return list(session.scalars(select(DailyStatistics).order_by(DailyStatistics.day)))


def get_setting(session: Session, name: str, default: Any = None) -> Any:
    setting = session.scalars(select(Setting).where(Setting.name == name)).first()
    return json.loads(setting.value) if setting else default


def set_setting(session: Session, name: str, value: Any) -> None:
    setting = session.scalars(select(Setting).where(Setting.name == name)).first()
    encoded = json.dumps(value, ensure_ascii=False)
    if setting is None:
        session.add(Setting(name=name, value=encoded))
    else:
        setting.value = encoded
