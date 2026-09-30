"""add groq to llm_provider enum

Revision ID: 118197ab0fed
Revises: c66fb88c10c2
Create Date: 2026-09-30 12:53:28.136259

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '118197ab0fed'
down_revision: Union[str, None] = 'c66fb88c10c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE cannot run inside Alembic's normal
    # transactional DDL block on Postgres, hence autocommit_block().
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE llm_provider ADD VALUE IF NOT EXISTS 'groq'")


def downgrade() -> None:
    # Postgres has no ALTER TYPE ... DROP VALUE; removing an enum value
    # safely means rebuilding the type and rewriting every row using it.
    # Not worth it for one additive, non-breaking option — downgrading
    # past this revision just leaves 'groq' as an unused, harmless value.
    pass
