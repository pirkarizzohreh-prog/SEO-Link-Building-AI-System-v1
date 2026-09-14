from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.project import ProjectStatus


class ProjectBase(BaseModel):
    project_name: str
    website_url: str
    industry: str | None = None
    description: str | None = None
    status: ProjectStatus = ProjectStatus.ACTIVE


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    project_name: str | None = None
    website_url: str | None = None
    industry: str | None = None
    description: str | None = None
    status: ProjectStatus | None = None


class ProjectRead(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class ProjectKnowledgeBaseUpsert(BaseModel):
    brand_name: str | None = None
    brand_voice_tone: str | None = None
    target_audience: str | None = None
    industry_context: str | None = None
    style_guidelines: str | None = None
    forbidden_words: list[str] | None = None
    mandatory_points: list[str] | None = None
    sample_reference_urls: list[str] | None = None
    custom_rules: dict | None = None


class ProjectKnowledgeBaseRead(ProjectKnowledgeBaseUpsert):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
