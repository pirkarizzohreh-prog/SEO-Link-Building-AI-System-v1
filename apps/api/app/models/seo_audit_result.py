from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class SeoAuditResult(Base, TimestampMixin):
    __tablename__ = "seo_audit_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"))
    check_name: Mapped[str] = mapped_column(String(255))
    passed: Mapped[bool] = mapped_column(Boolean)
    score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)

    article: Mapped["Article"] = relationship(back_populates="seo_audit_results")
