from __future__ import annotations

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import JSONType
from app.models.mixins import TimestampMixin, UpdatedAtMixin


class ContentTemplate(Base, TimestampMixin, UpdatedAtMixin):
    __tablename__ = "content_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    applicable_page_types: Mapped[list | None] = mapped_column(JSONType, nullable=True)
    default_outline_skeleton: Mapped[dict | list | None] = mapped_column(JSONType, nullable=True)
    default_word_count: Mapped[int] = mapped_column(Integer, default=1200)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
