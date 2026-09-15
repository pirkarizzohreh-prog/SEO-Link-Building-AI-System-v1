from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.ai_job import JobType
from app.models.approval import ApprovalDecision, ApprovalType
from app.models.content_status_history import PipelineStage
from app.models.topic import Topic, TopicStatus
from app.models.user import User
from app.schemas.approval import ActionNote
from app.schemas.job import AiJobRead
from app.schemas.topic import TopicCreate, TopicRead, TopicUpdate
from app.services.approval_service import record_approval
from app.services.job_service import enqueue_job
from app.services.status_history_service import record_transition
from app.utils.crud import CRUDBase

router = APIRouter(tags=["Topics"])
crud = CRUDBase(Topic)


@router.get("/campaigns/{campaign_id}/topics", response_model=list[TopicRead])
def list_topics(campaign_id: int, db: Session = Depends(get_db)):
    return crud.list(db, limit=500, campaign_id=campaign_id)


@router.post("/campaigns/{campaign_id}/topics", response_model=TopicRead, status_code=201)
def create_topic(campaign_id: int, payload: TopicCreate, db: Session = Depends(get_db)):
    return crud.create(db, payload, campaign_id=campaign_id)


@router.put("/topics/{topic_id}", response_model=TopicRead)
def update_topic(topic_id: int, payload: TopicUpdate, db: Session = Depends(get_db)):
    return crud.update(db, topic_id, payload)


@router.post("/topics/{topic_id}/approve", response_model=TopicRead)
def approve_topic(
    topic_id: int,
    payload: ActionNote = ActionNote(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Idea -> Brief. Human Approval Layer: records who approved it, not
    just that it happened — see docs/AI_WORKFLOW.md.
    """
    topic = crud.get(db, topic_id)
    from_status = topic.status.value
    topic.status = TopicStatus.SELECTED

    record_approval(
        db,
        entity_table="topics",
        entity_id=topic.id,
        approval_type=ApprovalType.TOPIC_SELECTION,
        decision=ApprovalDecision.APPROVED,
        decided_by=current_user,
        note=payload.note,
    )
    record_transition(
        db,
        entity_table="topics",
        entity_id=topic.id,
        stage=PipelineStage.IDEA,
        from_status=from_status,
        to_status=topic.status.value,
        actor=current_user,
    )
    db.commit()
    db.refresh(topic)
    return topic


@router.post("/topics/{topic_id}/reject", response_model=TopicRead)
def reject_topic(
    topic_id: int,
    payload: ActionNote = ActionNote(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    topic = crud.get(db, topic_id)
    from_status = topic.status.value
    topic.status = TopicStatus.REJECTED

    record_approval(
        db,
        entity_table="topics",
        entity_id=topic.id,
        approval_type=ApprovalType.TOPIC_SELECTION,
        decision=ApprovalDecision.REJECTED,
        decided_by=current_user,
        note=payload.note,
    )
    record_transition(
        db,
        entity_table="topics",
        entity_id=topic.id,
        stage=PipelineStage.REJECTED,
        from_status=from_status,
        to_status=topic.status.value,
        actor=current_user,
        note=payload.note,
    )
    db.commit()
    db.refresh(topic)
    return topic


@router.post("/topics/{topic_id}/generate-brief", response_model=AiJobRead, status_code=202)
def generate_brief(topic_id: int, db: Session = Depends(get_db)):
    topic = crud.get(db, topic_id)
    if topic.status != TopicStatus.SELECTED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Topic {topic_id} must be approved (selected) before generating a brief for it",
        )
    return enqueue_job(db, job_type=JobType.BRIEF_GENERATION, reference_table="topics", reference_id=topic.id)
