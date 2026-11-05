"""Dépendances partagées des routes : contexte de l'application, session, sécurité.

Sécurité : l'API n'écoute que 127.0.0.1 (ce PC) ET exige un jeton secret, généré
au démarrage. Le jeton est envoyé dans l'en-tête `Authorization: Bearer <jeton>`,
ou dans `?token=<jeton>` pour les images (une balise <img> ne peut pas envoyer d'en-tête).
Ainsi, une page web ouverte dans le navigateur ne peut pas interroger l'API.
"""
from __future__ import annotations

import secrets
from collections.abc import Callable, Iterator
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import Settings
from app.database.database import Database
from app.observer_service import ObserverService
from app.user_settings import UserSettings, load_user_settings


@dataclass(frozen=True)
class AppContext:
    """Tout ce dont les routes ont besoin, créé une seule fois au démarrage."""

    settings: Settings
    db: Database
    token: str
    vision_ready: bool  # modèles de reconnaissance présents
    observer: ObserverService | None = None  # None si la vision n'est pas prête
    request_shutdown: Callable[[], None] | None = None  # arrêt propre du moteur (application de bureau)


_bearer = HTTPBearer(auto_error=False, description="Jeton affiché au démarrage du backend")


def get_context(request: Request) -> AppContext:
    return request.app.state.context


def require_token(
    context: AppContext = Depends(get_context),
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    token: str | None = Query(default=None, description="Alternative à l'en-tête (images)"),
) -> None:
    provided = credentials.credentials if credentials else token
    # compare_digest : comparaison en temps constant (évite de deviner le jeton par mesure du temps)
    if provided is None or not secrets.compare_digest(provided, context.token):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Jeton manquant ou invalide",
                            headers={"WWW-Authenticate": "Bearer"})


def get_session(context: AppContext = Depends(get_context)) -> Iterator[Session]:
    with context.db.session() as session:
        yield session


def get_user_settings(
    session: Session = Depends(get_session), context: AppContext = Depends(get_context)
) -> UserSettings:
    return load_user_settings(session, context.settings.data_dir)
