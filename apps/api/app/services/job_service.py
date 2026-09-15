"""Enqueues rows onto the `ai_jobs` queue — see docs/ARCHITECTURE.md.

Routers call this and return immediately (the actual LLM call can take
30-60s); app/jobs/worker.py picks the row up separately. Nothing here
ever calls an LLM provider directly.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.ai_job import AiJob, JobStatus, JobType


def enqueue_job(
    db: Session,
    *,
    job_type: JobType,
    reference_table: str,
    reference_id: int,
    input_payload: dict[str, Any] | None = None,
) -> AiJob:
    job = AiJob(
        job_type=job_type,
        reference_table=reference_table,
        reference_id=reference_id,
        status=JobStatus.PENDING,
        input_payload=input_payload or {},
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job
