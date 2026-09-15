"""Topic Generator Agent — docs/AI_WORKFLOW.md, Stage: Idea (step 3)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai.agent_result import AgentResult
from app.ai.json_utils import parse_json_response
from app.ai.kb_context import build_kb_context_block
from app.ai.prompts_service import get_active_prompt
from app.ai.providers.base import BaseLLMClient
from app.models.ai_job import AiJob
from app.models.campaign import Campaign
from app.models.content_gap import ContentGap, GapStatus
from app.models.keyword import Keyword, KeywordType
from app.models.prompt_template import PromptAgentType
from app.models.topic import GeneratedBy, Topic, TopicStatus

# Batch size cap so one campaign.start doesn't try to generate (and pay
# for) dozens of topics in a single call; the rest come from re-running
# this agent as earlier topics get approved/rejected.
MAX_TOPICS_PER_BATCH = 8


def run(db: Session, job: AiJob, client: BaseLLMClient) -> AgentResult:
    campaign = db.get(Campaign, job.reference_id)
    if campaign is None:
        raise ValueError(f"Campaign {job.reference_id} not found")
    target_page = campaign.target_page

    related_keywords = (
        db.query(Keyword)
        .filter(Keyword.target_page_id == target_page.id, Keyword.type != KeywordType.MAIN)
        .all()
    )
    content_gaps = (
        db.query(ContentGap)
        .filter(ContentGap.target_page_id == target_page.id, ContentGap.status == GapStatus.NEW)
        .all()
    )
    topic_count = min(campaign.total_links_target, MAX_TOPICS_PER_BATCH)

    prompt_template = get_active_prompt(db, PromptAgentType.TOPIC_GEN)
    job.prompt_template_id = prompt_template.id
    job.prompt_template_version = prompt_template.version

    user_prompt = prompt_template.template_text.format(
        main_keyword=target_page.main_keyword,
        related_keywords=", ".join(k.keyword for k in related_keywords) or "—",
        content_gaps=", ".join(g.gap_topic for g in content_gaps) or "—",
        topic_count=topic_count,
        kb_context=build_kb_context_block(db, campaign.project_id),
    )
    result = client.generate(
        system_prompt="تو یک استراتژیست محتوا و SEO هستی.",
        user_prompt=user_prompt,
        json_mode=True,
    )

    parsed = parse_json_response(result.text)
    items = parsed.get("topics", []) if isinstance(parsed, dict) else []

    created_titles = []
    for item in items[:MAX_TOPICS_PER_BATCH]:
        title = (item.get("title") or "").strip()
        if not title:
            continue
        db.add(
            Topic(
                campaign_id=campaign.id,
                title=title,
                rationale=item.get("rationale"),
                status=TopicStatus.SUGGESTED,
                generated_by=GeneratedBy.AI,
            )
        )
        created_titles.append(title)

    # MVP simplification (documented in docs/AI_WORKFLOW.md as a known
    # trade-off): we don't ask the model to cite which gap inspired which
    # topic, so we can't mark gaps used_in_topic 1:1. Since they were all
    # offered to the model as candidate input, mark them consumed as a
    # batch rather than leaving them "new" forever.
    for gap in content_gaps:
        gap.status = GapStatus.USED_IN_TOPIC

    db.flush()

    return AgentResult(
        output_payload={"created_topics": created_titles},
        tokens_used=result.tokens_used,
        cost_estimate=result.cost_estimate,
    )
