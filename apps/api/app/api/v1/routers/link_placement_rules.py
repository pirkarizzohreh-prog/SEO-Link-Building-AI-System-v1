from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.link_placement_rule import LinkPlacementRule, RuleScope
from app.schemas.link_placement_rule import (
    LinkPlacementRuleCreate,
    LinkPlacementRuleRead,
    LinkPlacementRuleUpdate,
    ResolvedLinkPlacementRule,
)
from app.services.rules_service import resolve_link_placement_rule
from app.utils.crud import CRUDBase

router = APIRouter(prefix="/link-placement-rules", tags=["Link Placement Rules"])
crud = CRUDBase(LinkPlacementRule)


@router.get("/resolve", response_model=ResolvedLinkPlacementRule)
def resolve_rule(campaign_id: int | None = None, db: Session = Depends(get_db)):
    return resolve_link_placement_rule(db, campaign_id=campaign_id)


@router.get("", response_model=list[LinkPlacementRuleRead])
def list_rules(scope: RuleScope | None = None, scope_id: int | None = None, db: Session = Depends(get_db)):
    return crud.list(db, limit=200, scope=scope, scope_id=scope_id)


@router.post("", response_model=LinkPlacementRuleRead, status_code=201)
def create_rule(payload: LinkPlacementRuleCreate, db: Session = Depends(get_db)):
    return crud.create(db, payload)


@router.put("/{rule_id}", response_model=LinkPlacementRuleRead)
def update_rule(rule_id: int, payload: LinkPlacementRuleUpdate, db: Session = Depends(get_db)):
    return crud.update(db, rule_id, payload)


@router.delete("/{rule_id}", status_code=204)
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    crud.delete(db, rule_id)
