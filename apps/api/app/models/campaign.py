from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import sa_enum
from app.models.mixins import TimestampMixin


class CampaignStatus(str, enum.Enum):
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    target_page_id: Mapped[int] = mapped_column(ForeignKey("target_pages.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    total_links_target: Mapped[int] = mapped_column(Integer)
    blog_count: Mapped[int] = mapped_column(Integer)
    duration_days: Mapped[int] = mapped_column(Integer)
    status: Mapped[CampaignStatus] = mapped_column(
        sa_enum(CampaignStatus, "campaign_status"), default=CampaignStatus.PLANNING
    )
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="campaigns")
    target_page: Mapped["TargetPage"] = relationship()
    topics: Mapped[list["Topic"]] = relationship(back_populates="campaign", cascade="all, delete-orphan")
    articles: Mapped[list["Article"]] = relationship(back_populates="campaign", cascade="all, delete-orphan")
