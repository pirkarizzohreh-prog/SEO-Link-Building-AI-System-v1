from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.article import ArticleStatus
from app.models.publication import PublicationMethod, PublicationStatus


class ArticleBase(BaseModel):
    target_page_id: int
    anchor_id: int
    topic_id: int | None = None
    content_brief_id: int | None = None
    blog_platform_id: int | None = None
    title: str
    content: str | None = None


class ArticleCreate(ArticleBase):
    """Manual article creation, for testing / fallback. AI-generated
    articles come from the Article Writer agent job (Sprint 3); the SEO
    Auditor (Sprint 4) and Human Approval Layer (Sprint 2) endpoints that
    move status/human_approved forward are added in later sprints.
    """

    pass


class ArticleUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    blog_platform_id: int | None = None


class ArticleRead(ArticleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    campaign_id: int
    word_count: int | None = None
    seo_score: float | None = None
    status: ArticleStatus
    human_approved: bool
    human_approved_by: int | None = None
    human_approved_at: datetime | None = None
    published_url: str | None = None
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class SeoAuditResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    article_id: int
    check_name: str
    passed: bool
    score: float | None = None
    details: str | None = None
    created_at: datetime


class PublishPackage(BaseModel):
    """Ready-to-copy payload for the MVP's manual publish flow — see
    docs/AI_WORKFLOW.md ("Publication Manager", version one).
    """

    article_id: int
    suggested_blog_platform_id: int | None = None
    suggested_blog_platform_name: str | None = None
    title: str
    content: str | None = None
    anchor_text: str
    target_url: str
    category: str | None = None


class PublicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    article_id: int
    blog_platform_id: int
    method: PublicationMethod
    status: PublicationStatus
    published_url: str | None = None
    notes: str | None = None
    published_at: datetime
