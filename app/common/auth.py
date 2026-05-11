"""JWT auth + role-based dependency.

Production: swap for OIDC (Auth0 / Clerk / Cognito). This module's surface is
the durable contract; `verify_token` is the only piece that changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import get_settings


class Role(str, Enum):
    ADMIN = "admin"
    UPLOADER = "uploader"
    REVIEWER = "reviewer"
    APPROVER = "approver"
    VIEWER = "viewer"
    SYSTEM = "system"


@dataclass(frozen=True)
class CurrentUser:
    user_id: UUID
    email: str
    org_id: UUID
    roles: frozenset[Role]


_bearer = HTTPBearer(auto_error=True)


def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> CurrentUser:
    settings = get_settings()
    try:
        claims = jwt.decode(
            creds.credentials,
            settings.app_jwt_secret,
            algorithms=[settings.app_jwt_alg],
        )
        return CurrentUser(
            user_id=UUID(claims["sub"]),
            email=claims["email"],
            org_id=UUID(claims["org_id"]),
            roles=frozenset(Role(r) for r in claims.get("roles", [])),
        )
    except (JWTError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid token",
        ) from exc


def require_role(*allowed: Role):
    def _guard(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not user.roles.intersection(allowed):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"requires one of: {[r.value for r in allowed]}",
            )
        return user
    return _guard
