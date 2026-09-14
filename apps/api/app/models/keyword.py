from __future__ import annotations

import enum

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import sa_enum
from app.models.mixins import TimestampMixin


class KeywordType(str, enum.Enum):
    MAIN = "main"
    RELATED = "related"
    SEMANTIC = "semantic"


class KeywordSource(str, enum.Enum):
    AI = "ai"
    MANUAL = "manual"


class Keyword(Base, TimestampMixin):
    __tablename__ = "keywords"

    id: Mapped[int] = mapped_column(primary_key=True)
    target_page_id: Mapped[int] = mapped_column(ForeignKey("target_pages.id", ondelete="CASCADE"))
    keyword: Mapped[str] = mapped_column(String(500))
    type: Mapped[KeywordType] = mapped_column(sa_enum(KeywordType, "keyword_type"), default=KeywordType.RELATED)
    source: Mapped[KeywordSource] = mapped_column(
        sa_enum(KeywordSource, "keyword_source"), default=KeywordSource.MANUAL
    )

    target_page: Mapped["TargetPage"] = relationship(back_populates="keywords")
