"""normalize reviewer action identity

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-04 23:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "reviewer_actions",
        sa.Column("reviewer_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "reviewer_actions",
        sa.Column("reviewer_name", sa.String(length=255), nullable=True),
    )
    op.create_index(
        op.f("ix_reviewer_actions_reviewer_user_id"),
        "reviewer_actions",
        ["reviewer_user_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_reviewer_actions_reviewer_user_id_users",
        "reviewer_actions",
        "users",
        ["reviewer_user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.execute("UPDATE reviewer_actions SET reviewer_name = reviewer_id WHERE reviewer_name IS NULL")
    op.execute(
        """
        UPDATE reviewer_actions AS ra
        SET reviewer_user_id = users.id
        FROM users
        WHERE ra.reviewer_user_id IS NULL
          AND (
            lower(trim(ra.reviewer_id)) = lower(trim(users.email))
            OR lower(trim(coalesce(ra.reviewer_name, ra.reviewer_id))) = lower(trim(users.full_name))
          )
        """
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_reviewer_actions_reviewer_user_id_users",
        "reviewer_actions",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_reviewer_actions_reviewer_user_id"), table_name="reviewer_actions")
    op.drop_column("reviewer_actions", "reviewer_name")
    op.drop_column("reviewer_actions", "reviewer_user_id")
