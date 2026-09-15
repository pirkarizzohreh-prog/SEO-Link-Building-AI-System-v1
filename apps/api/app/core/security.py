"""Password hashing + JWT issuing/parsing.

Deliberately stateless: no refresh-token table / revocation list in
Sprint 2 — a refresh token is just a JWT with `type=refresh` and a longer
TTL. Revoking sessions server-side (e.g. on password change) is a known
gap, acceptable for an internal MVP tool; note it before adding
multi-tenant/external users.
"""

from __future__ import annotations

import enum
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings


class TokenType(str, enum.Enum):
    ACCESS = "access"
    REFRESH = "refresh"


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # Malformed hash (e.g. empty) — never let this raise past auth checks.
        return False


def _create_token(subject: int, token_type: TokenType, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(subject),
        "type": token_type.value,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: int) -> str:
    return _create_token(
        user_id, TokenType.ACCESS, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )


def create_refresh_token(user_id: int) -> str:
    return _create_token(
        user_id, TokenType.REFRESH, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )


class InvalidTokenError(Exception):
    pass


def decode_token(token: str, expected_type: TokenType) -> int:
    """Returns the user id encoded in `token`, or raises InvalidTokenError."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise InvalidTokenError(str(exc)) from exc

    if payload.get("type") != expected_type.value:
        raise InvalidTokenError(f"expected a {expected_type.value} token")

    try:
        return int(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise InvalidTokenError("token missing a valid subject") from exc
