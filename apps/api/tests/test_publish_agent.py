"""Unit tests for the automated Publication Manager — docs/AI_WORKFLOW.md
("Stage: Published", نسخه دوم). No real browser: app/ai/agents/
publish_agent.py resolves its publisher via
app.automation.publishers.factory.get_publisher, which these tests
monkeypatch to a FakePublisher — same pattern test_ai_agents.py uses for
competitor_intel_agent's fetch_html.
"""

from __future__ import annotations

from app.ai.agents import publish_agent
from app.automation.publishers.base_publisher import PublishResult
from app.core.crypto import encrypt_secret
from app.models.ai_job import AiJob, JobStatus, JobType
from app.models.article import Article, ArticleStatus
from app.models.blog_platform import BlogPlatform, BlogPlatformStatus
from app.models.content_status_history import ContentStatusHistory, PipelineStage
from app.models.publication import Publication, PublicationStatus
from tests.fake_llm_client import FakeLLMClient
from tests.fake_publisher import FakePublisher


def _make_job(reference_id: int, blog_platform_id: int | None = None) -> AiJob:
    return AiJob(
        job_type=JobType.PUBLISH,
        reference_table="articles",
        reference_id=reference_id,
        status=JobStatus.RUNNING,
        input_payload={"blog_platform_id": blog_platform_id} if blog_platform_id else {},
    )


def _make_blog_platform(db_session, *, with_credentials: bool = True) -> BlogPlatform:
    blog = BlogPlatform(name="Yektablog", url="https://yektablog.net", status=BlogPlatformStatus.ACTIVE)
    if with_credentials:
        blog.username = "guest-poster"
        blog.password_encrypted = encrypt_secret("s3cret")
        blog.login_url = "https://yektablog.net/wp-login.php"
    db_session.add(blog)
    db_session.flush()
    return blog


def _make_approved_article(db_session, db_campaign, db_target_page) -> Article:
    from app.models.anchor import Anchor, AnchorType

    anchor = Anchor(target_page_id=db_target_page.id, anchor_text="wastewater package", anchor_type=AnchorType.EXACT)
    db_session.add(anchor)
    db_session.flush()

    article = Article(
        campaign_id=db_campaign.id,
        target_page_id=db_target_page.id,
        anchor_id=anchor.id,
        title="Managing wastewater in food plants",
        content="## Intro\n[wastewater package](https://aebwater.com) A great article.",
        status=ArticleStatus.APPROVED,
        human_approved=True,
    )
    db_session.add(article)
    db_session.commit()
    return article


def test_publish_agent_success(db_session, db_campaign, db_target_page, monkeypatch):
    blog = _make_blog_platform(db_session)
    article = _make_approved_article(db_session, db_campaign, db_target_page)
    fake = FakePublisher(PublishResult(success=True, published_url="https://yektablog.net/post/1"))
    monkeypatch.setattr(publish_agent, "get_publisher", lambda: fake)

    job = _make_job(article.id, blog.id)
    result = publish_agent.run(db_session, job, FakeLLMClient([]))
    db_session.commit()
    db_session.refresh(article)

    assert result.output_payload["published_url"] == "https://yektablog.net/post/1"
    assert article.status == ArticleStatus.PUBLISHED
    assert article.published_url == "https://yektablog.net/post/1"
    assert article.blog_platform_id == blog.id

    # The publisher must never see the raw encrypted password.
    assert fake.calls[0].password == "s3cret"
    assert fake.calls[0].username == "guest-poster"

    pub = db_session.query(Publication).filter(Publication.article_id == article.id).one()
    assert pub.status == PublicationStatus.SUCCESS

    history = (
        db_session.query(ContentStatusHistory)
        .filter(ContentStatusHistory.entity_table == "articles", ContentStatusHistory.entity_id == article.id)
        .filter(ContentStatusHistory.stage == PipelineStage.PUBLISHED)
        .one()
    )
    assert history.to_status == "published"


def test_publish_agent_rejects_unapproved_article(db_session, db_campaign, db_target_page, monkeypatch):
    blog = _make_blog_platform(db_session)
    article = _make_approved_article(db_session, db_campaign, db_target_page)
    article.human_approved = False
    db_session.commit()

    fake = FakePublisher(PublishResult(success=True, published_url="https://x"))
    monkeypatch.setattr(publish_agent, "get_publisher", lambda: fake)

    job = _make_job(article.id, blog.id)
    try:
        publish_agent.run(db_session, job, FakeLLMClient([]))
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "human_approved" in str(exc)
    assert fake.calls == []


def test_publish_agent_requires_automation_credentials(db_session, db_campaign, db_target_page, monkeypatch):
    blog = _make_blog_platform(db_session, with_credentials=False)
    article = _make_approved_article(db_session, db_campaign, db_target_page)

    fake = FakePublisher(PublishResult(success=True, published_url="https://x"))
    monkeypatch.setattr(publish_agent, "get_publisher", lambda: fake)

    job = _make_job(article.id, blog.id)
    try:
        publish_agent.run(db_session, job, FakeLLMClient([]))
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "automation credentials" in str(exc)
    assert fake.calls == []


def test_publish_agent_records_failed_attempt_and_raises(db_session, db_campaign, db_target_page, monkeypatch):
    blog = _make_blog_platform(db_session)
    article = _make_approved_article(db_session, db_campaign, db_target_page)

    fake = FakePublisher(PublishResult(success=False, error_message="Login failed"))
    monkeypatch.setattr(publish_agent, "get_publisher", lambda: fake)

    job = _make_job(article.id, blog.id)
    try:
        publish_agent.run(db_session, job, FakeLLMClient([]))
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "Login failed" in str(exc)

    db_session.commit()
    db_session.refresh(article)
    assert article.status == ArticleStatus.APPROVED  # unchanged
    pub = db_session.query(Publication).filter(Publication.article_id == article.id).one()
    assert pub.status == PublicationStatus.FAILED
    assert pub.notes == "Login failed"


def test_publish_agent_falls_back_to_suggested_platform(db_session, db_campaign, db_target_page, monkeypatch):
    blog = _make_blog_platform(db_session)
    article = _make_approved_article(db_session, db_campaign, db_target_page)
    fake = FakePublisher(PublishResult(success=True, published_url="https://yektablog.net/post/2"))
    monkeypatch.setattr(publish_agent, "get_publisher", lambda: fake)

    job = _make_job(article.id)  # no blog_platform_id in input_payload
    result = publish_agent.run(db_session, job, FakeLLMClient([]))

    assert result.output_payload["blog_platform_id"] == blog.id
