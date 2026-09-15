"""FastAPI dependencies for authentication/authorization.

`current_user` is applied to almost every endpoint (wired at the router
group level in app/main.py) per docs/API_SPEC.md: "Auth: Authorization:
Bearer <JWT> (به‌جز /auth/login)". `require_admin` narrows further, for
the handful of destructive/user-management endpoints — see
docs/API_SPEC.md's Users addendum for exactly which ones.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import InvalidTokenError, TokenType, decode_token
from app.db.session import get_db
from app.models.user import User, UserRole

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized

    try:
        user_id = decode_token(credentials.credentials, expected_type=TokenType.ACCESS)
    except InvalidTokenError as exc:
        raise unauthorized from exc

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise unauthorized
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires an admin.",
        )
    return current_user
