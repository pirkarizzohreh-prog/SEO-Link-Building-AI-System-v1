from __future__ import annotations

import enum

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import sa_enum
from app.models.mixins import TimestampMixin


class GapType(str, enum.Enum):
    TOPIC = "topic"
    KEYWORD = "keyword"
    HEADING = "heading"


class GapStatus(str, enum.Enum):
    NEW = "new"
    USED_IN_TOPIC = "used_in_topic"
    IGNORED = "ignored"


class ContentGap(Base, TimestampMixin):
    __tablename__ = "content_gaps"

    id: Mapped[int] = mapped_column(primary_key=True)
    target_page_id: Mapped[int] = mapped_column(ForeignKey("target_pages.id", ondelete="CASCADE"))
    gap_topic: Mapped[str] = mapped_column(String(500))
    gap_type: Mapped[GapType] = mapped_column(sa_enum(GapType, "gap_type"), default=GapType.TOPIC)
    source_competitor_page_id: Mapped[int | None] = mapped_column(
        ForeignKey("competitor_pages.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[GapStatus] = mapped_column(sa_enum(GapStatus, "gap_status"), default=GapStatus.NEW)

    target_page: Mapped["TargetPage"] = relationship(back_populates="content_gaps")
    source_competitor_page: Mapped["CompetitorPage | None"] = relationship(back_populates="content_gaps")
