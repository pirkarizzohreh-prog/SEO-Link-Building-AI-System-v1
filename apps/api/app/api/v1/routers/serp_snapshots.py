from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.serp_snapshot import SerpSnapshot
from app.schemas.competitor_intel import SerpSnapshotCreate, SerpSnapshotRead
from app.utils.crud import CRUDBase

router = APIRouter(tags=["SERP Snapshots"])
crud = CRUDBase(SerpSnapshot)


@router.get("/target-pages/{target_page_id}/serp-snapshots", response_model=list[SerpSnapshotRead])
def list_serp_snapshots(target_page_id: int, keyword: str | None = None, db: Session = Depends(get_db)):
    return crud.list(db, limit=200, target_page_id=target_page_id, keyword=keyword)


@router.post("/target-pages/{target_page_id}/serp-snapshots", response_model=SerpSnapshotRead, status_code=201)
def create_serp_snapshot(target_page_id: int, payload: SerpSnapshotCreate, db: Session = Depends(get_db)):
    return crud.create(db, payload, target_page_id=target_page_id)
