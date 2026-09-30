"""SEO Auditor Agent — docs/AI_WORKFLOW.md, Stage: Audit (step 6).

Runs the whole retry loop inside a single `seo_audit` ai_job (not chained
across separate jobs): hard checks first (deterministic, no LLM); on a
hard-check failure the article is rewritten in place — same brief, same
anchor — via `writer_agent.generate_draft` with the failure feedback
appended to the prompt, up to `MAX_AUDIT_RETRIES` times, before giving up
to `articles.status = needs_human_review`. Soft checks (heading structure,
keyword density, duplicate similarity, LLM tone/forbidden-words) never
block the pass/fail outcome or trigger a retry — they are recorded for the
human reviewer, per the "هشدار نرم" framing in docs/AI_WORKFLOW.md.

Exactly one `content_status_history(stage=audit)` row is written per run,
covering the whole stage regardless of how many retries happened inside it
(docs/AI_WORKFLOW.md: "یک ردیف ... ثبت می‌شود").
"""

from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.ai.agent_result import AgentResult
from app.ai.agents.writer_agent import generate_draft
from app.ai.json_utils import parse_json_response
from app.ai.kb_context import build_kb_context_block
from app.ai.prompts_service import get_active_prompt
from app.ai.providers.base import BaseLLMClient
from app.models.ai_job import AiJob
from app.models.article import Article, ArticleStatus
from app.models.content_status_history import ActorType, ContentStatusHistory, PipelineStage
from app.models.prompt_template import PromptAgentType
from app.models.seo_audit_result import SeoAuditResult
from app.schemas.link_placement_rule import ResolvedLinkPlacementRule
from app.services.rules_service import resolve_link_placement_rule

MAX_AUDIT_RETRIES = 2
MIN_TONE_SCORE = 60
DUPLICATE_SIMILARITY_THRESHOLD = 0.8
HEADING_MATCH_RATIO_THRESHOLD = 0.5
KEYWORD_DENSITY_MIN = 0.3
KEYWORD_DENSITY_MAX = 3.0

_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_HEADING_RE = re.compile(r"^#{2,3}\s+(.+)$", re.MULTILINE)

# (check_name, passed, details, score)
CheckResult = tuple[str, bool, str, float | None]


def _extract_links(content: str) -> list[tuple[str, str]]:
    return _MD_LINK_RE.findall(content)


def _run_hard_checks(
    content: str,
    target_word_count: int,
    target_page_url: str,
    anchor_text: str,
    rule: ResolvedLinkPlacementRule,
) -> list[CheckResult]:
    word_count = len(content.split())
    links = _extract_links(content)
    matching_link = f"[{anchor_text}]({target_page_url})"
    link_index = content.find(matching_link)

    results: list[CheckResult] = [
        (
            "word_count",
            word_count >= target_word_count,
            f"{word_count} کلمه (حداقل لازم: {target_word_count})",
            float(word_count),
        ),
        (
            "link_presence",
            len(links) > 0,
            f"{len(links)} لینک یافت شد" if links else "هیچ لینکی در متن یافت نشد",
            float(len(links)),
        ),
        (
            "url_anchor_correctness",
            link_index != -1,
            "لینک با anchor_text و target_url دقیق یافت شد"
            if link_index != -1
            else f"لینکی با anchor='{anchor_text}' و url='{target_page_url}' یافت نشد",
            None,
        ),
    ]

    if link_index != -1:
        words_before = len(content[:link_index].split())
        results.append(
            (
                "link_position",
                words_before <= rule.link_position_max_words,
                f"لینک در کلمه‌ی {words_before}ام قرار دارد (حداکثر مجاز: {rule.link_position_max_words})",
                float(words_before),
            )
        )
    else:
        results.append(("link_position", False, "قابل بررسی نیست: لینک هدف یافت نشد", None))

    results.append(
        (
            "outbound_link_count",
            len(links) <= rule.max_outbound_links,
            f"{len(links)} لینک خروجی (حداکثر مجاز: {rule.max_outbound_links})",
            float(len(links)),
        )
    )
    return results


def _check_heading_structure(content: str, outline: list[dict]) -> CheckResult:
    outline_headings = [item.get("heading", "").strip() for item in outline if item.get("heading")]
    if not outline_headings:
        return ("heading_structure", True, "بریف فاقد outline هدینگ برای مقایسه بود", None)

    content_headings = [h.strip().lower() for h in _HEADING_RE.findall(content)]
    matched = sum(1 for heading in outline_headings if heading.lower() in content_headings or any(heading.lower() in h for h in content_headings))
    ratio = matched / len(outline_headings)
    passed = ratio >= HEADING_MATCH_RATIO_THRESHOLD
    return (
        "heading_structure",
        passed,
        f"{matched}/{len(outline_headings)} هدینگ بریف در متن یافت شد ({round(ratio * 100)}٪)",
        round(ratio * 100, 2),
    )


def _check_keyword_density(content: str, main_keyword: str) -> CheckResult:
    words = content.split()
    total = len(words) or 1
    occurrences = content.lower().count(main_keyword.lower())
    density = occurrences / total * 100
    passed = KEYWORD_DENSITY_MIN <= density <= KEYWORD_DENSITY_MAX
    return (
        "keyword_density",
        passed,
        f"چگالی کلیدواژه‌ی اصلی: {round(density, 2)}٪ (بازه‌ی مطلوب: {KEYWORD_DENSITY_MIN}-{KEYWORD_DENSITY_MAX}٪)",
        round(density, 2),
    )


def _shingles(text: str, n: int = 3) -> set[tuple[str, ...]]:
    words = re.findall(r"\w+", text.lower())
    if len(words) < n:
        return set()
    return {tuple(words[i : i + n]) for i in range(len(words) - n + 1)}


def _check_duplicate_similarity(db: Session, article: Article, content: str) -> CheckResult:
    others = (
        db.query(Article)
        .filter(
            Article.target_page_id == article.target_page_id,
            Article.id != article.id,
            Article.content.isnot(None),
        )
        .all()
    )
    shingles_a = _shingles(content)
    if not others or not shingles_a:
        return ("duplicate_similarity", True, "مقاله‌ی قبلی برای مقایسه یافت نشد", 0.0)

    max_similarity = 0.0
    for other in others:
        shingles_b = _shingles(other.content or "")
        if not shingles_b:
            continue
        similarity = len(shingles_a & shingles_b) / len(shingles_a | shingles_b)
        max_similarity = max(max_similarity, similarity)

    passed = max_similarity < DUPLICATE_SIMILARITY_THRESHOLD
    return (
        "duplicate_similarity",
        passed,
        f"بیشترین شباهت به مقالات قبلی همین صفحه‌ی هدف: {round(max_similarity * 100, 2)}٪",
        round(max_similarity * 100, 2),
    )


def _check_tone(db: Session, project_id: int, content: str, client: BaseLLMClient) -> tuple[CheckResult, int, float]:
    prompt_template = get_active_prompt(db, PromptAgentType.SEO_AUDIT)
    user_prompt = prompt_template.template_text.format(
        kb_context=build_kb_context_block(db, project_id),
        content=content,
    )
    result = client.generate(
        system_prompt="تو یک ویراستار SEO دقیق و سخت‌گیر هستی.",
        user_prompt=user_prompt,
        json_mode=True,
    )
    parsed = parse_json_response(result.text)
    if not isinstance(parsed, dict):
        raise ValueError("Model tone-check response was not a JSON object")

    tone_score = float(parsed.get("tone_score", 0))
    forbidden_words = parsed.get("forbidden_words_found") or []
    passed = tone_score >= MIN_TONE_SCORE and not forbidden_words
    details = parsed.get("reason", "")
    if forbidden_words:
        details = f"{details} | کلمات ممنوعه‌ی یافت‌شده: {', '.join(forbidden_words)}".strip(" |")

    return ("tone_and_brand_rules", passed, details, tone_score), result.tokens_used, result.cost_estimate


def run(db: Session, job: AiJob, client: BaseLLMClient) -> AgentResult:
    article = db.get(Article, job.reference_id)
    if article is None:
        raise ValueError(f"Article {job.reference_id} not found")
    if article.status != ArticleStatus.IN_AUDIT:
        raise ValueError(f"Article {article.id} is not in_audit (status={article.status.value})")

    brief = article.content_brief
    target_page = article.target_page
    anchor = article.anchor
    campaign = article.campaign
    rule = resolve_link_placement_rule(db, campaign_id=campaign.id)
    target_word_count = brief.target_word_count if brief is not None else 0

    total_tokens = 0
    total_cost = 0.0
    hard_results: list[CheckResult] = []
    attempt = 0

    while True:
        content = article.content or ""
        hard_results = _run_hard_checks(content, target_word_count, target_page.url, anchor.anchor_text, rule)
        if all(passed for _, passed, _, _ in hard_results):
            break
        # Can't regenerate without the brief/topic that produced the draft —
        # fall straight through to needs_human_review in that edge case.
        if brief is None or attempt >= MAX_AUDIT_RETRIES:
            break

        feedback = "؛ ".join(details for _, passed, details, _ in hard_results if not passed)
        result, prompt_template = generate_draft(
            db,
            brief=brief,
            topic=brief.topic,
            target_page=target_page,
            anchor=anchor,
            rule=rule,
            client=client,
            extra_feedback=feedback,
        )
        job.prompt_template_id = prompt_template.id
        job.prompt_template_version = prompt_template.version
        total_tokens += result.tokens_used
        total_cost += result.cost_estimate

        article.content = result.text.strip()
        article.word_count = len(article.content.split())
        article.audit_retry_count += 1
        db.flush()
        attempt += 1

    final_content = article.content or ""
    soft_results: list[CheckResult] = []
    if brief is not None:
        soft_results.append(_check_heading_structure(final_content, brief.outline))
    soft_results.append(_check_keyword_density(final_content, target_page.main_keyword))
    soft_results.append(_check_duplicate_similarity(db, article, final_content))

    tone_result, tone_tokens, tone_cost = _check_tone(db, campaign.project_id, final_content, client)
    soft_results.append(tone_result)
    total_tokens += tone_tokens
    total_cost += tone_cost

    for existing in list(article.seo_audit_results):
        db.delete(existing)
    db.flush()
    for name, passed, details, score in [*hard_results, *soft_results]:
        db.add(SeoAuditResult(article_id=article.id, check_name=name, passed=passed, score=score, details=details))

    passed_overall = all(passed for _, passed, _, _ in hard_results)
    from_status = article.status.value
    article.status = ArticleStatus.REVIEWED if passed_overall else ArticleStatus.NEEDS_HUMAN_REVIEW

    db.add(
        ContentStatusHistory(
            entity_table="articles",
            entity_id=article.id,
            stage=PipelineStage.AUDIT,
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
            "passed": passed_overall,
            "retries_used": article.audit_retry_count,
            "status": article.status.value,
        },
        tokens_used=total_tokens,
        cost_estimate=total_cost,
    )
