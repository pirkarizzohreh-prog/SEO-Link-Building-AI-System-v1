"""Keyword Intelligence Agent — docs/AI_WORKFLOW.md, Stage: Idea (step 2).

Chained automatically by app/jobs/handlers.py into a topic_gen job once
this one succeeds — see docs/AI_WORKFLOW.md's "زنجیره‌ی خودکار".
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai.agent_result import AgentResult
from app.ai.json_utils import parse_json_response
from app.ai.kb_context import build_kb_context_block
from app.ai.prompts_service import get_active_prompt
from app.ai.providers.base import BaseLLMClient
from app.models.ai_job import AiJob
from app.models.campaign import Campaign
from app.models.keyword import Keyword, KeywordSource, KeywordType
from app.models.prompt_template import PromptAgentType


def run(db: Session, job: AiJob, client: BaseLLMClient) -> AgentResult:
    campaign = db.get(Campaign, job.reference_id)
    if campaign is None:
        raise ValueError(f"Campaign {job.reference_id} not found")
    target_page = campaign.target_page

    prompt_template = get_active_prompt(db, PromptAgentType.KEYWORD_INTEL)
    job.prompt_template_id = prompt_template.id
    job.prompt_template_version = prompt_template.version

    user_prompt = prompt_template.template_text.format(
        title=target_page.title,
        url=target_page.url,
        main_keyword=target_page.main_keyword,
        kb_context=build_kb_context_block(db, campaign.project_id),
    )
    result = client.generate(
        system_prompt="تو یک متخصص تحقیق کلمات کلیدی SEO هستی.",
        user_prompt=user_prompt,
        json_mode=True,
    )

    parsed = parse_json_response(result.text)
    items = parsed.get("related_keywords", []) if isinstance(parsed, dict) else []

    created = []
    for item in items:
        keyword_text = (item.get("keyword") or "").strip()
        if not keyword_text:
            continue
        kw_type = item.get("type") if item.get("type") in ("related", "semantic") else "related"
        keyword = Keyword(
            target_page_id=target_page.id,
            keyword=keyword_text,
            type=KeywordType(kw_type),
            source=KeywordSource.AI,
        )
        db.add(keyword)
        created.append(keyword_text)
    db.flush()

    return AgentResult(
        output_payload={"created_keywords": created},
        tokens_used=result.tokens_used,
        cost_estimate=result.cost_estimate,
    )
