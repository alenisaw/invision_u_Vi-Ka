"""add tamper evident audit fields

Revision ID: 8c1f4b7a92de
Revises: 7a3d9b6e4c11
Create Date: 2026-03-30 22:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8c1f4b7a92de"
down_revision: Union[str, None] = "7a3d9b6e4c11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("audit_log", sa.Column("sequence_no", sa.Integer(), nullable=True))
    op.add_column("audit_log", sa.Column("prev_hash", sa.String(length=128), nullable=True))
    op.add_column("audit_log", sa.Column("event_hash", sa.String(length=128), nullable=True))
    op.add_column("audit_log", sa.Column("signature_version", sa.String(length=20), nullable=True))
    op.create_index(op.f("ix_audit_log_sequence_no"), "audit_log", ["sequence_no"], unique=False)
    op.create_index(op.f("ix_audit_log_event_hash"), "audit_log", ["event_hash"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_log_event_hash"), table_name="audit_log")
    op.drop_index(op.f("ix_audit_log_sequence_no"), table_name="audit_log")
    op.drop_column("audit_log", "signature_version")
    op.drop_column("audit_log", "event_hash")
    op.drop_column("audit_log", "prev_hash")
    op.drop_column("audit_log", "sequence_no")
