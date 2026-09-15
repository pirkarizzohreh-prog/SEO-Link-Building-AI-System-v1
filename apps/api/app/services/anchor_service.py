"""Anchor selection against the resolved Link Placement Rule — see
docs/AI_WORKFLOW.md ("Stage: Writing") and docs/DATABASE_SCHEMA.md
(`anchor_usage_log`). Shared by the anchors router's distribution
endpoint and the Article Writer agent so both compute "actual usage"
the same way.
"""

from __future__ import annotations

from collections import Counter

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.anchor import Anchor, AnchorType
from app.models.anchor_usage_log import AnchorUsageLog

DISTRIBUTION_WINDOW = 20


def compute_actual_counts(db: Session, target_page_id: int, window: int = DISTRIBUTION_WINDOW) -> Counter:
    recent = db.scalars(
        select(AnchorUsageLog.anchor_type)
        .join(Anchor, AnchorUsageLog.anchor_id == Anchor.id)
        .where(Anchor.target_page_id == target_page_id)
        .order_by(AnchorUsageLog.used_at.desc())
        .limit(window)
    ).all()
    return Counter(recent)


def pick_next_anchor(db: Session, target_page_id: int, target_ratio: dict[str, float]) -> Anchor:
    """Picks an active, not-yet-exhausted anchor whose type is currently
    the most under-represented relative to `target_ratio` (the resolved
    Link Placement Rule's anchor_distribution).
    """
    actual = compute_actual_counts(db, target_page_id)
    total = sum(actual.values()) or 1

    deficits = []
    for anchor_type in AnchorType:
        target_pct = target_ratio.get(anchor_type.value, 0)
        actual_pct = actual.get(anchor_type, 0) / total * 100
        deficits.append((target_pct - actual_pct, anchor_type))
    deficits.sort(key=lambda pair: pair[0], reverse=True)

    for _, anchor_type in deficits:
        candidate = (
            db.query(Anchor)
            .filter(
                Anchor.target_page_id == target_page_id,
                Anchor.anchor_type == anchor_type,
                Anchor.is_active.is_(True),
                or_(Anchor.usage_limit.is_(None), Anchor.usage_count < Anchor.usage_limit),
            )
            .order_by(Anchor.usage_count.asc())
            .first()
        )
        if candidate is not None:
            return candidate

    raise ValueError(f"No active, available anchor for target_page_id={target_page_id}")


def record_anchor_usage(db: Session, anchor: Anchor, article_id: int) -> None:
    db.add(AnchorUsageLog(anchor_id=anchor.id, article_id=article_id, anchor_type=anchor.anchor_type))
    anchor.usage_count += 1
