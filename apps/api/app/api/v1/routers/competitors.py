from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.competitor import Competitor
from app.models.competitor_page import CompetitorPage
from app.models.content_gap import ContentGap, GapStatus
from app.schemas.competitor_intel import (
    CompetitorCreate,
    CompetitorPageCreate,
    CompetitorPageRead,
    CompetitorRead,
    CompetitorUpdate,
    ContentGapRead,
    ContentGapUpdate,
)
from app.utils.crud import CRUDBase

router = APIRouter(tags=["Competitor Intelligence"])
competitor_crud = CRUDBase(Competitor)
competitor_page_crud = CRUDBase(CompetitorPage)
content_gap_crud = CRUDBase(ContentGap)


@router.get("/projects/{project_id}/competitors", response_model=list[CompetitorRead])
def list_competitors(project_id: int, db: Session = Depends(get_db)):
    return competitor_crud.list(db, limit=200, project_id=project_id)


@router.post("/projects/{project_id}/competitors", response_model=CompetitorRead, status_code=201)
def create_competitor(project_id: int, payload: CompetitorCreate, db: Session = Depends(get_db)):
    return competitor_crud.create(db, payload, project_id=project_id)


@router.put("/competitors/{competitor_id}", response_model=CompetitorRead)
def update_competitor(competitor_id: int, payload: CompetitorUpdate, db: Session = Depends(get_db)):
    return competitor_crud.update(db, competitor_id, payload)


@router.delete("/competitors/{competitor_id}", status_code=204)
def delete_competitor(competitor_id: int, db: Session = Depends(get_db)):
    competitor_crud.delete(db, competitor_id)


@router.post("/competitors/{competitor_id}/pages", response_model=CompetitorPageRead, status_code=201)
def register_competitor_page(competitor_id: int, payload: CompetitorPageCreate, db: Session = Depends(get_db)):
    """Registers a competitor page for later analysis. The actual fetch +
    LLM comparison (`POST /competitor-pages/{id}/analyze`) is an AI job,
    added in Sprint 3.
    """
    competitor_crud.get(db, competitor_id)
    return competitor_page_crud.create(db, payload, competitor_id=competitor_id)


@router.get("/target-pages/{target_page_id}/content-gaps", response_model=list[ContentGapRead])
def list_content_gaps(target_page_id: int, db: Session = Depends(get_db)):
    return content_gap_crud.list(db, limit=200, target_page_id=target_page_id)


@router.post("/content-gaps/{gap_id}/ignore", response_model=ContentGapRead)
def ignore_content_gap(gap_id: int, db: Session = Depends(get_db)):
    return content_gap_crud.update(db, gap_id, ContentGapUpdate(status=GapStatus.IGNORED))
