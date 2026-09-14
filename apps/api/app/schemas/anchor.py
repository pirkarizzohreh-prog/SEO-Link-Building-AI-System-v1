from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.anchor import AnchorType


class AnchorBase(BaseModel):
    anchor_text: str
    anchor_type: AnchorType
    usage_limit: int | None = None
    is_active: bool = True


class AnchorCreate(AnchorBase):
    pass


class AnchorUpdate(BaseModel):
    anchor_text: str | None = None
    anchor_type: AnchorType | None = None
    usage_limit: int | None = None
    is_active: bool | None = None


class AnchorRead(AnchorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    target_page_id: int
    usage_count: int
    created_at: datetime


class AnchorDistribution(BaseModel):
    target_page_id: int
    window_size: int
    target_ratio: dict[str, float]
    actual_counts: dict[str, int]
    actual_ratio: dict[str, float]
