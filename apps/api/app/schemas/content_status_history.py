from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.content_status_history import ActorType, PipelineStage


class ContentStatusHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_table: str
    entity_id: int
    stage: PipelineStage
    from_status: str | None
    to_status: str
    actor_type: ActorType
    actor_id: int | None
    note: str | None
    created_at: datetime
