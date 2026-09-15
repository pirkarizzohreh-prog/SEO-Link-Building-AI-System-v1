"""The Human Approval Layer's only writer — see docs/AI_WORKFLOW.md
("Stage: Human Review") and docs/DATABASE_SCHEMA.md (`approvals` is
append-only, `decided_by` is never NULL).

No AI job, worker, or agent ever imports this module: it is called
exclusively from routes that depend on `get_current_user`, so every
`Approval` row traces back to a real, authenticated person.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.approval import Approval, ApprovalDecision, ApprovalType
from app.models.user import User


def record_approval(
    db: Session,
    *,
    entity_table: str,
    entity_id: int,
    approval_type: ApprovalType,
    decision: ApprovalDecision,
    decided_by: User,
    note: str | None = None,
) -> Approval:
    approval = Approval(
        entity_table=entity_table,
        entity_id=entity_id,
        approval_type=approval_type,
        decision=decision,
        decided_by=decided_by.id,
        note=note,
    )
    db.add(approval)
    db.flush()  # gets us approval.id without ending the caller's transaction
    return approval
