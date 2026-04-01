"""add candidate dedupe_key for deduplication

Revision ID: a1b2c3d4e5f6
Revises: 2c6f3a1e9b42
Create Date: 2026-04-01 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "2c6f3a1e9b42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "candidates",
        sa.Column("dedupe_key", sa.String(64), nullable=True),
    )
    op.create_index("ix_candidates_dedupe_key", "candidates", ["dedupe_key"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_candidates_dedupe_key", table_name="candidates")
    op.drop_column("candidates", "dedupe_key")
