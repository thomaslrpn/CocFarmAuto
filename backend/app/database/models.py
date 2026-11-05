"""Tables de la base SQLite (SQLAlchemy 2.0, style « Mapped »).

Correspondance avec le cahier des charges (§10), noms en anglais dans le code :
- villages          <- Table Villages (date_analyse, quantite_or, ..., strategie_recommandee)
- analyses          <- Table Analyses (village_id, date_analyse, resultat, confiance_detection)
- daily_statistics  <- Table Statistiques (date, nombre_villages, ressources_analysees, score_moyen)
- settings          <- Table Paramètres (nom, valeur)
- attacks           <- récapitulatifs d'attaque (butin disponible / récupéré), ajoutée en 0.4.0

IMPORTANT : le schéma réel est créé par les MIGRATIONS (migrations.py). Toute
modification ici doit s'accompagner d'une nouvelle migration (un test le vérifie).
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Village(Base):
    __tablename__ = "villages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    gold: Mapped[int] = mapped_column(Integer)
    elixir: Mapped[int] = mapped_column(Integer)
    dark_elixir: Mapped[int] = mapped_column(Integer)
    profitability_score: Mapped[int] = mapped_column(Integer)
    recommendation: Mapped[str] = mapped_column(String)
    recommended_strategy: Mapped[str | None] = mapped_column(String)  # clé de stratégie, None = à passer
    estimated_difficulty: Mapped[float | None] = mapped_column(Float)  # pas encore mesurée
    town_hall_level: Mapped[int | None] = mapped_column(Integer)  # pas encore mesuré
    detection_confidence: Mapped[float] = mapped_column(Float)
    source_image: Mapped[str | None] = mapped_column(String, unique=True)  # évite les doublons à l'import

    analyses: Mapped[list[Analysis]] = relationship(back_populates="village", cascade="all, delete-orphan")


class Analysis(Base):
    """Un calcul de score sur un village, avec le détail complet (JSON) et les préférences utilisées."""

    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    village_id: Mapped[int] = mapped_column(ForeignKey("villages.id", ondelete="CASCADE"), index=True)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime)
    result: Mapped[str] = mapped_column(Text)  # ProfitabilityResult + préférences, en JSON
    detection_confidence: Mapped[float] = mapped_column(Float)
    app_version: Mapped[str] = mapped_column(String)

    village: Mapped[Village] = relationship(back_populates="analyses")


class DailyStatistics(Base):
    """Agrégats par jour, recalculés à partir des villages."""

    __tablename__ = "daily_statistics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    day: Mapped[date] = mapped_column(Date, unique=True)
    villages_count: Mapped[int] = mapped_column(Integer)
    total_gold: Mapped[int] = mapped_column(Integer)
    total_elixir: Mapped[int] = mapped_column(Integer)
    total_dark_elixir: Mapped[int] = mapped_column(Integer)
    average_score: Mapped[float] = mapped_column(Float)


class Setting(Base):
    """Paramètre de l'application (valeur JSON)."""

    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    value: Mapped[str] = mapped_column(Text)


class Attack(Base):
    """Une attaque observée : butin disponible au départ et butin récupéré (None = non lu)."""

    __tablename__ = "attacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    village_id: Mapped[int | None] = mapped_column(ForeignKey("villages.id", ondelete="SET NULL"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime)
    ended_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    available_gold: Mapped[int] = mapped_column(Integer)
    available_elixir: Mapped[int] = mapped_column(Integer)
    available_dark_elixir: Mapped[int] = mapped_column(Integer)
    gained_gold: Mapped[int | None] = mapped_column(Integer)
    gained_elixir: Mapped[int | None] = mapped_column(Integer)
    gained_dark_elixir: Mapped[int | None] = mapped_column(Integer)
    farm_score: Mapped[int | None] = mapped_column(Integer)  # note du farm sur 100 (butin récupéré)
    farm_rating: Mapped[str | None] = mapped_column(String)  # excellent, bon, moyen, faible
