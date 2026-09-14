from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import JSONType, sa_enum
from app.models.mixins import TimestampMixin


class JobType(str, enum.Enum):
    KEYWORD_INTEL = "keyword_intel"
    TOPIC_GEN = "topic_gen"
    ARTICLE_WRITE = "article_write"
    SEO_AUDIT = "seo_audit"
    PUBLISH = "publish"
    COMPETITOR_ANALYSIS = "competitor_analysis"
    BRIEF_GENERATION = "brief_generation"
    INTERNAL_LINK_SUGGESTION = "internal_link_suggestion"
    SERP_FETCH = "serp_fetch"


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class LlmProvider(str, enum.Enum):
    OPENAI = "openai"
    CLAUDE = "claude"


class AiJob(Base, TimestampMixin):
    """The MVP job queue + full AI call log (see docs/ARCHITECTURE.md).

    Sprint 1 only defines the table and exposes read-only endpoints; the
    worker that polls `status='pending'` and the agents that actually
    populate/consume these rows are built in Sprint 3 (AI Agents).
    """

    __tablename__ = "ai_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_type: Mapped[JobType] = mapped_column(sa_enum(JobType, "job_type"))
    reference_table: Mapped[str] = mapped_column(String(100))
    reference_id: Mapped[int] = mapped_column(Integer)
    status: Mapped[JobStatus] = mapped_column(sa_enum(JobStatus, "job_status"), default=JobStatus.PENDING)
    provider: Mapped[LlmProvider | None] = mapped_column(sa_enum(LlmProvider, "llm_provider"), nullable=True)
    prompt_template_id: Mapped[int | None] = mapped_column(
        ForeignKey("prompt_templates.id"), nullable=True
    )
    prompt_template_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_payload: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    output_payload: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_estimate: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
