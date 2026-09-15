"""The MVP job queue's worker — see docs/ARCHITECTURE.md ("چرا صف کار...
و نه فراخوانی همزمان"). A single long-running process that polls
`ai_jobs` for `status='pending'` rows and executes them one at a time.

Run it with:

    python -m app.jobs.worker

(docker-compose.yml runs this as its own `worker` service). No
concurrency control beyond `FOR UPDATE SKIP LOCKED` is implemented —
fine for a single worker process; add a proper lease/heartbeat if this
ever needs more than one.
"""

from __future__ import annotations

import logging
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.jobs.handlers import process_job
from app.models.ai_job import AiJob, JobStatus

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 3.0


def claim_next_job(db: Session) -> AiJob | None:
    stmt = select(AiJob).where(AiJob.status == JobStatus.PENDING).order_by(AiJob.created_at).limit(1)
    # SKIP LOCKED is Postgres-only; the test suite runs on SQLite, where
    # this degrades to a plain (unlocked) select — fine for a single
    # worker process and for tests, which call process_job directly
    # rather than running concurrent claim_next_job calls anyway.
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        stmt = stmt.with_for_update(skip_locked=True)
    return db.scalars(stmt).first()


def run_forever(poll_interval: float = POLL_INTERVAL_SECONDS) -> None:
    from app.ai.providers.factory import get_default_provider

    client = get_default_provider()
    logger.info("AI job worker started using provider=%s", client.provider_name.value)

    while True:
        db = SessionLocal()
        try:
            job = claim_next_job(db)
            if job is None:
                db.close()
                time.sleep(poll_interval)
                continue
            logger.info("Processing ai_job %s (%s)", job.id, job.job_type.value)
            process_job(db, job, client)
        finally:
            db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_forever()
