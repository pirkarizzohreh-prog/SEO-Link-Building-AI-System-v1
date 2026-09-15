"""Content Brief Generator — docs/AI_WORKFLOW.md, Stage: Brief (step 4)."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.ai.agent_result import AgentResult
from app.ai.json_utils import parse_json_response
from app.ai.kb_context import build_kb_context_block
from app.ai.prompts_service import get_active_prompt
from app.ai.providers.base import BaseLLMClient
from app.models.ai_job import AiJob
from app.models.content_brief import BriefStatus, ContentBrief
from app.models.content_gap import ContentGap, GapStatus
from app.models.content_template import ContentTemplate
from app.models.keyword import Keyword, KeywordType
from app.models.prompt_template import PromptAgentType
from app.models.topic import Topic

DEFAULT_TARGET_WORD_COUNT = 1200


def _find_matching_template(db: Session, page_type: str) -> ContentTemplate | None:
    candidates = db.query(ContentTemplate).filter(ContentTemplate.is_active.is_(True)).all()
    for template in candidates:
        if template.applicable_page_types and page_type in template.applicable_page_types:
            return template
    return None


def run(db: Session, job: AiJob, client: BaseLLMClient) -> AgentResult:
    topic = db.get(Topic, job.reference_id)
    if topic is None:
        raise ValueError(f"Topic {job.reference_id} not found")
    if db.query(ContentBrief).filter(ContentBrief.topic_id == topic.id).first() is not None:
        raise ValueError(f"Topic {topic.id} already has a content brief")

    campaign = topic.campaign
    target_page = campaign.target_page
    related_keywords = (
        db.query(Keyword)
        .filter(Keyword.target_page_id == target_page.id, Keyword.type != KeywordType.MAIN)
        .all()
    )
    content_gaps = (
        db.query(ContentGap)
        .filter(ContentGap.target_page_id == target_page.id, ContentGap.status == GapStatus.USED_IN_TOPIC)
        .all()
    )
    template = _find_matching_template(db, target_page.page_type.value)

    prompt_template = get_active_prompt(db, PromptAgentType.BRIEF_GENERATION)
    job.prompt_template_id = prompt_template.id
    job.prompt_template_version = prompt_template.version

    template_hint = ""
    if template is not None:
        template_hint = (
            f"از این اسکلت پایه به‌عنوان چارچوب استفاده کن: "
            f"{json.dumps(template.default_outline_skeleton, ensure_ascii=False)}"
        )

    user_prompt = prompt_template.template_text.format(
        topic_title=topic.title,
        topic_rationale=topic.rationale or "—",
        main_keyword=target_page.main_keyword,
        related_keywords=", ".join(k.keyword for k in related_keywords) or "—",
        content_gaps=", ".join(g.gap_topic for g in content_gaps) or "—",
        template_hint=template_hint,
        kb_context=build_kb_context_block(db, campaign.project_id),
    )
    result = client.generate(
        system_prompt="تو یک استراتژیست محتوا هستی.",
        user_prompt=user_prompt,
        json_mode=True,
    )

    parsed = parse_json_response(result.text)
    if not isinstance(parsed, dict) or not parsed.get("outline"):
        raise ValueError("Model response did not include a usable 'outline'")

    brief = ContentBrief(
        topic_id=topic.id,
        content_template_id=template.id if template else None,
        target_page_id=target_page.id,
        outline=parsed["outline"],
        target_word_count=parsed.get("target_word_count") or DEFAULT_TARGET_WORD_COUNT,
        keywords_to_include=parsed.get("keywords_to_include"),
        must_include_points=parsed.get("must_include_points"),
        tone=parsed.get("tone"),
        source_content_gap_ids=[g.id for g in content_gaps] or None,
        status=BriefStatus.DRAFT,
    )
    db.add(brief)
    db.flush()

    return AgentResult(
        output_payload={"content_brief_id": brief.id, "outline_sections": len(parsed["outline"])},
        tokens_used=result.tokens_used,
        cost_estimate=result.cost_estimate,
    )
