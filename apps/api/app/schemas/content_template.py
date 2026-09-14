from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.prompt_template import PromptAgentType


class ContentTemplateBase(BaseModel):
    name: str
    description: str | None = None
    applicable_page_types: list[str] | None = None
    default_outline_skeleton: list | dict | None = None
    default_word_count: int = 1200
    is_active: bool = True


class ContentTemplateCreate(ContentTemplateBase):
    pass


class ContentTemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    applicable_page_types: list[str] | None = None
    default_outline_skeleton: list | dict | None = None
    default_word_count: int | None = None
    is_active: bool | None = None


class ContentTemplateRead(ContentTemplateBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class PromptTemplateCreate(BaseModel):
    agent_type: PromptAgentType
    name: str
    template_text: str
    created_by: int | None = None


class PromptTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_type: PromptAgentType
    name: str
    template_text: str
    version: int
    is_active: bool
    created_by: int | None = None
    created_at: datetime
