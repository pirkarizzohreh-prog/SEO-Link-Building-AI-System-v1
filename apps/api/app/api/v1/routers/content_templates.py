from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.content_template import ContentTemplate
from app.models.prompt_template import PromptAgentType, PromptTemplate
from app.schemas.content_template import (
    ContentTemplateCreate,
    ContentTemplateRead,
    ContentTemplateUpdate,
    PromptTemplateCreate,
    PromptTemplateRead,
)
from app.utils.crud import CRUDBase

content_template_crud = CRUDBase(ContentTemplate)

content_templates_router = APIRouter(prefix="/content-templates", tags=["Content Templates"])
prompt_templates_router = APIRouter(prefix="/prompt-templates", tags=["Prompt Templates"])


@content_templates_router.get("", response_model=list[ContentTemplateRead])
def list_content_templates(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return content_template_crud.list(db, skip=skip, limit=limit)


@content_templates_router.post("", response_model=ContentTemplateRead, status_code=201)
def create_content_template(payload: ContentTemplateCreate, db: Session = Depends(get_db)):
    return content_template_crud.create(db, payload)


@content_templates_router.put("/{template_id}", response_model=ContentTemplateRead)
def update_content_template(template_id: int, payload: ContentTemplateUpdate, db: Session = Depends(get_db)):
    return content_template_crud.update(db, template_id, payload)


@content_templates_router.delete("/{template_id}", status_code=204)
def delete_content_template(template_id: int, db: Session = Depends(get_db)):
    content_template_crud.delete(db, template_id)


@prompt_templates_router.get("", response_model=list[PromptTemplateRead])
def list_prompt_templates(agent_type: PromptAgentType | None = None, db: Session = Depends(get_db)):
    stmt_filters = {"agent_type": agent_type} if agent_type else {}
    return CRUDBase(PromptTemplate).list(db, limit=200, **stmt_filters)


@prompt_templates_router.get("/{agent_type}/active", response_model=PromptTemplateRead)
def get_active_prompt_template(agent_type: PromptAgentType, db: Session = Depends(get_db)):
    prompt = (
        db.query(PromptTemplate)
        .filter(PromptTemplate.agent_type == agent_type, PromptTemplate.is_active.is_(True))
        .order_by(PromptTemplate.version.desc())
        .first()
    )
    if prompt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active prompt template for agent_type={agent_type.value}",
        )
    return prompt


@prompt_templates_router.post("", response_model=PromptTemplateRead, status_code=201)
def create_prompt_template_version(payload: PromptTemplateCreate, db: Session = Depends(get_db)):
    """Register a new prompt version for an agent_type. The previous active
    version (if any) is deactivated, never overwritten — see
    docs/DATABASE_SCHEMA.md (`prompt_templates` is append-only).
    """
    current = (
        db.query(PromptTemplate)
        .filter(PromptTemplate.agent_type == payload.agent_type, PromptTemplate.is_active.is_(True))
        .first()
    )
    next_version = 1
    if current is not None:
        next_version = current.version + 1
        current.is_active = False

    new_prompt = PromptTemplate(
        agent_type=payload.agent_type,
        name=payload.name,
        template_text=payload.template_text,
        created_by=payload.created_by,
        version=next_version,
        is_active=True,
    )
    db.add(new_prompt)
    db.commit()
    db.refresh(new_prompt)
    return new_prompt
