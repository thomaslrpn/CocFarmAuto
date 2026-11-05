"""Import des observations (fichiers JSON du mode observation) dans la base.

Ré-exécutable sans risque : un village déjà importé (même image) est ignoré.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.analysis.scoring import ScoringPreferences
from app.database.database import Database
from app.database.repository import find_by_source_image, refresh_daily_statistics, save_evaluation
from app.observer import load_observations
from app.strategy.advisor import evaluate_village


@dataclass
class ImportReport:
    found: int = 0
    imported: int = 0
    already_present: int = 0


def import_observations(db: Database, directory: Path, prefs: ScoringPreferences) -> ImportReport:
    sheets = load_observations(directory)
    report = ImportReport(found=len(sheets))
    days = set()
    with db.session() as session:
        for sheet in sheets:
            if sheet.source_image and find_by_source_image(session, sheet.source_image):
                report.already_present += 1
                continue
            save_evaluation(session, evaluate_village(sheet, prefs), prefs)
            report.imported += 1
            days.add(sheet.analyzed_at.date())
        for day in days:
            refresh_daily_statistics(session, day)
    return report
