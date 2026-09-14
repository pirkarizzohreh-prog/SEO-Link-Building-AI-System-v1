from __future__ import annotations

import enum

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import sa_enum
from app.models.mixins import TimestampMixin


class PromptAgentType(str, enum.Enum):
    KEYWORD_INTEL = "keyword_intel"
    TOPIC_GEN = "topic_gen"
    COMPETITOR_ANALYSIS = "competitor_analysis"
    BRIEF_GENERATION = "brief_generation"
    ARTICLE_WRITE = "article_write"
    SEO_AUDIT = "seo_audit"
    INTERNAL_LINK_SUGGESTION = "internal_link_suggestion"


class PromptTemplate(Base, TimestampMixin):
    __tablename__ = "prompt_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    agent_type: Mapped[PromptAgentType] = mapped_column(
        sa_enum(PromptAgentType, "prompt_agent_type")
    )
    name: Mapped[str] = mapped_column(String(255))
    template_text: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
