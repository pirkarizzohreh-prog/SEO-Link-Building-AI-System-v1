"""Writer for the Advanced Content Status Workflow's audit trail — see
docs/AI_WORKFLOW.md and docs/DATABASE_SCHEMA.md (`content_status_history`).

`record_transition` is deliberately generic (entity_table/entity_id, not a
FK) so it can log topics, content_briefs and articles alike without a
migration per entity type.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.content_status_history import ActorType, ContentStatusHistory, PipelineStage
from app.models.user import User


def record_transition(
    db: Session,
    *,
    entity_table: str,
    entity_id: int,
    stage: PipelineStage,
    from_status: str | None,
    to_status: str,
    actor: User | None,
    note: str | None = None,
) -> ContentStatusHistory:
    entry = ContentStatusHistory(
        entity_table=entity_table,
        entity_id=entity_id,
        stage=stage,
        from_status=from_status,
        to_status=to_status,
        actor_type=ActorType.USER if actor is not None else ActorType.AI,
        actor_id=actor.id if actor is not None else None,
        note=note,
    )
    db.add(entry)
    db.flush()
    return entry
