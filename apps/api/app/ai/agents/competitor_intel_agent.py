"""Competitor Intelligence Agent — docs/AI_WORKFLOW.md, Stage: Idea (step 1).

Runs in two parts: a deterministic fetch+extract (no LLM, no cost) that
fills in `competitor_pages.fetched_*`, then one LLM call comparing the
extracted signals against our own keywords to produce `content_gaps`.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.ai.agent_result import AgentResult
from app.ai.html_extract import extract_page_signals
from app.ai.json_utils import parse_json_response
from app.ai.prompts_service import get_active_prompt
from app.ai.providers.base import BaseLLMClient
from app.ai.safe_fetch import fetch_html
from app.models.ai_job import AiJob
from app.models.competitor_page import CompetitorPage
from app.models.content_gap import ContentGap, GapStatus, GapType
from app.models.keyword import Keyword
from app.models.prompt_template import PromptAgentType

_VALID_GAP_TYPES = {t.value for t in GapType}


def run(db: Session, job: AiJob, client: BaseLLMClient) -> AgentResult:
    page = db.get(CompetitorPage, job.reference_id)
    if page is None:
        raise ValueError(f"Competitor page {job.reference_id} not found")
    if page.target_page_id is None:
        raise ValueError("This competitor page has no linked target_page_id — set one before analyzing")
    target_page = page.target_page

    html = fetch_html(page.url)
    signals = extract_page_signals(html)

    page.fetched_title = signals["title"][:500] if signals["title"] else None
    page.fetched_headings = signals["headings"]
    page.fetched_word_count = signals["word_count"]
    page.top_keywords = signals["top_keywords"]
    page.analyzed_at = datetime.now(timezone.utc)

    our_keywords = db.query(Keyword).filter(Keyword.target_page_id == target_page.id).all()

    prompt_template = get_active_prompt(db, PromptAgentType.COMPETITOR_ANALYSIS)
    job.prompt_template_id = prompt_template.id
    job.prompt_template_version = prompt_template.version

    user_prompt = prompt_template.template_text.format(
        main_keyword=target_page.main_keyword,
        our_keywords=", ".join(k.keyword for k in our_keywords) or "—",
        competitor_title=signals["title"] or "—",
        competitor_headings=", ".join(signals["headings"]) or "—",
        competitor_keywords=", ".join(signals["top_keywords"]) or "—",
    )
    result = client.generate(
        system_prompt="تو یک تحلیل‌گر محتوا و SEO هستی.",
        user_prompt=user_prompt,
        json_mode=True,
    )

    parsed = parse_json_response(result.text)
    items = parsed.get("gaps", []) if isinstance(parsed, dict) else []

    created_gaps = []
    for item in items:
        gap_topic = (item.get("gap_topic") or "").strip()
        if not gap_topic:
            continue
        gap_type = item.get("gap_type") if item.get("gap_type") in _VALID_GAP_TYPES else GapType.TOPIC.value
        db.add(
            ContentGap(
                target_page_id=target_page.id,
                gap_topic=gap_topic,
                gap_type=GapType(gap_type),
                source_competitor_page_id=page.id,
                status=GapStatus.NEW,
            )
        )
        created_gaps.append(gap_topic)
    db.flush()

    return AgentResult(
        output_payload={
            "fetched_word_count": signals["word_count"],
            "created_content_gaps": created_gaps,
        },
        tokens_used=result.tokens_used,
        cost_estimate=result.cost_estimate,
    )
