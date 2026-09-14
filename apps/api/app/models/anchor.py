from __future__ import annotations

import enum

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import sa_enum
from app.models.mixins import TimestampMixin


class AnchorType(str, enum.Enum):
    EXACT = "exact"
    PARTIAL = "partial"
    SEMANTIC = "semantic"
    BRAND = "brand"


class Anchor(Base, TimestampMixin):
    __tablename__ = "anchors"

    id: Mapped[int] = mapped_column(primary_key=True)
    target_page_id: Mapped[int] = mapped_column(ForeignKey("target_pages.id", ondelete="CASCADE"))
    anchor_text: Mapped[str] = mapped_column(String(500))
    anchor_type: Mapped[AnchorType] = mapped_column(sa_enum(AnchorType, "anchor_type"))
    usage_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    target_page: Mapped["TargetPage"] = relationship(back_populates="anchors")
    usage_logs: Mapped[list["AnchorUsageLog"]] = relationship(
        back_populates="anchor", cascade="all, delete-orphan"
    )
