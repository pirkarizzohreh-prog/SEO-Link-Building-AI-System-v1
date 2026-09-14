from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.content_brief import BriefStatus


class ContentBriefBase(BaseModel):
    target_page_id: int
    content_template_id: int | None = None
    outline: list[dict]
    target_word_count: int = 1200
    keywords_to_include: list[str] | None = None
    must_include_points: list[str] | None = None
    tone: str | None = None
    source_content_gap_ids: list[int] | None = None


class ContentBriefCreate(ContentBriefBase):
    """Manual brief creation. AI-generated briefs come from the Content
    Brief Generator agent job (Sprint 3).
    """

    pass


class ContentBriefUpdate(BaseModel):
    outline: list[dict] | None = None
    target_word_count: int | None = None
    keywords_to_include: list[str] | None = None
    must_include_points: list[str] | None = None
    tone: str | None = None
    status: BriefStatus | None = None


class ContentBriefRead(ContentBriefBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    topic_id: int
    status: BriefStatus
    created_at: datetime
