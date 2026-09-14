from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.content_brief import ContentBrief
from app.schemas.content_brief import ContentBriefCreate, ContentBriefRead, ContentBriefUpdate
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


# NOTE: POST /content-briefs/{id}/approve (writes `approvals` +
# `content_status_history`) needs an authenticated user — Sprint 2.
# POST /content-briefs/{id}/generate-article is an AI job — Sprint 3.
