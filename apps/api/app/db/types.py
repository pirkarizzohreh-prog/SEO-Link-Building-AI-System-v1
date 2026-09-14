"""Cross-dialect column type helpers.

Production runs on PostgreSQL (JSONB, native enum types); the test suite
runs against SQLite for speed. These helpers keep model definitions
dialect-agnostic without sacrificing the PostgreSQL-specific behaviour
documented in docs/DATABASE_SCHEMA.md.
"""

from __future__ import annotations

from enum import Enum
from typing import Type

from sqlalchemy import JSON
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB

# JSONB on Postgres, plain JSON on SQLite (used only by tests).
JSONType = JSONB().with_variant(JSON(), "sqlite")


def sa_enum(enum_cls: Type[Enum], name: str) -> SAEnum:
    """Build a SQLAlchemy Enum column type that stores the *value* of each
    Python enum member (e.g. "active") rather than SQLAlchemy's default of
    the member *name* (e.g. "ACTIVE") — matching the lowercase string
    values used throughout docs/DATABASE_SCHEMA.md and the API schemas.
    """

    return SAEnum(enum_cls, name=name, values_callable=lambda e: [member.value for member in e])
