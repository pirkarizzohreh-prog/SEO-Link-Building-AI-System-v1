from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.keyword import KeywordSource, KeywordType
from app.models.target_page import PageType


class TargetPageBase(BaseModel):
    title: str
    url: str
    main_keyword: str
    page_type: PageType = PageType.ARTICLE
    priority: int = 0


class TargetPageCreate(TargetPageBase):
    pass


class TargetPageUpdate(BaseModel):
    title: str | None = None
    url: str | None = None
    main_keyword: str | None = None
    page_type: PageType | None = None
    priority: int | None = None


class TargetPageRead(TargetPageBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    created_at: datetime


class KeywordBase(BaseModel):
    keyword: str
    type: KeywordType = KeywordType.RELATED
    source: KeywordSource = KeywordSource.MANUAL


class KeywordCreate(KeywordBase):
    pass


class KeywordRead(KeywordBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    target_page_id: int
    created_at: datetime
