"""add candidate dedupe_key for deduplication

Revision ID: a1b2c3d4e5f6
Revises: 2c6f3a1e9b42
Create Date: 2026-04-01 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "2c6f3a1e9b42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("candidates")}
    index_names = {index["name"] for index in inspector.get_indexes("candidates")}

    if "dedupe_key" not in columns:
        op.add_column(
            "candidates",
            sa.Column("dedupe_key", sa.String(64), nullable=True),
        )
    if "ix_candidates_dedupe_key" not in index_names:
        op.create_index("ix_candidates_dedupe_key", "candidates", ["dedupe_key"], unique=True)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("candidates")}
    index_names = {index["name"] for index in inspector.get_indexes("candidates")}

    if "ix_candidates_dedupe_key" in index_names:
        op.drop_index("ix_candidates_dedupe_key", table_name="candidates")
    if "dedupe_key" in columns:
        op.drop_column("candidates", "dedupe_key")
