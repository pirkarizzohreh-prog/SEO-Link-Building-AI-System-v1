from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.topic import Topic
from app.schemas.topic import TopicCreate, TopicRead, TopicUpdate
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


# NOTE: POST /topics/{id}/approve and /reject (which also write to
# `approvals` + `content_status_history`) require a real authenticated
# user — added in Sprint 2 (Auth). POST /topics/{id}/generate-brief is an
# AI job, added in Sprint 3.
