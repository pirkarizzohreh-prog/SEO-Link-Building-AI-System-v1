from __future__ import annotations

from pydantic import BaseModel


class ActionNote(BaseModel):
    """Optional free-text note attached to an approve/reject/publish action."""

    note: str | None = None


class PublishRequest(BaseModel):
    blog_platform_id: int
    published_url: str
    notes: str | None = None


class PublishAutomatedRequest(BaseModel):
    """POST /articles/{id}/publish-automated — Sprint 5. `blog_platform_id`
    is optional; omit it to let `suggest_blog_platform` pick one, same as
    the manual publish-package flow.
    """

    blog_platform_id: int | None = None
