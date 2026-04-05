"""Create the current admissions schema baseline.

Revision ID: d4e5f6a7b8c9
Revises:
Create Date: 2026-04-05 23:40:00
"""

from __future__ import annotations

from alembic import op

from app.core.database import Base
from app.modules.storage import models  # noqa: F401


# revision identifiers, used by Alembic.
revision = "d4e5f6a7b8c9"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the full current schema from SQLAlchemy metadata."""

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    """Drop the full current schema in reverse dependency order."""

    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
