from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.ai_job import AiJob, JobStatus, JobType
from app.schemas.job import AiJobRead
from app.utils.crud import CRUDBase

router = APIRouter(prefix="/jobs", tags=["AI Jobs"])
crud = CRUDBase(AiJob)


@router.get("", response_model=list[AiJobRead])
def list_jobs(
    status: JobStatus | None = None,
    job_type: JobType | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Read-only in Sprint 1 — jobs are created by AI-triggering endpoints
    and processed by the worker, both added in Sprint 3.
    """
    return crud.list(db, skip=skip, limit=limit, status=status, job_type=job_type)


@router.get("/{job_id}", response_model=AiJobRead)
def get_job(job_id: int, db: Session = Depends(get_db)):
    return crud.get(db, job_id)
