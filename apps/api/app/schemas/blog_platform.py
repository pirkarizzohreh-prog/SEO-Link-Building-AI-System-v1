from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.blog_platform import BlogPlatformStatus


class BlogPlatformBase(BaseModel):
    name: str
    url: str
    status: BlogPlatformStatus = BlogPlatformStatus.ACTIVE
    username: str | None = None
    login_url: str | None = None
    category_default: str | None = None


class BlogPlatformCreate(BlogPlatformBase):
    pass


class BlogPlatformUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    status: BlogPlatformStatus | None = None
    username: str | None = None
    login_url: str | None = None
    category_default: str | None = None


# Note: `password_encrypted` is deliberately not accepted through any Sprint 1
# schema. Writing a credential requires the KMS/Fernet encryption-at-rest
# path documented in docs/DATABASE_SCHEMA.md, which lands with the
# automation login flow in Sprint 5 — never as a plain string via this API.


class BlogPlatformRead(BlogPlatformBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    last_publish_date: datetime | None = None
    created_at: datetime
