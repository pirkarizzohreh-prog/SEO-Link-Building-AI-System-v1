from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import sa_enum
from app.models.anchor import AnchorType


class AnchorUsageLog(Base):
    """Append-only log of anchor usage, used to enforce the anchor
    distribution ratio resolved from `link_placement_rules` (see
    docs/AI_WORKFLOW.md, Stage: Writing).
    """

    __tablename__ = "anchor_usage_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    anchor_id: Mapped[int] = mapped_column(ForeignKey("anchors.id", ondelete="CASCADE"))
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"))
    anchor_type: Mapped[AnchorType] = mapped_column(sa_enum(AnchorType, "anchor_type"))
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    anchor: Mapped["Anchor"] = relationship(back_populates="usage_logs")
    article: Mapped["Article"] = relationship(back_populates="anchor_usage_log")
