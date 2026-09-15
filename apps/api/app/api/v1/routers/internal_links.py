from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.ai_job import JobType
from app.models.internal_link_suggestion import InternalLinkStatus, InternalLinkSuggestion
from app.models.project import Project
from app.schemas.internal_link_suggestion import (
    InternalLinkSuggestionRead,
    InternalLinkSuggestionStatusUpdate,
)
from app.schemas.job import AiJobRead
from app.services.job_service import enqueue_job
from app.utils.crud import CRUDBase

router = APIRouter(tags=["Internal Link Suggestions"])
crud = CRUDBase(InternalLinkSuggestion)


@router.get("/projects/{project_id}/internal-link-suggestions", response_model=list[InternalLinkSuggestionRead])
def list_internal_link_suggestions(
    project_id: int, status: InternalLinkStatus | None = None, db: Session = Depends(get_db)
):
    return crud.list(db, limit=500, project_id=project_id, status=status)


@router.post("/internal-link-suggestions/{suggestion_id}/apply", response_model=InternalLinkSuggestionRead)
def apply_suggestion(suggestion_id: int, db: Session = Depends(get_db)):
    return crud.update(db, suggestion_id, InternalLinkSuggestionStatusUpdate(status=InternalLinkStatus.APPLIED))


@router.post("/internal-link-suggestions/{suggestion_id}/dismiss", response_model=InternalLinkSuggestionRead)
def dismiss_suggestion(suggestion_id: int, db: Session = Depends(get_db)):
    return crud.update(db, suggestion_id, InternalLinkSuggestionStatusUpdate(status=InternalLinkStatus.DISMISSED))


@router.post("/projects/{project_id}/analyze-internal-links", response_model=AiJobRead, status_code=202)
def analyze_internal_links(project_id: int, db: Session = Depends(get_db)):
    if db.get(Project, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found")
    return enqueue_job(
        db, job_type=JobType.INTERNAL_LINK_SUGGESTION, reference_table="projects", reference_id=project_id
    )
