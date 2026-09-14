from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.campaign import CampaignStatus


class CampaignBase(BaseModel):
    project_id: int
    target_page_id: int
    name: str
    total_links_target: int
    blog_count: int
    duration_days: int
    start_date: date | None = None
    end_date: date | None = None


class CampaignCreate(CampaignBase):
    pass


class CampaignUpdate(BaseModel):
    name: str | None = None
    total_links_target: int | None = None
    blog_count: int | None = None
    duration_days: int | None = None
    status: CampaignStatus | None = None
    start_date: date | None = None
    end_date: date | None = None


class CampaignRead(CampaignBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: CampaignStatus
    created_at: datetime
