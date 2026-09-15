from __future__ import annotations

from pydantic import BaseModel


class ActionNote(BaseModel):
    """Optional free-text note attached to an approve/reject/publish action."""

    note: str | None = None


class PublishRequest(BaseModel):
    blog_platform_id: int
    published_url: str
    notes: str | None = None
