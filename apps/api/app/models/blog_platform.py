from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import sa_enum
from app.models.mixins import TimestampMixin


class BlogPlatformStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class BlogPlatform(Base, TimestampMixin):
    __tablename__ = "blog_platforms"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(1000))
    status: Mapped[BlogPlatformStatus] = mapped_column(
        sa_enum(BlogPlatformStatus, "blog_platform_status"), default=BlogPlatformStatus.ACTIVE
    )
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_encrypted: Mapped[str | None] = mapped_column(String(500), nullable=True)
    login_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    category_default: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_publish_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    articles: Mapped[list["Article"]] = relationship(back_populates="blog_platform")
    publications: Mapped[list["Publication"]] = relationship(back_populates="blog_platform")
