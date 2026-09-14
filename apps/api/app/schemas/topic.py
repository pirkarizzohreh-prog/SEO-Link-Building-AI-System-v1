from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.topic import GeneratedBy, TopicStatus


class TopicBase(BaseModel):
    title: str
    rationale: str | None = None


class TopicCreate(TopicBase):
    """Manual topic creation. AI-generated topics are written by the
    Topic Generator agent job (Sprint 3), not through this endpoint.
    """

    pass


class TopicUpdate(BaseModel):
    title: str | None = None
    rationale: str | None = None
    status: TopicStatus | None = None


class TopicRead(TopicBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    campaign_id: int
    status: TopicStatus
    generated_by: GeneratedBy
    created_at: datetime
