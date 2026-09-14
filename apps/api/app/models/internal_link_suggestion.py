from __future__ import annotations

import enum

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import sa_enum
from app.models.mixins import TimestampMixin


class InternalLinkStatus(str, enum.Enum):
    SUGGESTED = "suggested"
    APPLIED = "applied"
    DISMISSED = "dismissed"


class InternalLinkSuggestion(Base, TimestampMixin):
    __tablename__ = "internal_link_suggestions"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    source_target_page_id: Mapped[int] = mapped_column(ForeignKey("target_pages.id", ondelete="CASCADE"))
    destination_target_page_id: Mapped[int] = mapped_column(ForeignKey("target_pages.id", ondelete="CASCADE"))
    suggested_anchor: Mapped[str] = mapped_column(String(500))
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[InternalLinkStatus] = mapped_column(
        sa_enum(InternalLinkStatus, "internal_link_status"), default=InternalLinkStatus.SUGGESTED
    )

    project: Mapped["Project"] = relationship(back_populates="internal_link_suggestions")
    source_target_page: Mapped["TargetPage"] = relationship(foreign_keys=[source_target_page_id])
    destination_target_page: Mapped["TargetPage"] = relationship(foreign_keys=[destination_target_page_id])
