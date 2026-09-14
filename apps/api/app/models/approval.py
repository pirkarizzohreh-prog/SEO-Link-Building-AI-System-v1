from __future__ import annotations

import enum

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import sa_enum
from app.models.mixins import TimestampMixin


class ApprovalType(str, enum.Enum):
    TOPIC_SELECTION = "topic_selection"
    BRIEF_APPROVAL = "brief_approval"
    PRE_PUBLISH = "pre_publish"


class ApprovalDecision(str, enum.Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


class Approval(Base, TimestampMixin):
    """Append-only Human Approval Layer audit log — see docs/AI_WORKFLOW.md.

    No router writes to this table in Sprint 1: `decided_by` requires a
    real, authenticated user identity, which lands in Sprint 2 (Auth).
    """

    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_table: Mapped[str] = mapped_column(String(100))
    entity_id: Mapped[int] = mapped_column(Integer)
    approval_type: Mapped[ApprovalType] = mapped_column(sa_enum(ApprovalType, "approval_type"))
    decision: Mapped[ApprovalDecision] = mapped_column(sa_enum(ApprovalDecision, "approval_decision"))
    decided_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    decided_by_user: Mapped["User"] = relationship()
