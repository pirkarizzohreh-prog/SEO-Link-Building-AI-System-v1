from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import JSONType, sa_enum
from app.models.mixins import TimestampMixin


class SearchEngine(str, enum.Enum):
    GOOGLE = "google"


class SerpSource(str, enum.Enum):
    MANUAL = "manual"
    API = "api"


class SerpSnapshot(Base, TimestampMixin):
    __tablename__ = "serp_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    target_page_id: Mapped[int] = mapped_column(ForeignKey("target_pages.id", ondelete="CASCADE"))
    keyword: Mapped[str] = mapped_column(String(500))
    search_engine: Mapped[SearchEngine] = mapped_column(
        sa_enum(SearchEngine, "search_engine"), default=SearchEngine.GOOGLE
    )
    results: Mapped[list] = mapped_column(JSONType)
    source: Mapped[SerpSource] = mapped_column(sa_enum(SerpSource, "serp_source"), default=SerpSource.MANUAL)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    target_page: Mapped["TargetPage"] = relationship(back_populates="serp_snapshots")
    competitor_pages: Mapped[list["CompetitorPage"]] = relationship(back_populates="source_serp_snapshot")
