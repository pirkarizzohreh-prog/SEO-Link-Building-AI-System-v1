from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import JSONType
from app.models.mixins import TimestampMixin, UpdatedAtMixin


class ProjectKnowledgeBase(Base, TimestampMixin, UpdatedAtMixin):
    __tablename__ = "project_knowledge_base"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), unique=True
    )
    brand_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    brand_voice_tone: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_audience: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    style_guidelines: Mapped[str | None] = mapped_column(Text, nullable=True)
    forbidden_words: Mapped[list | None] = mapped_column(JSONType, nullable=True)
    mandatory_points: Mapped[list | None] = mapped_column(JSONType, nullable=True)
    sample_reference_urls: Mapped[list | None] = mapped_column(JSONType, nullable=True)
    custom_rules: Mapped[dict | None] = mapped_column(JSONType, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="knowledge_base")
