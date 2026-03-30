"""add pipeline job tracking

Revision ID: 7a3d9b6e4c11
Revises: 5b7a2d1c9f30
Create Date: 2026-03-30 21:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "7a3d9b6e4c11"
down_revision: Union[str, None] = "5b7a2d1c9f30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pipeline_jobs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("candidate_id", sa.UUID(), nullable=False),
        sa.Column("job_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("current_stage", sa.String(length=50), nullable=True),
        sa.Column("execution_mode", sa.String(length=20), nullable=False),
        sa.Column("requested_by", sa.String(length=100), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("payload_schema_version", sa.String(length=50), nullable=True),
        sa.Column("payload_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column("queued_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pipeline_jobs_candidate_id"), "pipeline_jobs", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_pipeline_jobs_current_stage"), "pipeline_jobs", ["current_stage"], unique=False)
    op.create_index(op.f("ix_pipeline_jobs_status"), "pipeline_jobs", ["status"], unique=False)

    op.create_table(
        "pipeline_stage_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("stage_name", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("output_ref", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["pipeline_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pipeline_stage_runs_job_id"), "pipeline_stage_runs", ["job_id"], unique=False)
    op.create_index(op.f("ix_pipeline_stage_runs_stage_name"), "pipeline_stage_runs", ["stage_name"], unique=False)
    op.create_index(op.f("ix_pipeline_stage_runs_status"), "pipeline_stage_runs", ["status"], unique=False)

    op.create_table(
        "pipeline_job_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("stage_name", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["pipeline_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pipeline_job_events_event_type"), "pipeline_job_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_pipeline_job_events_job_id"), "pipeline_job_events", ["job_id"], unique=False)
    op.create_index(op.f("ix_pipeline_job_events_stage_name"), "pipeline_job_events", ["stage_name"], unique=False)
    op.create_index(op.f("ix_pipeline_job_events_status"), "pipeline_job_events", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_pipeline_job_events_status"), table_name="pipeline_job_events")
    op.drop_index(op.f("ix_pipeline_job_events_stage_name"), table_name="pipeline_job_events")
    op.drop_index(op.f("ix_pipeline_job_events_job_id"), table_name="pipeline_job_events")
    op.drop_index(op.f("ix_pipeline_job_events_event_type"), table_name="pipeline_job_events")
    op.drop_table("pipeline_job_events")

    op.drop_index(op.f("ix_pipeline_stage_runs_status"), table_name="pipeline_stage_runs")
    op.drop_index(op.f("ix_pipeline_stage_runs_stage_name"), table_name="pipeline_stage_runs")
    op.drop_index(op.f("ix_pipeline_stage_runs_job_id"), table_name="pipeline_stage_runs")
    op.drop_table("pipeline_stage_runs")

    op.drop_index(op.f("ix_pipeline_jobs_status"), table_name="pipeline_jobs")
    op.drop_index(op.f("ix_pipeline_jobs_current_stage"), table_name="pipeline_jobs")
    op.drop_index(op.f("ix_pipeline_jobs_candidate_id"), table_name="pipeline_jobs")
    op.drop_table("pipeline_jobs")
