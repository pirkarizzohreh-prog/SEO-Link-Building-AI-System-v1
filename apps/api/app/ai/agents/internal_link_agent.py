"""Internal Link Suggestion Agent — docs/AI_WORKFLOW.md, step 9.

Independent of the guest-post pipeline (see the module docstring in
app/models/internal_link_suggestion.py): analyzes a project's own
target_pages for internal linking opportunities, never touches
`articles`. MVP limitation carried over from docs/DATABASE_SCHEMA.md:
only `target_pages` already registered are considered, not a full site
crawl.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai.agent_result import AgentResult
from app.ai.json_utils import parse_json_response
from app.ai.prompts_service import get_active_prompt
from app.ai.providers.base import BaseLLMClient
from app.models.ai_job import AiJob
from app.models.internal_link_suggestion import InternalLinkStatus, InternalLinkSuggestion
from app.models.prompt_template import PromptAgentType
from app.models.target_page import TargetPage

MAX_SUGGESTIONS = 10


def run(db: Session, job: AiJob, client: BaseLLMClient) -> AgentResult:
    project_id = job.reference_id
    pages = db.query(TargetPage).filter(TargetPage.project_id == project_id).all()
    if len(pages) < 2:
        return AgentResult(output_payload={"created_suggestions": [], "reason": "fewer than 2 target pages"})

    valid_ids = {p.id for p in pages}
    pages_list = "\n".join(f"- id={p.id}, عنوان: {p.title}, کلیدواژه اصلی: {p.main_keyword}" for p in pages)

    prompt_template = get_active_prompt(db, PromptAgentType.INTERNAL_LINK_SUGGESTION)
    job.prompt_template_id = prompt_template.id
    job.prompt_template_version = prompt_template.version

    user_prompt = prompt_template.template_text.format(pages_list=pages_list)
    result = client.generate(
        system_prompt="تو یک متخصص ساختار سایت و SEO داخلی هستی.",
        user_prompt=user_prompt,
        json_mode=True,
    )

    parsed = parse_json_response(result.text)
    items = parsed.get("suggestions", []) if isinstance(parsed, dict) else []

    created = []
    for item in items[:MAX_SUGGESTIONS]:
        source_id = item.get("source_id")
        destination_id = item.get("destination_id")
        anchor = (item.get("suggested_anchor") or "").strip()
        if source_id not in valid_ids or destination_id not in valid_ids or source_id == destination_id:
            continue
        if not anchor:
            continue
        db.add(
            InternalLinkSuggestion(
                project_id=project_id,
                source_target_page_id=source_id,
                destination_target_page_id=destination_id,
                suggested_anchor=anchor,
                reason=item.get("reason"),
                status=InternalLinkStatus.SUGGESTED,
            )
        )
        created.append({"source_id": source_id, "destination_id": destination_id})
    db.flush()

    return AgentResult(
        output_payload={"created_suggestions": created},
        tokens_used=result.tokens_used,
        cost_estimate=result.cost_estimate,
    )
