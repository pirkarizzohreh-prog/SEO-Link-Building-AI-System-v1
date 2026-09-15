"""Project Knowledge Base -> prompt context block — see docs/AI_WORKFLOW.md
("Stage ۰ — پیش‌نیازهای Config"). Injected into every content-related
agent's prompt; empty when the project hasn't set one up (backward
compatible with a KB-less project, per the design doc).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.project_knowledge_base import ProjectKnowledgeBase


def build_kb_context_block(db: Session, project_id: int) -> str:
    kb = db.query(ProjectKnowledgeBase).filter(ProjectKnowledgeBase.project_id == project_id).first()
    if kb is None:
        return ""

    lines = ["اطلاعات برند/پروژه (Project Knowledge Base) — رعایت این نکات الزامی است:"]
    if kb.brand_name:
        lines.append(f"- نام برند: {kb.brand_name}")
    if kb.brand_voice_tone:
        lines.append(f"- لحن برند: {kb.brand_voice_tone}")
    if kb.target_audience:
        lines.append(f"- مخاطب هدف: {kb.target_audience}")
    if kb.industry_context:
        lines.append(f"- زمینه صنعت: {kb.industry_context}")
    if kb.style_guidelines:
        lines.append(f"- راهنمای سبک نگارش: {kb.style_guidelines}")
    if kb.forbidden_words:
        lines.append(f"- کلمات/ادعاهای ممنوعه (هرگز استفاده نشود): {', '.join(kb.forbidden_words)}")
    if kb.mandatory_points:
        lines.append(f"- نکات الزامی: {', '.join(kb.mandatory_points)}")

    return "\n".join(lines) if len(lines) > 1 else ""
