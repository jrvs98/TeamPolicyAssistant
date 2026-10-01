from dataclasses import dataclass
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from app.config import Settings, get_settings

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    subject: str
    username: str | None
    roles: frozenset[str]


@lru_cache
def get_jwks_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url)


def _unauthorized(detail: str = "Invalid or missing access token") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _roles_from_claims(claims: dict[str, object], client_id: str) -> frozenset[str]:
    roles: set[str] = set()
    realm_access = claims.get("realm_access")
    if isinstance(realm_access, dict) and isinstance(realm_access.get("roles"), list):
        roles.update(role for role in realm_access["roles"] if isinstance(role, str))

    resource_access = claims.get("resource_access")
    if isinstance(resource_access, dict):
        client_access = resource_access.get(client_id)
        if isinstance(client_access, dict) and isinstance(client_access.get("roles"), list):
            roles.update(role for role in client_access["roles"] if isinstance(role, str))
    return frozenset(roles)


def _decode_token(token: str, settings: Settings) -> dict[str, object]:
    try:
        jwks_client = get_jwks_client(f"{settings.keycloak_issuer}/protocol/openid-connect/certs")
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        options = {"verify_aud": settings.keycloak_audience is not None}
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=settings.keycloak_issuer,
            audience=settings.keycloak_audience,
            options=options,
        )
    except (jwt.InvalidTokenError, jwt.PyJWKClientError) as error:
        raise _unauthorized() from error


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()

    claims = _decode_token(credentials.credentials, settings)
    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        raise _unauthorized("Access token has no subject")

    username = claims.get("preferred_username")
    return CurrentUser(
        subject=subject,
        username=username if isinstance(username, str) else None,
        roles=_roles_from_claims(claims, settings.keycloak_client_id),
    )


def require_role(role: str):
    def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if role not in user.roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user

    return dependency


require_admin = require_role("admin")
require_employee = require_role("employee")
require_authenticated = get_current_user
