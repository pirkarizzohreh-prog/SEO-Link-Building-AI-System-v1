from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.link_placement_rule import DEFAULT_ANCHOR_DISTRIBUTION, RuleScope


class LinkPlacementRuleBase(BaseModel):
    scope: RuleScope
    scope_id: int | None = None
    anchor_distribution: dict[str, float] = DEFAULT_ANCHOR_DISTRIBUTION
    link_position_max_words: int = 100
    max_outbound_links: int = 1
    max_links_per_blog_per_month: int | None = None
    min_days_between_links_same_target: int | None = None
    is_active: bool = True


class LinkPlacementRuleCreate(LinkPlacementRuleBase):
    pass


class LinkPlacementRuleUpdate(BaseModel):
    anchor_distribution: dict[str, float] | None = None
    link_position_max_words: int | None = None
    max_outbound_links: int | None = None
    max_links_per_blog_per_month: int | None = None
    min_days_between_links_same_target: int | None = None
    is_active: bool | None = None


class LinkPlacementRuleRead(LinkPlacementRuleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class ResolvedLinkPlacementRule(LinkPlacementRuleBase):
    """The effective rule for a campaign, after resolving campaign -> project -> global."""

    resolved_from: RuleScope
    rule_id: int | None = None
