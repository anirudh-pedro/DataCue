"""Authentication utilities and FastAPI dependencies for Firebase ID tokens."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from shared.config import get_config

try:  # pragma: no cover - import guard for optional dependency
    import firebase_admin
    from firebase_admin import auth as firebase_auth, credentials
except ImportError:  # pragma: no cover - handled at runtime when auth is enabled
    firebase_admin = None  # type: ignore[assignment]
    firebase_auth = None  # type: ignore[assignment]
    credentials = None  # type: ignore[assignment]


class FirebaseInitialisationError(RuntimeError):
    """Raised when Firebase cannot be initialised despite being enabled."""


@dataclass
class AuthenticatedUser:
    """Represents the authenticated Firebase user context."""

    uid: str
    email: Optional[str]
    claims: Dict[str, Any]


_bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache(maxsize=1)
def _firebase_app() -> Optional["firebase_admin.App"]:
    """Initialise and cache the Firebase app when authentication is enabled."""

    config = get_config()
    if config.disable_firebase_auth:
        return None

    if firebase_admin is None or credentials is None:
        raise FirebaseInitialisationError(
            "firebase-admin is required when Firebase authentication is enabled."
        )

    if config.firebase_auth_emulator_host:
        os.environ.setdefault("FIREBASE_AUTH_EMULATOR_HOST", config.firebase_auth_emulator_host)

    try:
        # Reuse existing app if already initialised elsewhere.
        return firebase_admin.get_app()
    except ValueError:
        pass

    credential: "credentials.Base" | None = None

    if config.firebase_credentials_file:
        credential = credentials.Certificate(config.firebase_credentials_file)
    elif config.firebase_service_account:
        try:
            credential = credentials.Certificate(json.loads(config.firebase_service_account))
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            raise FirebaseInitialisationError(
                "FIREBASE_SERVICE_ACCOUNT_JSON contains invalid JSON."
            ) from exc

    if credential is None:
        raise FirebaseInitialisationError(
            "Firebase credentials are not configured. Set FIREBASE_CREDENTIALS_FILE "
            "or FIREBASE_SERVICE_ACCOUNT_JSON."
        )

    options: Dict[str, Any] = {}
    if config.firebase_project_id:
        options["projectId"] = config.firebase_project_id

    return firebase_admin.initialize_app(credential, options or None)


def _authenticate(
    *,
    bearer_token: Optional[str],
    query_token: Optional[str],
    debug_user_id: Optional[str],
) -> AuthenticatedUser:
    config = get_config()

    if config.disable_firebase_auth:
        if not debug_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication disabled for backend; supply X-Debug-User header for access.",
            )
        return AuthenticatedUser(uid=debug_user_id, email=None, claims={"debug": True})

    token = bearer_token or query_token
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication token")

    if firebase_auth is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Firebase authentication is not configured",
        )

    try:
        decoded = firebase_auth.verify_id_token(token, app=_firebase_app())
    except FirebaseInitialisationError:
        raise
    except Exception as exc:  # pragma: no cover - delegated to FastAPI error handling
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token") from exc

    uid = decoded.get("uid") or decoded.get("sub")
    if not uid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")

    return AuthenticatedUser(uid=uid, email=decoded.get("email"), claims=decoded)


async def get_authenticated_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    debug_user_id: Optional[str] = Header(default=None, alias="X-Debug-User", convert_underscores=False),
) -> AuthenticatedUser:
    """FastAPI dependency that verifies the request's Firebase ID token."""

    bearer_token = credentials.credentials if credentials else None

    try:
        return _authenticate(bearer_token=bearer_token, query_token=None, debug_user_id=debug_user_id)
    except FirebaseInitialisationError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


def authenticate_request(
    *,
    authorization: Optional[str] = None,
    token: Optional[str] = None,
    debug_user_id: Optional[str] = None,
) -> AuthenticatedUser:
    """Authenticate arbitrary requests (e.g. streaming endpoints) where dependencies cannot be used."""

    bearer_token: Optional[str] = None
    if authorization:
        scheme, _, value = authorization.partition(" ")
        if scheme.lower() == "bearer" and value.strip():
            bearer_token = value.strip()

    try:
        return _authenticate(bearer_token=bearer_token, query_token=token, debug_user_id=debug_user_id)
    except FirebaseInitialisationError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


__all__ = [
    "AuthenticatedUser",
    "authenticate_request",
    "get_authenticated_user",
]
