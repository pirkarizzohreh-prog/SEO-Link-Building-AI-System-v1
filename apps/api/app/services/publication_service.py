"""Publication Manager, version one (MVP/manual) — see docs/AI_WORKFLOW.md.

The automated Playwright path is Sprint 5; this module only builds the
"ready to publish" package and picks a suggested blog platform.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.blog_platform import BlogPlatform, BlogPlatformStatus


def suggest_blog_platform(db: Session) -> BlogPlatform | None:
    """Least-recently-used among active blog platforms (NULLs — never
    published to — sort first).
    """
    stmt = (
        select(BlogPlatform)
        .where(BlogPlatform.status == BlogPlatformStatus.ACTIVE)
        .order_by(BlogPlatform.last_publish_date.asc().nulls_first())
        .limit(1)
    )
    return db.scalars(stmt).first()
