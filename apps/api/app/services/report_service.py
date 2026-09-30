"""Report Manager — docs/AI_WORKFLOW.md ("مرحله ۱۰ — Report Manager"),
docs/API_SPEC.md ("Reports"). Pure read/aggregation, no AI involved.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.anchor import Anchor, AnchorType
from app.models.anchor_usage_log import AnchorUsageLog
from app.models.article import Article, ArticleStatus
from app.models.campaign import Campaign
from app.models.content_brief import ContentBrief
from app.models.content_status_history import ContentStatusHistory, PipelineStage
from app.models.project import Project
from app.models.topic import Topic
from app.services.rules_service import resolve_link_placement_rule

# Statuses an article only reaches once the SEO Auditor has run on it at
# least once (docs/AI_WORKFLOW.md, Stage: Audit's three possible article
# statuses plus whatever it moved on to since).
_AUDITED_STATUSES = {
    ArticleStatus.REVIEWED,
    ArticleStatus.NEEDS_HUMAN_REVIEW,
    ArticleStatus.APPROVED,
    ArticleStatus.PUBLISHED,
}
_AUDIT_PASSED_STATUSES = {ArticleStatus.REVIEWED, ArticleStatus.APPROVED, ArticleStatus.PUBLISHED}

# entity_table -> model, so pipeline-stats can look up the timestamp an
# entity started existing in (used as the "stage start" for whichever
# stage's history row has no earlier row of its own to measure from).
_ENTITY_MODELS: dict[str, type] = {
    "topics": Topic,
    "content_briefs": ContentBrief,
    "articles": Article,
}


def build_project_report(db: Session, project: Project) -> dict:
    campaign_ids = [c.id for c in db.query(Campaign.id).filter(Campaign.project_id == project.id)]
    articles = db.query(Article).filter(Article.campaign_id.in_(campaign_ids)).all() if campaign_ids else []
    published = [a for a in articles if a.status == ArticleStatus.PUBLISHED]

    return {
        "project_id": project.id,
        "project_name": project.project_name,
        "total_target_pages": len(project.target_pages),
        "total_campaigns": len(campaign_ids),
        "total_links_built": len(published),
        "pages_covered": len({a.target_page_id for a in published}),
    }


def build_campaign_report(db: Session, campaign: Campaign) -> dict:
    articles = db.query(Article).filter(Article.campaign_id == campaign.id).all()
    published = [a for a in articles if a.status == ArticleStatus.PUBLISHED]

    anchor_types_used = [
        row[0]
        for row in db.query(AnchorUsageLog.anchor_type)
        .join(Anchor, AnchorUsageLog.anchor_id == Anchor.id)
        .join(Article, AnchorUsageLog.article_id == Article.id)
        .filter(Article.campaign_id == campaign.id)
        .all()
    ]
    usage_counts = Counter(anchor_types_used)
    actual_counts = {t.value: usage_counts.get(t, 0) for t in AnchorType}

    rule = resolve_link_placement_rule(db, campaign_id=campaign.id)

    audited = [a for a in articles if a.status in _AUDITED_STATUSES]
    passed = [a for a in audited if a.status in _AUDIT_PASSED_STATUSES]
    audit_success_rate = round(len(passed) / len(audited) * 100, 2) if audited else None

    return {
        "campaign_id": campaign.id,
        "campaign_name": campaign.name,
        "anchor_distribution_target": rule.anchor_distribution,
        "anchor_distribution_actual": actual_counts,
        "published_urls": [a.published_url for a in published if a.published_url],
        "total_articles": len(articles),
        "audited_articles": len(audited),
        "audit_success_rate": audit_success_rate,
    }


def _entity_created_at(db: Session, entity_table: str, entity_id: int) -> datetime | None:
    model = _ENTITY_MODELS.get(entity_table)
    if model is None:
        return None
    entity = db.get(model, entity_id)
    return entity.created_at if entity is not None else None


def build_pipeline_stats(db: Session, campaign: Campaign) -> dict:
    """Average time spent in each of the 6 stages, per docs/AI_WORKFLOW.md
    ("Pipeline Bottleneck Report"): for every entity that passed through a
    stage, the time spent in that stage is measured from the previous
    `content_status_history` row for that same entity (or the entity's own
    `created_at`, if this is its first recorded transition) to the row that
    marks the stage as done.
    """
    entities: list[tuple[str, int]] = [("topics", t.id) for t in campaign.topics]
    entities += [("content_briefs", t.brief.id) for t in campaign.topics if t.brief is not None]
    entities += [("articles", a.id) for a in campaign.articles]

    durations_by_stage: dict[PipelineStage, list[float]] = {}
    for entity_table, entity_id in entities:
        rows = (
            db.query(ContentStatusHistory)
            .filter(
                ContentStatusHistory.entity_table == entity_table,
                ContentStatusHistory.entity_id == entity_id,
            )
            .order_by(ContentStatusHistory.created_at.asc())
            .all()
        )
        prev_time = _entity_created_at(db, entity_table, entity_id)
        for row in rows:
            if prev_time is not None:
                hours = (row.created_at - prev_time).total_seconds() / 3600
                durations_by_stage.setdefault(row.stage, []).append(hours)
            prev_time = row.created_at

    stats = {}
    for stage in PipelineStage:
        samples = durations_by_stage.get(stage)
        if not samples:
            continue
        stats[stage.value] = {
            "avg_hours": round(sum(samples) / len(samples), 2),
            "sample_count": len(samples),
        }

    return {"campaign_id": campaign.id, "campaign_name": campaign.name, "stages": stats}
