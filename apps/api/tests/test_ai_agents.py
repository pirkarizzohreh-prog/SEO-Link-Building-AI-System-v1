"""Unit tests for each agent's run() function, against a FakeLLMClient —
no network, no API keys. These call the agent directly (not through
app.jobs.handlers.process_job), so a job row is built manually here just
to carry reference_table/reference_id/prompt_template_* like the real
worker would give it.
"""

from __future__ import annotations

import json

import pytest

from app.ai.agents import brief_agent, competitor_intel_agent, internal_link_agent, keyword_agent, topic_agent, writer_agent
from app.ai.safe_fetch import UnsafeUrlError, fetch_html
from app.models.ai_job import AiJob, JobStatus, JobType
from app.models.anchor import Anchor, AnchorType
from app.models.competitor import Competitor
from app.models.competitor_page import CompetitorPage
from app.models.content_brief import BriefStatus, ContentBrief
from app.models.content_gap import ContentGap, GapStatus, GapType
from app.models.target_page import TargetPage
from app.models.topic import GeneratedBy, Topic, TopicStatus
from tests.fake_llm_client import FakeLLMClient


def _make_job(job_type: JobType, reference_table: str, reference_id: int) -> AiJob:
    return AiJob(job_type=job_type, reference_table=reference_table, reference_id=reference_id, status=JobStatus.RUNNING)


def test_keyword_agent_creates_keywords(db_session, db_campaign):
    job = _make_job(JobType.KEYWORD_INTEL, "campaigns", db_campaign.id)
    client = FakeLLMClient(
        [json.dumps({"related_keywords": [{"keyword": "industrial wastewater", "type": "related"}]})]
    )

    result = keyword_agent.run(db_session, job, client)

    assert result.output_payload["created_keywords"] == ["industrial wastewater"]
    assert result.tokens_used == 100
    assert job.prompt_template_id is not None  # seeded lazily on first use


def test_topic_agent_creates_topics_and_consumes_gaps(db_session, db_campaign, db_target_page):
    gap = ContentGap(target_page_id=db_target_page.id, gap_topic="BOD/COD control", gap_type=GapType.TOPIC, status=GapStatus.NEW)
    db_session.add(gap)
    db_session.commit()

    job = _make_job(JobType.TOPIC_GEN, "campaigns", db_campaign.id)
    client = FakeLLMClient(
        [json.dumps({"topics": [{"title": "Managing wastewater in food plants", "rationale": "educational"}]})]
    )

    result = topic_agent.run(db_session, job, client)

    topics = db_session.query(Topic).filter(Topic.campaign_id == db_campaign.id).all()
    assert len(topics) == 1
    assert topics[0].generated_by == GeneratedBy.AI
    assert topics[0].status == TopicStatus.SUGGESTED
    assert result.output_payload["created_topics"] == ["Managing wastewater in food plants"]

    db_session.refresh(gap)
    assert gap.status == GapStatus.USED_IN_TOPIC


def test_brief_agent_creates_brief_and_rejects_duplicate(db_session, db_campaign, db_target_page):
    topic = Topic(campaign_id=db_campaign.id, title="Topic A", status=TopicStatus.SELECTED)
    db_session.add(topic)
    db_session.commit()

    job = _make_job(JobType.BRIEF_GENERATION, "topics", topic.id)
    client = FakeLLMClient(
        [
            json.dumps(
                {
                    "outline": [{"heading": "Intro", "level": "h2", "key_points": ["why it matters"]}],
                    "target_word_count": 1300,
                    "tone": "technical",
                }
            )
        ]
    )

    result = brief_agent.run(db_session, job, client)
    db_session.commit()

    brief = db_session.query(ContentBrief).filter(ContentBrief.topic_id == topic.id).one()
    assert brief.target_word_count == 1300
    assert brief.status == BriefStatus.DRAFT
    assert result.output_payload["content_brief_id"] == brief.id

    # A second attempt for the same topic must fail loudly, not silently overwrite.
    job2 = _make_job(JobType.BRIEF_GENERATION, "topics", topic.id)
    with pytest.raises(ValueError, match="already has a content brief"):
        brief_agent.run(db_session, job2, FakeLLMClient(["{}"]))


def test_writer_agent_picks_anchor_and_creates_article(db_session, db_campaign, db_target_page):
    topic = Topic(campaign_id=db_campaign.id, title="Topic A", status=TopicStatus.SELECTED)
    db_session.add(topic)
    db_session.flush()
    brief = ContentBrief(
        topic_id=topic.id,
        target_page_id=db_target_page.id,
        outline=[{"heading": "Intro", "level": "h2", "key_points": ["x"]}],
        target_word_count=50,
        status=BriefStatus.APPROVED,
    )
    exact_anchor = Anchor(target_page_id=db_target_page.id, anchor_text="exact match", anchor_type=AnchorType.EXACT)
    brand_anchor = Anchor(target_page_id=db_target_page.id, anchor_text="brand anchor", anchor_type=AnchorType.BRAND)
    db_session.add_all([brief, exact_anchor, brand_anchor])
    db_session.commit()

    job = _make_job(JobType.ARTICLE_WRITE, "content_briefs", brief.id)
    client = FakeLLMClient(["## Intro\nThis is a great article about wastewater treatment. " * 5])

    result = writer_agent.run(db_session, job, client)
    db_session.commit()

    from app.models.article import Article

    article = db_session.get(Article, result.output_payload["article_id"])
    assert article.status.value == "draft"
    assert article.content
    assert article.anchor_id in (exact_anchor.id, brand_anchor.id)

    picked_anchor = db_session.get(Anchor, article.anchor_id)
    assert picked_anchor.usage_count == 1


def test_writer_agent_rejects_unapproved_brief(db_session, db_campaign, db_target_page):
    topic = Topic(campaign_id=db_campaign.id, title="Topic A", status=TopicStatus.SELECTED)
    db_session.add(topic)
    db_session.flush()
    brief = ContentBrief(
        topic_id=topic.id, target_page_id=db_target_page.id, outline=[], status=BriefStatus.DRAFT
    )
    db_session.add(brief)
    db_session.commit()

    job = _make_job(JobType.ARTICLE_WRITE, "content_briefs", brief.id)
    with pytest.raises(ValueError, match="not approved"):
        writer_agent.run(db_session, job, FakeLLMClient(["text"]))


def test_internal_link_agent_filters_invalid_ids(db_session, db_project):
    page_a = TargetPage(project_id=db_project.id, title="A", url="https://a", main_keyword="a")
    page_b = TargetPage(project_id=db_project.id, title="B", url="https://b", main_keyword="b")
    db_session.add_all([page_a, page_b])
    db_session.commit()

    job = _make_job(JobType.INTERNAL_LINK_SUGGESTION, "projects", db_project.id)
    client = FakeLLMClient(
        [
            json.dumps(
                {
                    "suggestions": [
                        {"source_id": page_a.id, "destination_id": page_b.id, "suggested_anchor": "b page", "reason": "related"},
                        {"source_id": page_a.id, "destination_id": page_a.id, "suggested_anchor": "self", "reason": "bad"},
                        {"source_id": 999999, "destination_id": page_b.id, "suggested_anchor": "bad id", "reason": "bad"},
                    ]
                }
            )
        ]
    )

    result = internal_link_agent.run(db_session, job, client)

    assert len(result.output_payload["created_suggestions"]) == 1


def test_internal_link_agent_noop_with_one_page(db_session, db_project, db_target_page):
    job = _make_job(JobType.INTERNAL_LINK_SUGGESTION, "projects", db_project.id)
    result = internal_link_agent.run(db_session, job, FakeLLMClient([]))
    assert result.output_payload["created_suggestions"] == []


def test_safe_fetch_blocks_private_addresses():
    with pytest.raises(UnsafeUrlError):
        fetch_html("http://127.0.0.1/admin")
    with pytest.raises(UnsafeUrlError):
        fetch_html("http://localhost:8000/")
    with pytest.raises(UnsafeUrlError):
        fetch_html("ftp://example.com/")


def test_competitor_intel_agent(db_session, db_project, db_target_page, monkeypatch):
    competitor = Competitor(project_id=db_project.id, name="Competitor A", website_url="https://competitor-a.example.com")
    db_session.add(competitor)
    db_session.flush()
    page = CompetitorPage(competitor_id=competitor.id, target_page_id=db_target_page.id, url="https://competitor-a.example.com/blog")
    db_session.add(page)
    db_session.commit()

    fake_html = "<html><head><title>Great wastewater guide</title></head><body><h2>BOD and COD basics</h2><p>industrial wastewater treatment plants</p></body></html>"
    monkeypatch.setattr(competitor_intel_agent, "fetch_html", lambda url: fake_html)

    job = _make_job(JobType.COMPETITOR_ANALYSIS, "competitor_pages", page.id)
    client = FakeLLMClient([json.dumps({"gaps": [{"gap_topic": "BOD and COD basics", "gap_type": "heading"}]})])

    result = competitor_intel_agent.run(db_session, job, client)
    db_session.commit()

    db_session.refresh(page)
    assert page.fetched_title == "Great wastewater guide"
    assert "BOD and COD basics" in page.fetched_headings

    gaps = db_session.query(ContentGap).filter(ContentGap.target_page_id == db_target_page.id).all()
    assert len(gaps) == 1
    assert gaps[0].gap_type == GapType.HEADING
    assert result.output_payload["created_content_gaps"] == ["BOD and COD basics"]


def test_competitor_intel_agent_requires_linked_target_page(db_session, db_project):
    competitor = Competitor(project_id=db_project.id, name="C", website_url="https://c.example.com")
    db_session.add(competitor)
    db_session.flush()
    page = CompetitorPage(competitor_id=competitor.id, url="https://c.example.com/blog")
    db_session.add(page)
    db_session.commit()

    job = _make_job(JobType.COMPETITOR_ANALYSIS, "competitor_pages", page.id)
    with pytest.raises(ValueError, match="no linked target_page_id"):
        competitor_intel_agent.run(db_session, job, FakeLLMClient(["{}"]))
