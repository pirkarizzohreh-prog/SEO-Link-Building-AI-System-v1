from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.keyword import Keyword
from app.models.target_page import TargetPage
from app.schemas.target_page import (
    KeywordCreate,
    KeywordRead,
    TargetPageCreate,
    TargetPageRead,
    TargetPageUpdate,
)
from app.utils.crud import CRUDBase

router = APIRouter(tags=["Target Pages"])
crud = CRUDBase(TargetPage)
keyword_crud = CRUDBase(Keyword)


@router.post("/projects/{project_id}/target-pages", response_model=TargetPageRead, status_code=201)
def create_target_page(project_id: int, payload: TargetPageCreate, db: Session = Depends(get_db)):
    return crud.create(db, payload, project_id=project_id)


@router.get("/target-pages/{target_page_id}", response_model=TargetPageRead)
def get_target_page(target_page_id: int, db: Session = Depends(get_db)):
    return crud.get(db, target_page_id)


@router.put("/target-pages/{target_page_id}", response_model=TargetPageRead)
def update_target_page(target_page_id: int, payload: TargetPageUpdate, db: Session = Depends(get_db)):
    return crud.update(db, target_page_id, payload)


@router.delete("/target-pages/{target_page_id}", status_code=204)
def delete_target_page(target_page_id: int, db: Session = Depends(get_db)):
    crud.delete(db, target_page_id)


@router.get("/target-pages/{target_page_id}/keywords", response_model=list[KeywordRead])
def list_keywords(target_page_id: int, db: Session = Depends(get_db)):
    crud.get(db, target_page_id)
    return keyword_crud.list(db, limit=500, target_page_id=target_page_id)


@router.post("/target-pages/{target_page_id}/keywords", response_model=KeywordRead, status_code=201)
def create_keyword(target_page_id: int, payload: KeywordCreate, db: Session = Depends(get_db)):
    crud.get(db, target_page_id)
    return keyword_crud.create(db, payload, target_page_id=target_page_id)
