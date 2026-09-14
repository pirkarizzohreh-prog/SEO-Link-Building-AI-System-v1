from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.blog_platform import BlogPlatform
from app.schemas.blog_platform import BlogPlatformCreate, BlogPlatformRead, BlogPlatformUpdate
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
