"""expand reviewer payload persistence

Revision ID: 2c6f3a1e9b42
Revises: edc8df0417b4
Create Date: 2026-03-29 21:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "2c6f3a1e9b42"
down_revision: Union[str, None] = "edc8df0417b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("candidate_scores", sa.Column("program_id", sa.String(length=120), nullable=True))
    op.add_column(
        "candidate_scores",
        sa.Column("program_weight_profile", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column("candidate_scores", sa.Column("decision_summary", sa.Text(), nullable=True))
    op.add_column("candidate_scores", sa.Column("confidence_band", sa.String(length=20), nullable=True))
    op.add_column("candidate_scores", sa.Column("manual_review_required", sa.Boolean(), nullable=True))
    op.add_column("candidate_scores", sa.Column("human_in_loop_required", sa.Boolean(), nullable=True))
    op.add_column("candidate_scores", sa.Column("uncertainty_flag", sa.Boolean(), nullable=True))
    op.add_column("candidate_scores", sa.Column("review_recommendation", sa.String(length=50), nullable=True))
    op.add_column(
        "candidate_scores",
        sa.Column("review_reasons", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "candidate_scores",
        sa.Column("top_strengths", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "candidate_scores",
        sa.Column("top_risks", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column("candidate_scores", sa.Column("score_delta_vs_baseline", sa.Float(), nullable=True))
    op.add_column(
        "candidate_scores",
        sa.Column("caution_flags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "candidate_scores",
        sa.Column("score_breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column("candidate_scores", sa.Column("model_family", sa.String(length=50), nullable=True))
    op.add_column(
        "candidate_scores",
        sa.Column("score_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index(
        op.f("ix_candidate_scores_manual_review_required"),
        "candidate_scores",
        ["manual_review_required"],
        unique=False,
    )
    op.create_index(
        op.f("ix_candidate_scores_review_recommendation"),
        "candidate_scores",
        ["review_recommendation"],
        unique=False,
    )
    op.create_index(
        op.f("ix_candidate_scores_uncertainty_flag"),
        "candidate_scores",
        ["uncertainty_flag"],
        unique=False,
    )

    op.add_column("candidate_explanations", sa.Column("scoring_version", sa.String(length=50), nullable=True))
    op.add_column("candidate_explanations", sa.Column("program_id", sa.String(length=120), nullable=True))
    op.add_column("candidate_explanations", sa.Column("recommendation_status", sa.String(length=50), nullable=True))
    op.add_column("candidate_explanations", sa.Column("review_priority_index", sa.Float(), nullable=True))
    op.add_column("candidate_explanations", sa.Column("confidence", sa.Float(), nullable=True))
    op.add_column("candidate_explanations", sa.Column("manual_review_required", sa.Boolean(), nullable=True))
    op.add_column("candidate_explanations", sa.Column("human_in_loop_required", sa.Boolean(), nullable=True))
    op.add_column("candidate_explanations", sa.Column("review_recommendation", sa.String(length=50), nullable=True))
    op.add_column(
        "candidate_explanations",
        sa.Column("report_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("candidate_explanations", "report_payload")
    op.drop_column("candidate_explanations", "review_recommendation")
    op.drop_column("candidate_explanations", "human_in_loop_required")
    op.drop_column("candidate_explanations", "manual_review_required")
    op.drop_column("candidate_explanations", "confidence")
    op.drop_column("candidate_explanations", "review_priority_index")
    op.drop_column("candidate_explanations", "recommendation_status")
    op.drop_column("candidate_explanations", "program_id")
    op.drop_column("candidate_explanations", "scoring_version")

    op.drop_index(op.f("ix_candidate_scores_uncertainty_flag"), table_name="candidate_scores")
    op.drop_index(op.f("ix_candidate_scores_review_recommendation"), table_name="candidate_scores")
    op.drop_index(op.f("ix_candidate_scores_manual_review_required"), table_name="candidate_scores")
    op.drop_column("candidate_scores", "score_payload")
    op.drop_column("candidate_scores", "model_family")
    op.drop_column("candidate_scores", "score_breakdown")
    op.drop_column("candidate_scores", "caution_flags")
    op.drop_column("candidate_scores", "score_delta_vs_baseline")
    op.drop_column("candidate_scores", "top_risks")
    op.drop_column("candidate_scores", "top_strengths")
    op.drop_column("candidate_scores", "review_reasons")
    op.drop_column("candidate_scores", "review_recommendation")
    op.drop_column("candidate_scores", "uncertainty_flag")
    op.drop_column("candidate_scores", "human_in_loop_required")
    op.drop_column("candidate_scores", "manual_review_required")
    op.drop_column("candidate_scores", "confidence_band")
    op.drop_column("candidate_scores", "decision_summary")
    op.drop_column("candidate_scores", "program_weight_profile")
    op.drop_column("candidate_scores", "program_id")
