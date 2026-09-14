from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.content_gap import GapStatus, GapType
from app.models.serp_snapshot import SearchEngine, SerpSource


class CompetitorBase(BaseModel):
    name: str
    website_url: str
    notes: str | None = None


class CompetitorCreate(CompetitorBase):
    pass


class CompetitorUpdate(BaseModel):
    name: str | None = None
    website_url: str | None = None
    notes: str | None = None


class CompetitorRead(CompetitorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    created_at: datetime


class CompetitorPageCreate(BaseModel):
    url: str
    target_page_id: int | None = None


class CompetitorPageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    competitor_id: int
    target_page_id: int | None
    source_serp_snapshot_id: int | None
    url: str
    fetched_title: str | None
    fetched_headings: list | None
    fetched_word_count: int | None
    top_keywords: list | None
    analyzed_at: datetime | None
    created_at: datetime


class ContentGapRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    target_page_id: int
    gap_topic: str
    gap_type: GapType
    source_competitor_page_id: int | None
    status: GapStatus
    created_at: datetime


class ContentGapUpdate(BaseModel):
    status: GapStatus


class SerpSnapshotCreate(BaseModel):
    keyword: str
    search_engine: SearchEngine = SearchEngine.GOOGLE
    results: list[dict]
    source: SerpSource = SerpSource.MANUAL
    fetched_at: datetime


class SerpSnapshotRead(SerpSnapshotCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    target_page_id: int
    created_at: datetime
