from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.ai_job import JobStatus, JobType, LlmProvider


class AiJobRead(BaseModel):
    """Read-only in Sprint 1 — jobs are created and processed by the
    worker + agents built in Sprint 3.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    job_type: JobType
    reference_table: str
    reference_id: int
    status: JobStatus
    provider: LlmProvider | None = None
    prompt_template_id: int | None = None
    prompt_template_version: int | None = None
    tokens_used: int | None = None
    cost_estimate: float | None = None
    error_message: str | None = None
    retry_count: int
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
