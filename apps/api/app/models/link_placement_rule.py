from __future__ import annotations

import enum

from sqlalchemy import Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import JSONType, sa_enum
from app.models.mixins import TimestampMixin, UpdatedAtMixin

DEFAULT_ANCHOR_DISTRIBUTION = {"exact": 30, "partial": 35, "semantic": 20, "brand": 15}


class RuleScope(str, enum.Enum):
    GLOBAL = "global"
    PROJECT = "project"
    CAMPAIGN = "campaign"


class LinkPlacementRule(Base, TimestampMixin, UpdatedAtMixin):
    __tablename__ = "link_placement_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    scope: Mapped[RuleScope] = mapped_column(sa_enum(RuleScope, "rule_scope"))
    scope_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    anchor_distribution: Mapped[dict] = mapped_column(
        JSONType, default=lambda: dict(DEFAULT_ANCHOR_DISTRIBUTION)
    )
    link_position_max_words: Mapped[int] = mapped_column(Integer, default=100)
    max_outbound_links: Mapped[int] = mapped_column(Integer, default=1)
    max_links_per_blog_per_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_days_between_links_same_target: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
