from __future__ import annotations

import enum

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import JSONType, sa_enum
from app.models.mixins import TimestampMixin


class BriefStatus(str, enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"


class ContentBrief(Base, TimestampMixin):
    __tablename__ = "content_briefs"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), unique=True)
    content_template_id: Mapped[int | None] = mapped_column(
        ForeignKey("content_templates.id", ondelete="SET NULL"), nullable=True
    )
    target_page_id: Mapped[int] = mapped_column(ForeignKey("target_pages.id", ondelete="CASCADE"))
    outline: Mapped[list] = mapped_column(JSONType)
    target_word_count: Mapped[int] = mapped_column(Integer, default=1200)
    keywords_to_include: Mapped[list | None] = mapped_column(JSONType, nullable=True)
    must_include_points: Mapped[list | None] = mapped_column(JSONType, nullable=True)
    tone: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_content_gap_ids: Mapped[list | None] = mapped_column(JSONType, nullable=True)
    status: Mapped[BriefStatus] = mapped_column(sa_enum(BriefStatus, "brief_status"), default=BriefStatus.DRAFT)

    topic: Mapped["Topic"] = relationship(back_populates="brief")
    articles: Mapped[list["Article"]] = relationship(back_populates="content_brief")
