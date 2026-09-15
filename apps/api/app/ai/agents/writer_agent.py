"""Article Writer Agent — docs/AI_WORKFLOW.md, Stage: Writing (step 5).

Produces `articles[status=draft]`. The SEO Auditor that moves it into
Stage: Audit is Sprint 4 — this agent's output sits at `draft` until
then (or until a human reviews it manually).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai.agent_result import AgentResult
from app.ai.kb_context import build_kb_context_block
from app.ai.prompts_service import get_active_prompt
from app.ai.providers.base import BaseLLMClient
from app.models.ai_job import AiJob
from app.models.article import Article, ArticleStatus
from app.models.content_brief import BriefStatus, ContentBrief
from app.models.content_status_history import ActorType, ContentStatusHistory, PipelineStage
from app.models.prompt_template import PromptAgentType
from app.services.anchor_service import pick_next_anchor, record_anchor_usage
from app.services.rules_service import resolve_link_placement_rule


def run(db: Session, job: AiJob, client: BaseLLMClient) -> AgentResult:
    brief = db.get(ContentBrief, job.reference_id)
    if brief is None:
        raise ValueError(f"Content brief {job.reference_id} not found")
    if brief.status != BriefStatus.APPROVED:
        raise ValueError(f"Content brief {brief.id} is not approved yet (status={brief.status.value})")

    topic = brief.topic
    campaign = topic.campaign
    target_page = brief.target_page

    rule = resolve_link_placement_rule(db, campaign_id=campaign.id)
    anchor = pick_next_anchor(db, target_page.id, rule.anchor_distribution)

    prompt_template = get_active_prompt(db, PromptAgentType.ARTICLE_WRITE)
    job.prompt_template_id = prompt_template.id
    job.prompt_template_version = prompt_template.version

    outline_text = "\n".join(
        f"- ({item.get('level', 'h2')}) {item.get('heading', '')}: "
        f"{'، '.join(item.get('key_points', []))}"
        for item in brief.outline
    )

    user_prompt = prompt_template.template_text.format(
        kb_context=build_kb_context_block(db, campaign.project_id),
        topic_title=topic.title,
        main_keyword=target_page.main_keyword,
        outline=outline_text or "—",
        keywords_to_include=", ".join(brief.keywords_to_include or []) or "—",
        must_include_points=", ".join(brief.must_include_points or []) or "—",
        tone=brief.tone or "طبیعی و انسانی",
        target_url=target_page.url,
        anchor_text=anchor.anchor_text,
        target_word_count=brief.target_word_count,
        link_position_max_words=rule.link_position_max_words,
    )
    result = client.generate(
        system_prompt="تو یک متخصص SEO و نویسنده تخصصی هستی.",
        user_prompt=user_prompt,
        json_mode=False,
    )

    content = result.text.strip()
    word_count = len(content.split())

    article = Article(
        campaign_id=campaign.id,
        topic_id=topic.id,
        content_brief_id=brief.id,
        target_page_id=target_page.id,
        anchor_id=anchor.id,
        title=topic.title,
        content=content,
        word_count=word_count,
        status=ArticleStatus.DRAFT,
    )
    db.add(article)
    db.flush()

    record_anchor_usage(db, anchor, article.id)
    db.add(
        ContentStatusHistory(
            entity_table="articles",
            entity_id=article.id,
            stage=PipelineStage.WRITING,
            from_status=None,
            to_status=ArticleStatus.DRAFT.value,
            actor_type=ActorType.AI,
            actor_id=job.id,
        )
    )
    db.flush()

    return AgentResult(
        output_payload={"article_id": article.id, "word_count": word_count, "anchor_id": anchor.id},
        tokens_used=result.tokens_used,
        cost_estimate=result.cost_estimate,
    )
