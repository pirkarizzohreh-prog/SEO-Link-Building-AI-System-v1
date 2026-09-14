from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import sa_enum
from app.models.mixins import TimestampMixin, UpdatedAtMixin


class ArticleStatus(str, enum.Enum):
    DRAFT = "draft"
    IN_AUDIT = "in_audit"
    REVIEWED = "reviewed"
    NEEDS_HUMAN_REVIEW = "needs_human_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"


class Article(Base, TimestampMixin, UpdatedAtMixin):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    content_brief_id: Mapped[int | None] = mapped_column(
        ForeignKey("content_briefs.id", ondelete="SET NULL"), nullable=True
    )
    target_page_id: Mapped[int] = mapped_column(ForeignKey("target_pages.id", ondelete="CASCADE"))
    anchor_id: Mapped[int] = mapped_column(ForeignKey("anchors.id"))
    blog_platform_id: Mapped[int | None] = mapped_column(
        ForeignKey("blog_platforms.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500))
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    seo_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    status: Mapped[ArticleStatus] = mapped_column(sa_enum(ArticleStatus, "article_status"), default=ArticleStatus.DRAFT)

    # Human Approval Layer — see docs/AI_WORKFLOW.md. `human_approved` must
    # only ever be written by app.services.approval_service (added in
    # Sprint 2, once a current-user identity exists); no router in Sprint 1
    # writes to it.
    human_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    human_approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    human_approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    published_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    campaign: Mapped["Campaign"] = relationship(back_populates="articles")
    topic: Mapped["Topic | None"] = relationship(back_populates="articles")
    content_brief: Mapped["ContentBrief | None"] = relationship(back_populates="articles")
    target_page: Mapped["TargetPage"] = relationship()
    anchor: Mapped["Anchor"] = relationship()
    blog_platform: Mapped["BlogPlatform | None"] = relationship(back_populates="articles")
    seo_audit_results: Mapped[list["SeoAuditResult"]] = relationship(
        back_populates="article", cascade="all, delete-orphan"
    )
    publications: Mapped[list["Publication"]] = relationship(
        back_populates="article", cascade="all, delete-orphan"
    )
    anchor_usage_log: Mapped["AnchorUsageLog | None"] = relationship(back_populates="article", uselist=False)
