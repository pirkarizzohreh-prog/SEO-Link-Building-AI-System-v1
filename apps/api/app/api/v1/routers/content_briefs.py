from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.approval import ApprovalDecision, ApprovalType
from app.models.content_brief import BriefStatus, ContentBrief
from app.models.content_status_history import PipelineStage
from app.models.user import User
from app.schemas.approval import ActionNote
from app.schemas.content_brief import ContentBriefCreate, ContentBriefRead, ContentBriefUpdate
from app.services.approval_service import record_approval
from app.services.status_history_service import record_transition
from app.utils.crud import CRUDBase

router = APIRouter(tags=["Content Briefs"])
crud = CRUDBase(ContentBrief)


@router.get("/topics/{topic_id}/brief", response_model=ContentBriefRead)
def get_brief_for_topic(topic_id: int, db: Session = Depends(get_db)):
    brief = db.query(ContentBrief).filter(ContentBrief.topic_id == topic_id).first()
    if brief is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No brief for topic {topic_id} yet")
    return brief


@router.post("/topics/{topic_id}/brief", response_model=ContentBriefRead, status_code=201)
def create_brief_for_topic(topic_id: int, payload: ContentBriefCreate, db: Session = Depends(get_db)):
    """Manual brief creation (see schemas.content_brief.ContentBriefCreate).
    Generation via the Content Brief Generator agent job is Sprint 3.
    """
    return crud.create(db, payload, topic_id=topic_id)


@router.put("/content-briefs/{brief_id}", response_model=ContentBriefRead)
def update_brief(brief_id: int, payload: ContentBriefUpdate, db: Session = Depends(get_db)):
    return crud.update(db, brief_id, payload)


@router.post("/content-briefs/{brief_id}/approve", response_model=ContentBriefRead)
def approve_brief(
    brief_id: int,
    payload: ActionNote = ActionNote(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Brief -> Writing."""
    brief = crud.get(db, brief_id)
    from_status = brief.status.value
    brief.status = BriefStatus.APPROVED

    record_approval(
        db,
        entity_table="content_briefs",
        entity_id=brief.id,
        approval_type=ApprovalType.BRIEF_APPROVAL,
        decision=ApprovalDecision.APPROVED,
        decided_by=current_user,
        note=payload.note,
    )
    record_transition(
        db,
        entity_table="content_briefs",
        entity_id=brief.id,
        stage=PipelineStage.BRIEF,
        from_status=from_status,
        to_status=brief.status.value,
        actor=current_user,
    )
    db.commit()
    db.refresh(brief)
    return brief


# NOTE: POST /content-briefs/{id}/generate-article is an AI job — Sprint 3.
