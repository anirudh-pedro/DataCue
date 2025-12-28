"""Firebase Authentication middleware for FastAPI."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.config import get_settings

_LOGGER = logging.getLogger(__name__)

# Firebase public keys endpoint for JWT verification
FIREBASE_KEYS_URL = "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com"

# Cache for Firebase public keys
_firebase_keys_cache: dict = {}


@dataclass
class FirebaseUser:
    """Represents an authenticated Firebase user."""
    
    uid: str
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    email_verified: bool = False
    
    @classmethod
    def from_token_payload(cls, payload: dict) -> "FirebaseUser":
        """Create FirebaseUser from decoded JWT payload."""
        return cls(
            uid=payload.get("user_id") or payload.get("sub"),
            email=payload.get("email"),
            name=payload.get("name"),
            picture=payload.get("picture"),
            email_verified=payload.get("email_verified", False),
        )


class FirebaseAuthBearer(HTTPBearer):
    """Custom HTTPBearer that handles Firebase JWT tokens."""
    
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        self.settings = get_settings()
    
    async def __call__(self, request: Request) -> Optional[FirebaseUser]:
        """Validate Firebase JWT and return user info."""
        
        # Check if auth is disabled (development mode)
        if self.settings.disable_firebase_auth:
            # In dev mode, try to extract user info from JWT without full validation
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                # If it looks like a JWT (has 2 dots), decode it without verification
                if token and token.count(".") == 2:
                    try:
                        user = self._decode_jwt_unsafe(token)
                        return user
                    except Exception as e:
                        _LOGGER.debug(f"Failed to decode JWT in dev mode: {e}")
                # If it looks like a Firebase UID (not a JWT), use it directly
                elif token and len(token) < 50:
                    return FirebaseUser(
                        uid=token,
                        email="dev@datacue.local",
                        name="Development User",
                        email_verified=True,
                    )
            
            # Check URL path for user ID (e.g., /sessions/user/{user_id})
            path_parts = request.url.path.split("/")
            if "user" in path_parts:
                user_idx = path_parts.index("user")
                if user_idx + 1 < len(path_parts):
                    return FirebaseUser(
                        uid=path_parts[user_idx + 1],
                        email="dev@datacue.local",
                        name="Development User",
                        email_verified=True,
                    )
            
            # Fallback to generic dev user
            return FirebaseUser(
                uid="dev-user-123",
                email="dev@datacue.local",
                name="Development User",
                email_verified=True,
            )
        
        # Get the authorization header
        credentials: Optional[HTTPAuthorizationCredentials] = await super().__call__(request)
        
        if not credentials:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing authentication token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None
        
        # Verify the Firebase token
        try:
            user = await self._verify_firebase_token(credentials.credentials)
            return user
        except Exception as e:
            _LOGGER.warning(f"Firebase token verification failed: {e}")
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid authentication token: {str(e)}",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None
    
    def _decode_jwt_unsafe(self, token: str) -> FirebaseUser:
        """Decode JWT without verification (dev mode only)."""
        import base64
        import json
        
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid token format")
        
        # Decode payload (middle part)
        payload_b64 = parts[1] + "=" * (4 - len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        
        return FirebaseUser.from_token_payload(payload)
    
    async def _verify_firebase_token(self, token: str) -> FirebaseUser:
        """Verify Firebase ID token and return user info."""
        import base64
        import json
        
        try:
            # Decode token without verification first to get header and payload
            # Note: In production, use firebase-admin SDK for proper verification
            parts = token.split(".")
            if len(parts) != 3:
                raise ValueError("Invalid token format")
            
            # Decode header
            header_b64 = parts[0] + "=" * (4 - len(parts[0]) % 4)
            header = json.loads(base64.urlsafe_b64decode(header_b64))
            
            # Decode payload
            payload_b64 = parts[1] + "=" * (4 - len(parts[1]) % 4)
            payload = json.loads(base64.urlsafe_b64decode(payload_b64))
            
            # Basic validation
            import time
            now = time.time()
            
            # Check expiration
            if payload.get("exp", 0) < now:
                raise ValueError("Token has expired")
            
            # Check issued at
            if payload.get("iat", now + 1) > now + 60:  # 60 second clock skew tolerance
                raise ValueError("Token issued in the future")
            
            # Check issuer (should be Firebase project)
            expected_issuer = f"https://securetoken.google.com/{self.settings.firebase_project_id}"
            if payload.get("iss") != expected_issuer:
                # Allow if project ID not configured
                if self.settings.firebase_project_id:
                    raise ValueError(f"Invalid token issuer: {payload.get('iss')}")
            
            # Check audience
            if payload.get("aud") != self.settings.firebase_project_id:
                if self.settings.firebase_project_id:
                    raise ValueError(f"Invalid token audience: {payload.get('aud')}")
            
            return FirebaseUser.from_token_payload(payload)
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to decode token: {e}")
        except Exception as e:
            raise ValueError(f"Token verification failed: {e}")


# Create singleton instance
firebase_auth = FirebaseAuthBearer(auto_error=True)
firebase_auth_optional = FirebaseAuthBearer(auto_error=False)


# Dependency functions
async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> FirebaseUser:
    """Get the current authenticated user. Raises 401 if not authenticated."""
    settings = get_settings()
    
    # In dev mode, extract user from various sources
    if settings.disable_firebase_auth:
        # Try to decode JWT from auth header
        if credentials and credentials.credentials:
            token = credentials.credentials
            if token.count(".") == 2:
                try:
                    import base64, json
                    parts = token.split(".")
                    payload_b64 = parts[1] + "=" * (4 - len(parts[1]) % 4)
                    payload = json.loads(base64.urlsafe_b64decode(payload_b64))
                    return FirebaseUser.from_token_payload(payload)
                except Exception:
                    pass
            # Simple token (UID)
            elif len(token) < 50:
                return FirebaseUser(uid=token, email="dev@datacue.local", name="Dev User", email_verified=True)
        
        # Extract from URL path
        path_parts = request.url.path.split("/")
        if "user" in path_parts:
            user_idx = path_parts.index("user")
            if user_idx + 1 < len(path_parts):
                return FirebaseUser(uid=path_parts[user_idx + 1], email="dev@datacue.local", name="Dev User", email_verified=True)
        
        # Fallback dev user
        return FirebaseUser(uid="dev-user-123", email="dev@datacue.local", name="Dev User", email_verified=True)
    
    # Production mode - require valid token
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        return await firebase_auth._verify_firebase_token(credentials.credentials)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[FirebaseUser]:
    """Get the current user if authenticated, otherwise None."""
    try:
        return await get_current_user(request, credentials)
    except HTTPException:
        return None


def require_auth():
    """Dependency that requires authentication."""
    return Depends(get_current_user)
