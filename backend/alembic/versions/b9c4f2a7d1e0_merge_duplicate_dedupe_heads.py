"""merge duplicate dedupe key heads

Revision ID: b9c4f2a7d1e0
Revises: 8c1f4b7a92de, a1b2c3d4e5f6
Create Date: 2026-04-02 20:10:00.000000

"""
from typing import Sequence, Union


revision: str = "b9c4f2a7d1e0"
down_revision: Union[str, Sequence[str], None] = ("8c1f4b7a92de", "a1b2c3d4e5f6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
