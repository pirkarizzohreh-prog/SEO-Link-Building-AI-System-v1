from __future__ import annotations

import enum

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import sa_enum
from app.models.mixins import TimestampMixin


class TopicStatus(str, enum.Enum):
    SUGGESTED = "suggested"
    SELECTED = "selected"
    REJECTED = "rejected"


class GeneratedBy(str, enum.Enum):
    AI = "ai"
    MANUAL = "manual"


class Topic(Base, TimestampMixin):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(500))
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TopicStatus] = mapped_column(sa_enum(TopicStatus, "topic_status"), default=TopicStatus.SUGGESTED)
    generated_by: Mapped[GeneratedBy] = mapped_column(
        sa_enum(GeneratedBy, "generated_by"), default=GeneratedBy.MANUAL
    )

    campaign: Mapped["Campaign"] = relationship(back_populates="topics")
    brief: Mapped["ContentBrief | None"] = relationship(
        back_populates="topic", uselist=False, cascade="all, delete-orphan"
    )
    articles: Mapped[list["Article"]] = relationship(back_populates="topic")
