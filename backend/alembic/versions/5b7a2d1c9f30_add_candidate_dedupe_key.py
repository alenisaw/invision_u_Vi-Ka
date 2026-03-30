"""add candidate dedupe key

Revision ID: 5b7a2d1c9f30
Revises: 2c6f3a1e9b42
Create Date: 2026-03-30 13:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5b7a2d1c9f30"
down_revision: Union[str, None] = "2c6f3a1e9b42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("candidates", sa.Column("dedupe_key", sa.String(length=64), nullable=True))
    op.create_index(
        op.f("ix_candidates_dedupe_key"),
        "candidates",
        ["dedupe_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_candidates_dedupe_key"), table_name="candidates")
    op.drop_column("candidates", "dedupe_key")
