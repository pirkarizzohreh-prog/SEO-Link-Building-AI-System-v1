from __future__ import annotations

from pydantic import BaseModel


class ProjectReport(BaseModel):
    project_id: int
    project_name: str
    total_target_pages: int
    total_campaigns: int
    total_links_built: int
    pages_covered: int


class CampaignReport(BaseModel):
    campaign_id: int
    campaign_name: str
    anchor_distribution_target: dict[str, float]
    anchor_distribution_actual: dict[str, int]
    published_urls: list[str]
    total_articles: int
    audited_articles: int
    audit_success_rate: float | None


class StageStat(BaseModel):
    avg_hours: float
    sample_count: int


class PipelineStats(BaseModel):
    campaign_id: int
    campaign_name: str
    stages: dict[str, StageStat]
