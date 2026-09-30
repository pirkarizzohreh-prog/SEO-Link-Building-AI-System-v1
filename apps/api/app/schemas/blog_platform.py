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


# Note: `password_encrypted` is deliberately not accepted through
# BlogPlatformCreate/Update. Writing a credential goes through
# BlogPlatformCredentials -> POST /blog-platforms/{id}/credentials
# (Sprint 5), which encrypts it (app/core/crypto.py) before storing —
# never as a plain string via the general CRUD schemas.


class BlogPlatformCredentials(BaseModel):
    """Sprint 5 — sets the login the Playwright automation uses. Admin-only
    (see the router); the plaintext password is never stored or echoed
    back, only its Fernet-encrypted form.
    """

    username: str
    password: str
    login_url: str | None = None


class BlogPlatformRead(BlogPlatformBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    has_automation_credentials: bool = False
    last_publish_date: datetime | None = None
    created_at: datetime
