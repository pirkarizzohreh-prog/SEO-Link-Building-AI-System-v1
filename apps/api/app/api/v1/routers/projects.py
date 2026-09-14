from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.project import Project, ProjectStatus
from app.models.target_page import TargetPage
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.schemas.target_page import TargetPageRead
from app.utils.crud import CRUDBase

router = APIRouter(prefix="/projects", tags=["Projects"])
crud = CRUDBase(Project)


@router.get("", response_model=list[ProjectRead])
def list_projects(
    skip: int = 0, limit: int = 50, status: ProjectStatus | None = None, db: Session = Depends(get_db)
):
    return crud.list(db, skip=skip, limit=limit, status=status)


@router.post("", response_model=ProjectRead, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    return crud.create(db, payload)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, db: Session = Depends(get_db)):
    return crud.get(db, project_id)


@router.put("/{project_id}", response_model=ProjectRead)
def update_project(project_id: int, payload: ProjectUpdate, db: Session = Depends(get_db)):
    return crud.update(db, project_id, payload)


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    crud.delete(db, project_id)


@router.get("/{project_id}/target-pages", response_model=list[TargetPageRead])
def list_project_target_pages(project_id: int, db: Session = Depends(get_db)):
    crud.get(db, project_id)  # 404 if the project doesn't exist
    return db.query(TargetPage).filter(TargetPage.project_id == project_id).all()
