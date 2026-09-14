"""A small generic repository used by the Sprint 1 CRUD routers.

This intentionally covers only plain create/read/update/delete against a
single table with simple equality filters. Anything with actual business
logic (state transitions, AI calls, resolving link_placement_rules, the
Human Approval Layer, ...) is implemented explicitly in its own router/
service function rather than being squeezed into this helper — see
docs/AI_WORKFLOW.md for what belongs where and in which sprint.
"""

from __future__ import annotations

from typing import Any, Generic, Type, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

ModelT = TypeVar("ModelT")


class CRUDBase(Generic[ModelT]):
    def __init__(self, model: Type[ModelT]):
        self.model = model

    def get(self, db: Session, id_: int) -> ModelT:
        obj = db.get(self.model, id_)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} {id_} not found",
            )
        return obj

    def list(self, db: Session, *, skip: int = 0, limit: int = 50, **filters: Any) -> list[ModelT]:
        stmt = select(self.model)
        for field, value in filters.items():
            if value is not None:
                stmt = stmt.where(getattr(self.model, field) == value)
        stmt = stmt.offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def create(self, db: Session, obj_in: BaseModel, **extra: Any) -> ModelT:
        data = obj_in.model_dump()
        data.update(extra)
        obj = self.model(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, id_: int, obj_in: BaseModel) -> ModelT:
        obj = self.get(db, id_)
        for field, value in obj_in.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, id_: int) -> None:
        obj = self.get(db, id_)
        db.delete(obj)
        db.commit()
