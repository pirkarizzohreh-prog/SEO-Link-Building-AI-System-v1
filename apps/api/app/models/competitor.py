from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Competitor(Base, TimestampMixin):
    __tablename__ = "competitors"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    website_url: Mapped[str] = mapped_column(String(1000))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="competitors")
    pages: Mapped[list["CompetitorPage"]] = relationship(
        back_populates="competitor", cascade="all, delete-orphan"
    )
