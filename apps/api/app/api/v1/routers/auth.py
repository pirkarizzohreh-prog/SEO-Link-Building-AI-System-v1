from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.security import (
    InvalidTokenError,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse, UserCreate, UserRead, UserUpdate
from app.utils.crud import CRUDBase

router = APIRouter(prefix="/auth", tags=["Auth"])
users_router = APIRouter(prefix="/users", tags=["Users"])
user_crud = CRUDBase(User)


def _tokens_for(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    return _tokens_for(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        user_id = decode_token(payload.refresh_token, expected_type=TokenType.REFRESH)
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    return _tokens_for(user)


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return current_user


# --- User management (addendum to docs/API_SPEC.md's Auth section) ---
# Not in the original spec, but needed for an internal multi-user tool to
# actually onboard teammates once login is required everywhere. Restricted
# to admins; the very first admin is created out-of-band via
# `python -m app.cli create-admin` (see apps/api/README.md) since there is
# no user yet to authorize the first POST /users call.


@users_router.get("", response_model=list[UserRead], dependencies=[Depends(require_admin)])
def list_users(db: Session = Depends(get_db)):
    return user_crud.list(db, limit=200)


@users_router.post("", response_model=UserRead, status_code=201, dependencies=[Depends(require_admin)])
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(
        name=payload.name,
        email=payload.email,
        role=payload.role,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@users_router.put("/{user_id}", response_model=UserRead, dependencies=[Depends(require_admin)])
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    user = user_crud.get(db, user_id)
    data = payload.model_dump(exclude_unset=True)
    new_password = data.pop("password", None)
    for field, value in data.items():
        setattr(user, field, value)
    if new_password:
        user.password_hash = hash_password(new_password)
    db.commit()
    db.refresh(user)
    return user
