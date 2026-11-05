"""Démarre le backend : `python -m app.main [--port 8765] [--parent-pid N]`.

- N'écoute que 127.0.0.1 : inaccessible depuis le réseau.
- Jeton : variable d'environnement COC_AUTOFARM_TOKEN (fournie par l'application
  de bureau), sinon généré au hasard et affiché.
- --parent-pid : PID de l'application de bureau ; le moteur s'arrête s'il disparaît.
- Arrêt propre : Ctrl+C, POST /api/shutdown, ou fin du processus parent.
- Documentation interactive : http://127.0.0.1:<port>/docs (bouton « Authorize » + jeton).
"""
from __future__ import annotations

import argparse
import logging
import os
import secrets
import sys

import uvicorn

from app.api.app import create_app
from app.api.deps import AppContext
from app.config import APP_VERSION, Settings
from app.database.database import Database
from app.database.migrations import MigrationError
from app.logging_setup import configure_logging
from app.observer_service import ObserverService, game_window_frames
from app.parent_watch import watch_parent
from app.vision.frame import VisionModels, analyze_frame
from app.vision.image_io import TemplatesNotFoundError

HOST = "127.0.0.1"
TOKEN_ENV = "COC_AUTOFARM_TOKEN"
DEV_DASHBOARD_URL = "http://localhost:5173"  # serveur de développement Vite (frontend/)

logger = logging.getLogger("app.main")


class ShutdownSwitch:
    """Relie la demande d'arrêt (API, parent fermé) au serveur uvicorn, créé plus tard."""

    def __init__(self) -> None:
        self.server: uvicorn.Server | None = None

    def __call__(self) -> None:
        if self.server is not None:
            self.server.should_exit = True  # uvicorn termine les requêtes puis appelle le « lifespan »


def build_context(settings: Settings, shutdown: ShutdownSwitch | None = None) -> AppContext:
    db = Database.open(settings.database_path, settings.backups_dir)
    observer = None
    try:
        models = VisionModels.load()
        observer = ObserverService(settings, db, game_window_frames(settings),
                                   lambda bgr: analyze_frame(bgr, models))
    except TemplatesNotFoundError as exc:
        logger.error("Modèles de vision absents : %s", exc)
    token = os.environ.get(TOKEN_ENV) or secrets.token_urlsafe(24)
    return AppContext(settings=settings, db=db, token=token, vision_ready=observer is not None,
                      observer=observer, request_shutdown=shutdown)


def main() -> int:
    settings = Settings.load()
    configure_logging(settings.logs_dir)
    parser = argparse.ArgumentParser(description="Backend local de CoC AutoFarm")
    parser.add_argument("--port", type=int, default=8765, help="port local (défaut : %(default)s)")
    parser.add_argument("--parent-pid", type=int, default=None, help="s'arrêter quand ce processus se termine")
    args = parser.parse_args()

    shutdown = ShutdownSwitch()
    try:
        context = build_context(settings, shutdown)
    except MigrationError as exc:
        logger.error("Erreur base de données : %s", exc)
        print(f"Erreur base de données : {exc}", file=sys.stderr)
        return 1

    server = uvicorn.Server(uvicorn.Config(create_app(context), host=HOST, port=args.port, log_level="warning"))
    shutdown.server = server
    if args.parent_pid:
        watch_parent(args.parent_pid, shutdown)

    logger.info("Moteur démarré (version %s, port %d, vision %s)", APP_VERSION, args.port,
                "prête" if context.vision_ready else "indisponible")
    print(f"\nCoC AutoFarm - API sur http://{HOST}:{args.port}")
    print(f"Documentation : http://{HOST}:{args.port}/docs")
    if not os.environ.get(TOKEN_ENV):
        print(f"Jeton (bouton « Authorize » de /docs) : {context.token}")
        print(f"Dashboard (dev, après « npm run dev ») : {DEV_DASHBOARD_URL}/?token={context.token}")
    print("Ctrl+C pour arrêter.\n")
    server.run()
    logger.info("Moteur arrêté")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
