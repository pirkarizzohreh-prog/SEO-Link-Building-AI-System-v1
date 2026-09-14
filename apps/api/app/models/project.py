from __future__ import annotations

import enum

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import sa_enum
from app.models.mixins import TimestampMixin, UpdatedAtMixin


class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Project(Base, TimestampMixin, UpdatedAtMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_name: Mapped[str] = mapped_column(String(255))
    website_url: Mapped[str] = mapped_column(String(500))
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        sa_enum(ProjectStatus, "project_status"), default=ProjectStatus.ACTIVE
    )

    target_pages: Mapped[list["TargetPage"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    knowledge_base: Mapped["ProjectKnowledgeBase | None"] = relationship(
        back_populates="project", uselist=False, cascade="all, delete-orphan"
    )
    competitors: Mapped[list["Competitor"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    campaigns: Mapped[list["Campaign"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    internal_link_suggestions: Mapped[list["InternalLinkSuggestion"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
