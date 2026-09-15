"""Executes one `ai_jobs` row: dispatches to the right agent, and owns
the job's lifecycle (running -> success/failed) plus chaining the next
job in a pipeline — see docs/AI_WORKFLOW.md ("زنجیره‌ی خودکار").

`process_job` is called both by app/jobs/worker.py's poll loop and
directly by tests (with a fake LLM client) — it has no dependency on how
the job was claimed.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable

from sqlalchemy.orm import Session

from app.ai.agent_result import AgentResult
from app.ai.agents import (
    brief_agent,
    competitor_intel_agent,
    internal_link_agent,
    keyword_agent,
    topic_agent,
    writer_agent,
)
from app.ai.providers.base import BaseLLMClient
from app.models.ai_job import AiJob, JobStatus, JobType
from app.services.job_service import enqueue_job

logger = logging.getLogger(__name__)

_AGENT_DISPATCH: dict[JobType, Callable[[Session, AiJob, BaseLLMClient], AgentResult]] = {
    JobType.KEYWORD_INTEL: keyword_agent.run,
    JobType.TOPIC_GEN: topic_agent.run,
    JobType.COMPETITOR_ANALYSIS: competitor_intel_agent.run,
    JobType.BRIEF_GENERATION: brief_agent.run,
    JobType.ARTICLE_WRITE: writer_agent.run,
    JobType.INTERNAL_LINK_SUGGESTION: internal_link_agent.run,
}

# keyword_intel -> topic_gen is the only automatic chain today (docs/
# AI_WORKFLOW.md's Stage: Idea); everything past it needs a human
# approval in between (topic approve -> generate-brief is a separate,
# user-triggered call, not chained).
_CHAIN_NEXT: dict[JobType, JobType] = {
    JobType.KEYWORD_INTEL: JobType.TOPIC_GEN,
}


def process_job(db: Session, job: AiJob, client: BaseLLMClient) -> None:
    job.status = JobStatus.RUNNING
    job.provider = client.provider_name
    job.started_at = datetime.now(timezone.utc)
    db.commit()

    agent_fn = _AGENT_DISPATCH.get(job.job_type)
    if agent_fn is None:
        db.rollback()
        job.status = JobStatus.FAILED
        job.error_message = f"No agent registered for job_type={job.job_type.value}"
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
        return

    try:
        result = agent_fn(db, job, client)
        job.output_payload = result.output_payload
        job.tokens_used = result.tokens_used
        job.cost_estimate = result.cost_estimate
        job.status = JobStatus.SUCCESS
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as exc:  # noqa: BLE001 - a failed job must never crash the worker loop
        logger.exception("ai_job %s (%s) failed", job.id, job.job_type.value)
        db.rollback()
        job.status = JobStatus.FAILED
        job.error_message = str(exc)[:2000]
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
        return

    next_type = _CHAIN_NEXT.get(job.job_type)
    if next_type is not None:
        enqueue_job(
            db,
            job_type=next_type,
            reference_table=job.reference_table,
            reference_id=job.reference_id,
        )
