"""Resolves the active prompt template for an agent — see
docs/AI_WORKFLOW.md ("پرامپت‌ها اکنون منبع اصلی‌شان دیتابیس است").

Runtime always prefers the active `prompt_templates` row (versioned via
`POST /prompt-templates`, editable without a redeploy). The `.md` files
in this directory are only the seed content: on first use for a given
`agent_type`, if no row exists yet, one is registered as version 1 from
the file — after that, the file is no longer consulted; further changes
go through the API/versioning, not by editing the file in place.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app.models.prompt_template import PromptAgentType, PromptTemplate

_PROMPTS_DIR = Path(__file__).parent / "prompts"

_SEED_FILENAMES: dict[PromptAgentType, str] = {
    PromptAgentType.KEYWORD_INTEL: "keyword_intel.md",
    PromptAgentType.TOPIC_GEN: "topic_generator.md",
    PromptAgentType.COMPETITOR_ANALYSIS: "competitor_analysis.md",
    PromptAgentType.BRIEF_GENERATION: "brief_generation.md",
    PromptAgentType.ARTICLE_WRITE: "article_writer.md",
    PromptAgentType.INTERNAL_LINK_SUGGESTION: "internal_link_suggestion.md",
}


def get_active_prompt(db: Session, agent_type: PromptAgentType) -> PromptTemplate:
    existing = (
        db.query(PromptTemplate)
        .filter(PromptTemplate.agent_type == agent_type, PromptTemplate.is_active.is_(True))
        .order_by(PromptTemplate.version.desc())
        .first()
    )
    if existing is not None:
        return existing

    filename = _SEED_FILENAMES.get(agent_type)
    if filename is None:
        raise RuntimeError(f"No seed prompt file registered for agent_type={agent_type.value}")

    template_text = (_PROMPTS_DIR / filename).read_text(encoding="utf-8")
    seeded = PromptTemplate(
        agent_type=agent_type,
        name=f"{agent_type.value} (seed v1)",
        template_text=template_text,
        version=1,
        is_active=True,
    )
    db.add(seeded)
    db.flush()
    return seeded
