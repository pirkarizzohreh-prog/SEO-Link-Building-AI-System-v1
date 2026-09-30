from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.crypto import encrypt_secret
from app.db.session import get_db
from app.models.blog_platform import BlogPlatform
from app.models.user import User
from app.schemas.blog_platform import BlogPlatformCreate, BlogPlatformCredentials, BlogPlatformRead, BlogPlatformUpdate
from app.utils.crud import CRUDBase

router = APIRouter(prefix="/blog-platforms", tags=["Blog Platforms"])
crud = CRUDBase(BlogPlatform)


@router.get("", response_model=list[BlogPlatformRead])
def list_blog_platforms(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.list(db, skip=skip, limit=limit)


@router.post("", response_model=BlogPlatformRead, status_code=201)
def create_blog_platform(payload: BlogPlatformCreate, db: Session = Depends(get_db)):
    return crud.create(db, payload)


@router.put("/{blog_platform_id}", response_model=BlogPlatformRead)
def update_blog_platform(blog_platform_id: int, payload: BlogPlatformUpdate, db: Session = Depends(get_db)):
    return crud.update(db, blog_platform_id, payload)


@router.delete("/{blog_platform_id}", status_code=204)
def delete_blog_platform(blog_platform_id: int, db: Session = Depends(get_db)):
    crud.delete(db, blog_platform_id)


@router.post("/{blog_platform_id}/credentials", response_model=BlogPlatformRead)
def set_blog_platform_credentials(
    blog_platform_id: int,
    payload: BlogPlatformCredentials,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Sprint 5 — the only way to set a blog's automation login. Admin-only:
    this is a real credential, not ordinary CRUD content.
    """
    blog_platform = crud.get(db, blog_platform_id)
    blog_platform.username = payload.username
    blog_platform.password_encrypted = encrypt_secret(payload.password)
    if payload.login_url is not None:
        blog_platform.login_url = payload.login_url
    db.commit()
    db.refresh(blog_platform)
    return blog_platform
