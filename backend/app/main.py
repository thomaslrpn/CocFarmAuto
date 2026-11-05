"""Démarre le backend : `python -m app.main [--port 8765]`.

- N'écoute que 127.0.0.1 : inaccessible depuis le réseau.
- Jeton : variable d'environnement COC_AUTOFARM_TOKEN (fournie par l'application
  de bureau en phase 7), sinon généré au hasard et affiché.
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
from app.config import Settings
from app.database.database import Database
from app.database.migrations import MigrationError
from app.vision.frame import VisionModels
from app.vision.image_io import TemplatesNotFoundError

HOST = "127.0.0.1"
TOKEN_ENV = "COC_AUTOFARM_TOKEN"

logger = logging.getLogger("app.main")


def build_context(settings: Settings) -> AppContext:
    db = Database.open(settings.database_path, settings.backups_dir)
    try:
        VisionModels.load()
        vision_ready = True
    except TemplatesNotFoundError as exc:
        logger.error("Modèles de vision absents : %s", exc)
        vision_ready = False
    token = os.environ.get(TOKEN_ENV) or secrets.token_urlsafe(24)
    return AppContext(settings=settings, db=db, token=token, vision_ready=vision_ready)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Backend local de CoC AutoFarm")
    parser.add_argument("--port", type=int, default=8765, help="port local (défaut : %(default)s)")
    args = parser.parse_args()

    try:
        context = build_context(Settings.load())
    except MigrationError as exc:
        print(f"Erreur base de données : {exc}", file=sys.stderr)
        return 1

    print(f"\nCoC AutoFarm - API sur http://{HOST}:{args.port}")
    print(f"Documentation : http://{HOST}:{args.port}/docs")
    if not os.environ.get(TOKEN_ENV):
        print(f"Jeton (bouton « Authorize » de /docs) : {context.token}")
    print("Ctrl+C pour arrêter.\n")
    uvicorn.run(create_app(context), host=HOST, port=args.port, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
