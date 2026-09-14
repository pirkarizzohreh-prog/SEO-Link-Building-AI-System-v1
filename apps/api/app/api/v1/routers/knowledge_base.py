from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.project import Project
from app.models.project_knowledge_base import ProjectKnowledgeBase
from app.schemas.project import ProjectKnowledgeBaseRead, ProjectKnowledgeBaseUpsert

router = APIRouter(tags=["Project Knowledge Base"])


def _get_project_or_404(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found")
    return project


@router.get("/projects/{project_id}/knowledge-base", response_model=ProjectKnowledgeBaseRead)
def get_knowledge_base(project_id: int, db: Session = Depends(get_db)):
    _get_project_or_404(db, project_id)
    kb = db.query(ProjectKnowledgeBase).filter(ProjectKnowledgeBase.project_id == project_id).first()
    if kb is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No knowledge base set for this project yet",
        )
    return kb


@router.put("/projects/{project_id}/knowledge-base", response_model=ProjectKnowledgeBaseRead)
def upsert_knowledge_base(project_id: int, payload: ProjectKnowledgeBaseUpsert, db: Session = Depends(get_db)):
    _get_project_or_404(db, project_id)
    kb = db.query(ProjectKnowledgeBase).filter(ProjectKnowledgeBase.project_id == project_id).first()
    data = payload.model_dump()
    if kb is None:
        kb = ProjectKnowledgeBase(project_id=project_id, **data)
        db.add(kb)
    else:
        for field, value in data.items():
            setattr(kb, field, value)
    db.commit()
    db.refresh(kb)
    return kb
