from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.internal_link_suggestion import InternalLinkStatus, InternalLinkSuggestion
from app.schemas.internal_link_suggestion import (
    InternalLinkSuggestionRead,
    InternalLinkSuggestionStatusUpdate,
)
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


# NOTE: POST /projects/{id}/analyze-internal-links is an AI job — Sprint 3.
