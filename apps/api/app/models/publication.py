from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import sa_enum
from app.models.mixins import TimestampMixin


class PublicationMethod(str, enum.Enum):
    MANUAL = "manual"
    AUTOMATED = "automated"


class PublicationStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"


class Publication(Base, TimestampMixin):
    __tablename__ = "publications"

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"))
    blog_platform_id: Mapped[int] = mapped_column(ForeignKey("blog_platforms.id"))
    method: Mapped[PublicationMethod] = mapped_column(sa_enum(PublicationMethod, "publication_method"))
    status: Mapped[PublicationStatus] = mapped_column(sa_enum(PublicationStatus, "publication_status"))
    published_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    article: Mapped["Article"] = relationship(back_populates="publications")
    blog_platform: Mapped["BlogPlatform"] = relationship(back_populates="publications")
