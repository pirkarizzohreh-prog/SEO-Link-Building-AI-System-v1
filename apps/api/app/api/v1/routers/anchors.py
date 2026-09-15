from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.anchor import Anchor, AnchorType
from app.schemas.anchor import AnchorCreate, AnchorDistribution, AnchorRead, AnchorUpdate
from app.services.anchor_service import compute_actual_counts
from app.services.rules_service import resolve_link_placement_rule
from app.utils.crud import CRUDBase

router = APIRouter(tags=["Anchor Bank"])
crud = CRUDBase(Anchor)


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
    30/35/20/15 unless overridden — see `link_placement_rules`). Uses the
    same `anchor_service.compute_actual_counts` the Article Writer agent
    (Sprint 3) calls before picking the next anchor, so this view always
    matches what the agent actually sees.
    """
    resolved = resolve_link_placement_rule(db)  # no campaign context here -> falls back to global
    counts = compute_actual_counts(db, target_page_id)
    total = sum(counts.values()) or 1
    actual_ratio = {t.value: round(counts.get(t, 0) / total * 100, 1) for t in AnchorType}

    return AnchorDistribution(
        target_page_id=target_page_id,
        window_size=sum(counts.values()),
        target_ratio=resolved.anchor_distribution,
        actual_counts={t.value: counts.get(t, 0) for t in AnchorType},
        actual_ratio=actual_ratio,
    )
