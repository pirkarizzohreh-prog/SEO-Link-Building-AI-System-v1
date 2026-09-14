from __future__ import annotations

import enum

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import sa_enum
from app.models.mixins import TimestampMixin


class PipelineStage(str, enum.Enum):
    """The 6 stages of the Advanced Content Status Workflow (docs/AI_WORKFLOW.md)."""

    IDEA = "idea"
    BRIEF = "brief"
    WRITING = "writing"
    AUDIT = "audit"
    HUMAN_REVIEW = "human_review"
    PUBLISHED = "published"
    REJECTED = "rejected"


class ActorType(str, enum.Enum):
    AI = "ai"
    USER = "user"


class ContentStatusHistory(Base, TimestampMixin):
    """Polymorphic audit log of every stage transition, across topics,
    content_briefs and articles. Populated from Sprint 2 onward (once
    actors — AI jobs and authenticated users — actually exist).
    """

    __tablename__ = "content_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_table: Mapped[str] = mapped_column(String(100))
    entity_id: Mapped[int] = mapped_column(Integer)
    stage: Mapped[PipelineStage] = mapped_column(sa_enum(PipelineStage, "pipeline_stage"))
    from_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    to_status: Mapped[str] = mapped_column(String(100))
    actor_type: Mapped[ActorType] = mapped_column(sa_enum(ActorType, "actor_type"))
    actor_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
