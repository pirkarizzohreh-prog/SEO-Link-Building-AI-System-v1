"""Link Placement Rules resolution — see docs/DATABASE_SCHEMA.md and
docs/AI_WORKFLOW.md ("Stage: Writing").

Resolution order is most-specific-wins: campaign -> project -> global.
This is deliberately a plain query, not a FK on campaigns/projects, so
adding an override for one campaign never requires a migration.

From Sprint 3 onward, `anchor_service.pick_next_anchor` and the Article
Writer prompt builder call this instead of hardcoding the 30/35/20/15
ratio or the "first 100 words" rule.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.campaign import Campaign
from app.models.link_placement_rule import LinkPlacementRule, RuleScope
from app.schemas.link_placement_rule import ResolvedLinkPlacementRule


def _find_active_rule(db: Session, scope: RuleScope, scope_id: int | None) -> LinkPlacementRule | None:
    query = db.query(LinkPlacementRule).filter(
        LinkPlacementRule.scope == scope,
        LinkPlacementRule.is_active.is_(True),
    )
    if scope_id is None:
        query = query.filter(LinkPlacementRule.scope_id.is_(None))
    else:
        query = query.filter(LinkPlacementRule.scope_id == scope_id)
    return query.first()


def resolve_link_placement_rule(db: Session, campaign_id: int | None = None) -> ResolvedLinkPlacementRule:
    """Return the effective rule for a campaign (or the bare global default
    when no campaign context is given, e.g. from a target-page-scoped
    endpoint like anchor distribution).
    """

    project_id: int | None = None
    if campaign_id is not None:
        campaign = db.get(Campaign, campaign_id)
        if campaign is not None:
            project_id = campaign.project_id

            rule = _find_active_rule(db, RuleScope.CAMPAIGN, campaign_id)
            if rule is not None:
                return _to_resolved(rule, RuleScope.CAMPAIGN)

    if project_id is not None:
        rule = _find_active_rule(db, RuleScope.PROJECT, project_id)
        if rule is not None:
            return _to_resolved(rule, RuleScope.PROJECT)

    rule = _find_active_rule(db, RuleScope.GLOBAL, None)
    if rule is not None:
        return _to_resolved(rule, RuleScope.GLOBAL)

    # No global row seeded yet (fresh install, migrations not seeded) —
    # fall back to the Pydantic schema's own defaults so the rest of the
    # pipeline always has *something* to resolve against.
    return ResolvedLinkPlacementRule(scope=RuleScope.GLOBAL, resolved_from=RuleScope.GLOBAL, rule_id=None)


def _to_resolved(rule: LinkPlacementRule, resolved_from: RuleScope) -> ResolvedLinkPlacementRule:
    return ResolvedLinkPlacementRule(
        scope=rule.scope,
        scope_id=rule.scope_id,
        anchor_distribution=rule.anchor_distribution,
        link_position_max_words=rule.link_position_max_words,
        max_outbound_links=rule.max_outbound_links,
        max_links_per_blog_per_month=rule.max_links_per_blog_per_month,
        min_days_between_links_same_target=rule.min_days_between_links_same_target,
        is_active=rule.is_active,
        resolved_from=resolved_from,
        rule_id=rule.id,
    )
