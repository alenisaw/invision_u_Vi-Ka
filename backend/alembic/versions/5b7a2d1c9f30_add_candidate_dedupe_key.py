"""add candidate dedupe key

Revision ID: 5b7a2d1c9f30
Revises: 2c6f3a1e9b42
Create Date: 2026-03-30 13:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "5b7a2d1c9f30"
down_revision: Union[str, None] = "2c6f3a1e9b42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("candidates")}
    index_names = {index["name"] for index in inspector.get_indexes("candidates")}
    dedupe_index_name = op.f("ix_candidates_dedupe_key")

    if "dedupe_key" not in columns:
        op.add_column("candidates", sa.Column("dedupe_key", sa.String(length=64), nullable=True))

    if dedupe_index_name not in index_names:
        op.create_index(
            dedupe_index_name,
            "candidates",
            ["dedupe_key"],
            unique=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("candidates")}
    index_names = {index["name"] for index in inspector.get_indexes("candidates")}
    dedupe_index_name = op.f("ix_candidates_dedupe_key")

    if dedupe_index_name in index_names:
        op.drop_index(dedupe_index_name, table_name="candidates")
    if "dedupe_key" in columns:
        op.drop_column("candidates", "dedupe_key")
