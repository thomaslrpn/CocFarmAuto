"""Tests de l'API (FastAPI TestClient, base temporaire)."""
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.analysis.relative import RelativeRanker
from app.analysis.scoring import ScoringPreferences
from app.analysis.village_analysis import Loot, build_sheet
from app.api.app import create_app
from app.api.deps import AppContext
from app.config import Settings
from app.database.database import Database
from app.database.repository import refresh_daily_statistics, save_evaluation
from app.strategy.advisor import evaluate_village

TOKEN = "jeton-de-test"
AUTH = {"Authorization": f"Bearer {TOKEN}"}
PREFS = ScoringPreferences()


def _settings(tmp_path) -> Settings:
    return Settings(
        data_dir=tmp_path, screenshots_dir=tmp_path / "screenshots", observations_dir=tmp_path / "observations",
        database_path=tmp_path / "test.db", backups_dir=tmp_path / "backups", logs_dir=tmp_path / "logs",
    )


@pytest.fixture
def ctx(tmp_path):
    settings = _settings(tmp_path)
    db = Database.open(settings.database_path, settings.backups_dir)
    yield AppContext(settings=settings, db=db, token=TOKEN, vision_ready=True)
    db.close()


@pytest.fixture
def client(ctx):
    with TestClient(create_app(ctx)) as c:
        yield c


def add_village(ctx, gold, elixir, dark, minute=0, image=None):
    sheet = build_sheet(Loot(gold=gold, elixir=elixir, dark_elixir=dark), 0.9,
                        datetime(2026, 11, 5, 10, minute), image)
    with ctx.db.session() as session:
        village = save_evaluation(session, evaluate_village(sheet, PREFS), PREFS)
        refresh_daily_statistics(session, sheet.analyzed_at.date())
        return village.id


# --- Score relatif -------------------------------------------------------------


def test_relative_ranker():
    ranker = RelativeRanker([10, 20, 30, 40, 50])
    assert ranker.percentile(50) == 100.0  # meilleur que les 4 autres
    assert ranker.percentile(10) == 0.0
    assert ranker.percentile(30) == 50.0
    assert RelativeRanker([42]).percentile(42) is None  # rien à comparer


def test_loot_value_is_not_capped():
    assert PREFS.loot_value(600_000, 600_000, 10_000) == pytest.approx(100)
    assert PREFS.loot_value(1_200_000, 1_200_000, 20_000) == pytest.approx(200)


# --- Sécurité ------------------------------------------------------------------


def test_health_is_public(client):
    assert client.get("/api/health").json() == {"status": "ok"}


@pytest.mark.parametrize("url", ["/api/status", "/api/villages", "/api/statistics", "/api/settings"])
def test_token_required(client, url):
    assert client.get(url).status_code == 401
    assert client.get(url, headers={"Authorization": "Bearer mauvais"}).status_code == 401
    assert client.get(url, headers=AUTH).status_code == 200


def test_token_accepted_in_query(client):
    assert client.get(f"/api/status?token={TOKEN}").status_code == 200


# --- Routes --------------------------------------------------------------------


def test_status(client):
    body = client.get("/api/status", headers=AUTH).json()
    assert body["villages_count"] == 0 and body["vision_ready"] is True
    assert body["game_window"] in {"found", "not_found", "unsupported"}


def test_villages_list_filters_and_relative_rank(client, ctx):
    add_village(ctx, 600_000, 600_000, 10_000, minute=1)  # 100/100, valeur 100
    add_village(ctx, 1_200_000, 1_200_000, 20_000, minute=2)  # 100/100, valeur 200 : départagé
    add_village(ctx, 30_000, 30_000, 500, minute=3)  # à passer

    page = client.get("/api/villages?sort=value", headers=AUTH).json()
    assert page["total"] == 3
    best, second = page["items"][0], page["items"][1]
    assert best["profitability_score"] == second["profitability_score"] == 100
    assert best["relative_rank"] == 100.0 and second["relative_rank"] == 50.0

    assert client.get("/api/villages?min_score=90", headers=AUTH).json()["total"] == 2
    assert client.get("/api/villages?strategy=none", headers=AUTH).json()["total"] == 1
    paged = client.get("/api/villages?limit=1&offset=1&sort=date", headers=AUTH).json()
    assert len(paged["items"]) == 1 and paged["items"][0]["analyzed_at"].endswith("10:02:00")


def test_village_detail_and_404(client, ctx):
    village_id = add_village(ctx, 300_000, 300_000, 5_000)
    body = client.get(f"/api/villages/{village_id}", headers=AUTH).json()
    assert body["profitability_score"] == 50
    assert any("Or" in line for line in body["explanation"])
    assert body["preferences_used"]["priority"] == "balanced"
    assert body["image_url"] is None and body["has_image"] is False
    assert client.get("/api/villages/999", headers=AUTH).status_code == 404


def test_village_image(client, ctx):
    ctx.settings.observations_dir.mkdir(parents=True)
    Image.new("RGB", (4, 4), "red").save(ctx.settings.observations_dir / "scout_x.png")
    with_image = add_village(ctx, 1, 1, 1, image="scout_x.png")
    traversal = add_village(ctx, 1, 1, 1, minute=5, image="../test.db")

    detail = client.get(f"/api/villages/{with_image}", headers=AUTH).json()
    response = client.get(f"{detail['image_url']}?token={TOKEN}")
    assert response.status_code == 200 and response.headers["content-type"] == "image/png"
    assert client.get(f"/api/villages/{traversal}/image", headers=AUTH).status_code == 404


def test_statistics(client, ctx):
    add_village(ctx, 100_000, 200_000, 1_000)
    add_village(ctx, 300_000, 400_000, 3_000, minute=1)
    body = client.get("/api/statistics", headers=AUTH).json()
    assert body["villages_count"] == 2 and body["total_gold"] == 400_000
    assert len(body["days"]) == 1 and body["days"][0]["villages_count"] == 2


def test_strategy_comparison(client, ctx):
    assert client.get("/api/strategies/compare", headers=AUTH).json()["results"] == []
    for minute, loot in enumerate([(900_000, 300_000, 5_000), (50_000, 40_000, 300), (600_000, 700_000, 9_000)]):
        add_village(ctx, *loot, minute=minute)
    body = client.get("/api/strategies/compare", headers=AUTH).json()
    assert body["villages_count"] == 3 and len(body["results"]) == 5
    assert "skip_rate" in body["results"][0]
    assert body["army_cost_configured"] is False
    assert any(line.startswith("[supposé]") for line in body["assumptions"])


def put_settings(client, body):
    return client.put("/api/settings", headers=AUTH, json=body)


def test_settings_partial_update(client):
    assert client.get("/api/settings", headers=AUTH).json()["preferences"]["priority"] == "balanced"
    put_settings(client, {"preferences": {"army_cost": {"gold": 50_000, "elixir": 1}}})
    updated = put_settings(client, {"preferences": {"priority": "gold", "army_cost": {"elixir": 250_000}}}).json()
    prefs = updated["preferences"]
    assert prefs["priority"] == "gold"
    assert prefs["army_cost"] == {"gold": 50_000, "elixir": 250_000, "dark_elixir": 0}  # or conservé
    assert prefs["target_loot"]["gold"] == 600_000  # non envoyé : inchangé
    assert updated["simulation"]["search_cost_gold"] == 1500
    assert client.get("/api/settings", headers=AUTH).json() == updated  # bien enregistré


def test_settings_validation_errors(client):
    incoherent = put_settings(client, {"preferences": {"very_good_threshold": 10}})
    assert incoherent.status_code == 422
    typo = put_settings(client, {"preferences": {"priorty": "gold"}})
    assert typo.status_code == 422 and "priorty" in typo.text
    nested_typo = put_settings(client, {"simulation": {"capture_rates": {"or": 0.5}}})
    assert nested_typo.status_code == 422
    assert put_settings(client, {"preferences": {"priority": "diamant"}}).status_code == 422
    # Rien n'a été modifié par les requêtes refusées
    assert client.get("/api/settings", headers=AUTH).json()["preferences"]["priority"] == "balanced"


def test_settings_docs_show_example(client):
    schema = client.get("/openapi.json").json()["components"]["schemas"]["UserSettingsUpdate"]
    assert schema["examples"][0] == {"preferences": {"priority": "gold"}}
