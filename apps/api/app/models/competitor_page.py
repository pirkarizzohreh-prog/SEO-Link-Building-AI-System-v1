from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import JSONType
from app.models.mixins import TimestampMixin


class CompetitorPage(Base, TimestampMixin):
    __tablename__ = "competitor_pages"

    id: Mapped[int] = mapped_column(primary_key=True)
    competitor_id: Mapped[int] = mapped_column(ForeignKey("competitors.id", ondelete="CASCADE"))
    target_page_id: Mapped[int | None] = mapped_column(
        ForeignKey("target_pages.id", ondelete="SET NULL"), nullable=True
    )
    source_serp_snapshot_id: Mapped[int | None] = mapped_column(
        ForeignKey("serp_snapshots.id", ondelete="SET NULL"), nullable=True
    )
    url: Mapped[str] = mapped_column(String(1000))
    fetched_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fetched_headings: Mapped[list | None] = mapped_column(JSONType, nullable=True)
    fetched_word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    top_keywords: Mapped[list | None] = mapped_column(JSONType, nullable=True)
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    competitor: Mapped["Competitor"] = relationship(back_populates="pages")
    source_serp_snapshot: Mapped["SerpSnapshot | None"] = relationship(back_populates="competitor_pages")
    content_gaps: Mapped[list["ContentGap"]] = relationship(back_populates="source_competitor_page")
