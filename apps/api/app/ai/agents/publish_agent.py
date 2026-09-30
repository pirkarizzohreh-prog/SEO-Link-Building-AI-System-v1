"""Publication Manager, automated path — docs/AI_WORKFLOW.md ("Stage:
Published", نسخه دوم). No LLM call (docs/AI_WORKFLOW.md's role table marks
Publisher "بدون LLM") — `client` is accepted only so this fits the same
`_AGENT_DISPATCH` signature as every other agent in app/jobs/handlers.py.

Defense in depth: `POST /articles/{id}/publish-automated` already checks
`human_approved` before enqueueing this job, but the job repeats the check
itself — per docs/AI_WORKFLOW.md ("همان چک human_approved را قبل از اجرا
تکرار می‌کند") and docs/DATABASE_SCHEMA.md's hard rule that this gate is
enforced at the service layer, not just at one call site, so a stale queue
entry or a bug in the enqueue path can never publish an unapproved article.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.ai.agent_result import AgentResult
from app.ai.providers.base import BaseLLMClient
from app.automation.markdown_to_html import markdown_to_html
from app.automation.publishers.base_publisher import PublishPayload
from app.automation.publishers.factory import get_publisher
from app.core.crypto import decrypt_secret
from app.models.ai_job import AiJob
from app.models.article import Article, ArticleStatus
from app.models.blog_platform import BlogPlatform
from app.models.content_status_history import ActorType, ContentStatusHistory, PipelineStage
from app.models.publication import Publication, PublicationMethod, PublicationStatus
from app.services.publication_service import suggest_blog_platform


def run(db: Session, job: AiJob, client: BaseLLMClient) -> AgentResult:
    article = db.get(Article, job.reference_id)
    if article is None:
        raise ValueError(f"Article {job.reference_id} not found")
    if not article.human_approved:
        raise ValueError(
            f"Article {article.id} is not human_approved — refusing to publish "
            "(app/ai/agents/publish_agent.py's defense-in-depth check)"
        )
    if article.status == ArticleStatus.PUBLISHED:
        raise ValueError(f"Article {article.id} is already published")

    blog_platform_id = (job.input_payload or {}).get("blog_platform_id")
    blog_platform = db.get(BlogPlatform, blog_platform_id) if blog_platform_id else suggest_blog_platform(db)
    if blog_platform is None:
        raise ValueError("No active blog platform available to publish to")
    if not blog_platform.has_automation_credentials:
        raise ValueError(
            f"Blog platform {blog_platform.id} has no automation credentials — "
            "set them via POST /blog-platforms/{id}/credentials first"
        )

    publisher = get_publisher()
    result = publisher.publish(
        PublishPayload(
            title=article.title,
            content_html=markdown_to_html(article.content or ""),
            login_url=blog_platform.login_url or f"{blog_platform.url.rstrip('/')}/wp-login.php",
            username=blog_platform.username,
            password=decrypt_secret(blog_platform.password_encrypted),
            category=blog_platform.category_default,
        )
    )

    if not result.success:
        db.add(
            Publication(
                article_id=article.id,
                blog_platform_id=blog_platform.id,
                method=PublicationMethod.AUTOMATED,
                status=PublicationStatus.FAILED,
                notes=result.error_message,
                published_at=datetime.now(timezone.utc),
            )
        )
        db.flush()
        # Re-raise so app/jobs/handlers.py marks the job FAILED and records
        # error_message — automation failures are never silent (docs/
        # AI_WORKFLOW.md: "خطاهای اتوماسیون هرگز silent fail نیستند").
        raise ValueError(result.error_message or "Automated publish failed for an unknown reason")

    now = datetime.now(timezone.utc)
    from_status = article.status.value
    article.blog_platform_id = blog_platform.id
    article.status = ArticleStatus.PUBLISHED
    article.published_url = result.published_url
    article.published_at = now
    blog_platform.last_publish_date = now

    db.add(
        Publication(
            article_id=article.id,
            blog_platform_id=blog_platform.id,
            method=PublicationMethod.AUTOMATED,
            status=PublicationStatus.SUCCESS,
            published_url=result.published_url,
            published_at=now,
        )
    )
    db.add(
        ContentStatusHistory(
            entity_table="articles",
            entity_id=article.id,
            stage=PipelineStage.PUBLISHED,
            from_status=from_status,
            to_status=article.status.value,
            actor_type=ActorType.AI,
            actor_id=job.id,
        )
    )
    db.flush()

    return AgentResult(
        output_payload={
            "article_id": article.id,
            "blog_platform_id": blog_platform.id,
            "published_url": result.published_url,
        },
        tokens_used=0,
        cost_estimate=0.0,
    )
