from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PipelineStageRunView(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    stage_name: str
    status: str
    attempt_count: int
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: int | None = None
    error_code: str | None = None
    error_message: str | None = None
    output_ref: dict | None = None
    created_at: datetime


class PipelineJobEventView(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    event_type: str
    stage_name: str | None = None
    status: str | None = None
    payload: dict
    created_at: datetime


class PipelineJobStatusView(BaseModel):
    model_config = ConfigDict(extra="ignore")

    job_id: str
    candidate_id: str
    job_type: str
    status: str
    current_stage: str | None = None
    requested_by: str
    execution_mode: str
    attempt_count: int
    error_code: str | None = None
    error_message: str | None = None
    queued_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    payload_schema_version: str | None = None
    stage_runs: list[PipelineStageRunView]


class AsyncPipelineSubmitResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    candidate_id: str
    job_id: str
    pipeline_status: str
    job_status: str
    current_stage: str | None = None
    message: str


class CandidatePipelineStatusView(BaseModel):
    model_config = ConfigDict(extra="ignore")

    candidate_id: str
    pipeline_status: str
    selected_program: str | None = None
    latest_job: PipelineJobStatusView | None = None
