"""
Keycloak JWT verification helpers.

The extension obtains an access token via Keycloak's OIDC Authorization Code
flow and includes it as a Bearer token in every API request.  This module
validates that token against Keycloak's public key.

Environment variables (set in .env):
    KEYCLOAK_URL        Base URL of the Keycloak server, e.g. http://localhost:8080
    KEYCLOAK_REALM      Realm name, e.g. sustainability
    KEYCLOAK_CLIENT_ID  Client ID registered in Keycloak
"""
import os
from functools import lru_cache

import httpx
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

load_dotenv()

KEYCLOAK_URL: str = os.environ.get("KEYCLOAK_URL", "http://localhost:8080")
KEYCLOAK_REALM: str = os.environ.get("KEYCLOAK_REALM", "sustainability")
KEYCLOAK_CLIENT_ID: str = os.environ.get("KEYCLOAK_CLIENT_ID", "sustainability-extension")

_security = HTTPBearer(auto_error=False)


@lru_cache(maxsize=1)
def _get_public_key() -> str:
    """Fetch and cache the realm's RSA public key from Keycloak."""
    url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}"
    try:
        resp = httpx.get(url, timeout=5)
        resp.raise_for_status()
        b64 = resp.json()["public_key"]
        return f"-----BEGIN PUBLIC KEY-----\n{b64}\n-----END PUBLIC KEY-----"
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Could not reach Keycloak to verify token: {exc}",
        )


def _decode_token(token: str) -> dict:
    try:
        public_key = _get_public_key()
        return jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            # audience check is relaxed here; tighten by setting options if needed
            options={"verify_aud": False},
        )
    except JWTError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {exc}")


def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Security(_security),
) -> dict:
    """FastAPI dependency – returns the decoded JWT payload (user info)."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    return _decode_token(credentials.credentials)
