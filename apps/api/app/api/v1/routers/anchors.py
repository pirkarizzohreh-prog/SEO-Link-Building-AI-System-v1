from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.anchor import Anchor, AnchorType
from app.models.anchor_usage_log import AnchorUsageLog
from app.schemas.anchor import AnchorCreate, AnchorDistribution, AnchorRead, AnchorUpdate
from app.services.rules_service import resolve_link_placement_rule
from app.utils.crud import CRUDBase

router = APIRouter(tags=["Anchor Bank"])
crud = CRUDBase(Anchor)

# The window (most recent N usages) the ratio is measured over — matches
# the "per 20 links" wording in the original PRD; the resolved rule only
# overrides the *target* ratio, not this window size, in Sprint 1.
DISTRIBUTION_WINDOW = 20


@router.get("/target-pages/{target_page_id}/anchors", response_model=list[AnchorRead])
def list_anchors(target_page_id: int, db: Session = Depends(get_db)):
    return crud.list(db, limit=500, target_page_id=target_page_id)


@router.post("/target-pages/{target_page_id}/anchors", response_model=AnchorRead, status_code=201)
def create_anchor(target_page_id: int, payload: AnchorCreate, db: Session = Depends(get_db)):
    return crud.create(db, payload, target_page_id=target_page_id)


@router.put("/anchors/{anchor_id}", response_model=AnchorRead)
def update_anchor(anchor_id: int, payload: AnchorUpdate, db: Session = Depends(get_db)):
    return crud.update(db, anchor_id, payload)


@router.delete("/anchors/{anchor_id}", status_code=204)
def delete_anchor(anchor_id: int, db: Session = Depends(get_db)):
    crud.delete(db, anchor_id)


@router.get("/target-pages/{target_page_id}/anchors/distribution", response_model=AnchorDistribution)
def get_anchor_distribution(target_page_id: int, db: Session = Depends(get_db)):
    """Actual anchor-type usage over the last `DISTRIBUTION_WINDOW` links for
    this target page, against the resolved target ratio (global default
    30/35/20/15 unless overridden — see `link_placement_rules`).
    """
    resolved = resolve_link_placement_rule(db)  # no campaign context here -> falls back to global
    recent = db.scalars(
        select(AnchorUsageLog.anchor_type)
        .join(Anchor, AnchorUsageLog.anchor_id == Anchor.id)
        .where(Anchor.target_page_id == target_page_id)
        .order_by(AnchorUsageLog.used_at.desc())
        .limit(DISTRIBUTION_WINDOW)
    ).all()

    counts = Counter(t.value for t in recent)
    total = sum(counts.values()) or 1
    actual_ratio = {t.value: round(counts.get(t.value, 0) / total * 100, 1) for t in AnchorType}

    return AnchorDistribution(
        target_page_id=target_page_id,
        window_size=len(recent),
        target_ratio=resolved.anchor_distribution,
        actual_counts={t.value: counts.get(t.value, 0) for t in AnchorType},
        actual_ratio=actual_ratio,
    )
