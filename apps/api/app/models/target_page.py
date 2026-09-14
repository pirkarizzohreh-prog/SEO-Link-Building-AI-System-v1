from __future__ import annotations

import enum

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import sa_enum
from app.models.mixins import TimestampMixin


class PageType(str, enum.Enum):
    PRODUCT = "product"
    ARTICLE = "article"
    CATEGORY = "category"


class TargetPage(Base, TimestampMixin):
    __tablename__ = "target_pages"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(500))
    url: Mapped[str] = mapped_column(String(1000))
    main_keyword: Mapped[str] = mapped_column(String(500))
    page_type: Mapped[PageType] = mapped_column(sa_enum(PageType, "page_type"), default=PageType.ARTICLE)
    priority: Mapped[int] = mapped_column(Integer, default=0)

    project: Mapped["Project"] = relationship(back_populates="target_pages")
    keywords: Mapped[list["Keyword"]] = relationship(
        back_populates="target_page", cascade="all, delete-orphan"
    )
    anchors: Mapped[list["Anchor"]] = relationship(
        back_populates="target_page", cascade="all, delete-orphan"
    )
    content_gaps: Mapped[list["ContentGap"]] = relationship(
        back_populates="target_page", cascade="all, delete-orphan"
    )
    serp_snapshots: Mapped[list["SerpSnapshot"]] = relationship(
        back_populates="target_page", cascade="all, delete-orphan"
    )
