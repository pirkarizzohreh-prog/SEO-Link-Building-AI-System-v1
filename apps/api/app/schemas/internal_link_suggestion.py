from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.internal_link_suggestion import InternalLinkStatus


class InternalLinkSuggestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    source_target_page_id: int
    destination_target_page_id: int
    suggested_anchor: str
    reason: str | None = None
    status: InternalLinkStatus
    created_at: datetime


class InternalLinkSuggestionStatusUpdate(BaseModel):
    status: InternalLinkStatus
