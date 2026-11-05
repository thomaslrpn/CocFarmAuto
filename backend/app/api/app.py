"""Construction de l'application FastAPI.

`create_app` reçoit un contexte déjà prêt (base ouverte, jeton...) : les tests
peuvent ainsi créer une API sur une base temporaire.
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.deps import AppContext, require_token
from app.api.routes import insights, observer, villages
from app.api.schemas import Health
from app.config import APP_NAME, APP_VERSION

# Origines autorisées : serveur de dev Vite et fenêtre Tauri (le jeton reste exigé).
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "tauri://localhost",
    "http://tauri.localhost",
    "https://tauri.localhost",
]


def create_app(context: AppContext) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        yield
        # Arrêt propre : finir le cycle d'observation en cours, PUIS fermer la base.
        if context.observer is not None:
            context.observer.stop()
        context.db.close()

    app = FastAPI(
        title=f"{APP_NAME} API",
        version=APP_VERSION,
        description="API locale de CoC AutoFarm (outil d'analyse, aucune action sur le jeu).",
        lifespan=lifespan,
    )
    app.state.context = context
    app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS,
                       allow_methods=["GET", "PUT", "POST"], allow_headers=["Authorization", "Content-Type"])

    @app.get("/api/health", response_model=Health, tags=["moteur"], summary="Le backend répond-il ? (sans jeton)")
    def health() -> Health:
        return Health(status="ok")

    protected = APIRouter(prefix="/api", dependencies=[Depends(require_token)])
    protected.include_router(insights.router)
    protected.include_router(villages.router)
    protected.include_router(observer.router)
    app.include_router(protected)
    return app
