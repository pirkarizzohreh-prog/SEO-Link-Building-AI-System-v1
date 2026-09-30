"""Unit tests for the SEO Auditor Agent — docs/AI_WORKFLOW.md, Stage:
Audit. Exercises the pass-on-first-try, retry-then-pass, and
exhaust-retries-then-needs_human_review paths against a FakeLLMClient.
"""

from __future__ import annotations

import json

from app.ai.agents import auditor_agent
from app.models.ai_job import AiJob, JobStatus, JobType
from app.models.anchor import Anchor, AnchorType
from app.models.article import Article, ArticleStatus
from app.models.content_brief import BriefStatus, ContentBrief
from app.models.content_status_history import ContentStatusHistory, PipelineStage
from app.models.seo_audit_result import SeoAuditResult
from app.models.topic import Topic, TopicStatus
from tests.fake_llm_client import FakeLLMClient

TARGET_URL = "https://aebwater.com/product/food-wastewater-package/"
ANCHOR_TEXT = "food industry wastewater package"
GOOD_TONE_JSON = json.dumps({"tone_score": 90, "forbidden_words_found": [], "reason": "لحن مناسب است"})


def _make_job(reference_id: int) -> AiJob:
    return AiJob(job_type=JobType.SEO_AUDIT, reference_table="articles", reference_id=reference_id, status=JobStatus.RUNNING)


def _make_article(db_session, db_campaign, db_target_page, *, content: str, target_word_count: int = 10) -> Article:
    topic = Topic(campaign_id=db_campaign.id, title="Topic A", status=TopicStatus.SELECTED)
    db_session.add(topic)
    db_session.flush()
    brief = ContentBrief(
        topic_id=topic.id,
        target_page_id=db_target_page.id,
        outline=[{"heading": "Intro", "level": "h2", "key_points": ["x"]}],
        target_word_count=target_word_count,
        status=BriefStatus.APPROVED,
    )
    anchor = Anchor(target_page_id=db_target_page.id, anchor_text=ANCHOR_TEXT, anchor_type=AnchorType.EXACT)
    db_session.add_all([brief, anchor])
    db_session.flush()

    article = Article(
        campaign_id=db_campaign.id,
        topic_id=topic.id,
        content_brief_id=brief.id,
        target_page_id=db_target_page.id,
        anchor_id=anchor.id,
        title=topic.title,
        content=content,
        word_count=len(content.split()),
        status=ArticleStatus.IN_AUDIT,
    )
    db_session.add(article)
    db_session.commit()
    return article


def _passing_content() -> str:
    filler = "این محصول عالی برای تصفیه فاضلاب صنایع غذایی است. " * 5
    return f"## Intro\n[{ANCHOR_TEXT}]({TARGET_URL}) {filler}"


def _failing_content_no_link() -> str:
    return "## Intro\nاین متن هیچ لینکی به صفحه‌ی هدف ندارد و کوتاه است."


def test_auditor_passes_on_first_try(db_session, db_campaign, db_target_page):
    article = _make_article(db_session, db_campaign, db_target_page, content=_passing_content())
    job = _make_job(article.id)
    client = FakeLLMClient([GOOD_TONE_JSON])

    result = auditor_agent.run(db_session, job, client)
    db_session.commit()
    db_session.refresh(article)

    assert result.output_payload["passed"] is True
    assert article.status == ArticleStatus.REVIEWED
    assert article.audit_retry_count == 0

    results = db_session.query(SeoAuditResult).filter(SeoAuditResult.article_id == article.id).all()
    check_names = {r.check_name for r in results}
    assert {"word_count", "link_presence", "url_anchor_correctness", "link_position", "outbound_link_count"} <= check_names
    assert all(r.passed for r in results if r.check_name in {"word_count", "link_presence", "url_anchor_correctness"})

    history = (
        db_session.query(ContentStatusHistory)
        .filter(ContentStatusHistory.entity_table == "articles", ContentStatusHistory.entity_id == article.id)
        .filter(ContentStatusHistory.stage == PipelineStage.AUDIT)
        .all()
    )
    assert len(history) == 1
    assert history[0].to_status == "reviewed"


def test_auditor_retries_then_passes(db_session, db_campaign, db_target_page):
    article = _make_article(db_session, db_campaign, db_target_page, content=_failing_content_no_link())
    job = _make_job(article.id)
    client = FakeLLMClient([_passing_content(), GOOD_TONE_JSON])

    result = auditor_agent.run(db_session, job, client)
    db_session.commit()
    db_session.refresh(article)

    assert result.output_payload["passed"] is True
    assert article.status == ArticleStatus.REVIEWED
    assert article.audit_retry_count == 1
    assert ANCHOR_TEXT in article.content


def test_auditor_exhausts_retries_then_needs_human_review(db_session, db_campaign, db_target_page):
    article = _make_article(db_session, db_campaign, db_target_page, content=_failing_content_no_link())
    job = _make_job(article.id)
    client = FakeLLMClient([_failing_content_no_link(), _failing_content_no_link(), GOOD_TONE_JSON])

    result = auditor_agent.run(db_session, job, client)
    db_session.commit()
    db_session.refresh(article)

    assert result.output_payload["passed"] is False
    assert article.status == ArticleStatus.NEEDS_HUMAN_REVIEW
    assert article.audit_retry_count == auditor_agent.MAX_AUDIT_RETRIES

    history = (
        db_session.query(ContentStatusHistory)
        .filter(ContentStatusHistory.entity_table == "articles", ContentStatusHistory.entity_id == article.id)
        .filter(ContentStatusHistory.stage == PipelineStage.AUDIT)
        .all()
    )
    assert len(history) == 1
    assert history[0].to_status == "needs_human_review"
