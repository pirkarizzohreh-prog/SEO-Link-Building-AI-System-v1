from __future__ import annotations

import enum

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import sa_enum
from app.models.mixins import TimestampMixin


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    EDITOR = "editor"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(sa_enum(UserRole, "user_role"), default=UserRole.EDITOR)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
