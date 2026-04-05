from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.auth.schemas import RoleLiteral


class AdminUserCreateRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=1, max_length=255)
    role: RoleLiteral
    is_active: bool = True

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("full_name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip()


class AdminUserUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    password: str | None = Field(default=None, min_length=1, max_length=255)
    role: RoleLiteral | None = None
    is_active: bool | None = None

    @field_validator("full_name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    role: RoleLiteral
    is_active: bool
    last_login_at: datetime | None = None
    created_at: datetime


class PipelineMetricsOverviewResponse(BaseModel):
    total_runs: int
    healthy_runs: int
    degraded_runs: int
    partial_runs: int
    manual_review_runs: int
    degraded_rate: float
    manual_review_rate: float
    avg_total_latency_ms: float
    p50_total_latency_ms: float
    p95_total_latency_ms: float
    avg_stage_latencies_ms: dict[str, float] = Field(default_factory=dict)
    fallback_counts: dict[str, int] = Field(default_factory=dict)
    quality_flag_counts: dict[str, int] = Field(default_factory=dict)


class PipelineRunMetricResponse(BaseModel):
    audit_id: UUID
    candidate_id: UUID | None = None
    recommendation_status: str | None = None
    pipeline_quality_status: str
    quality_flags: list[str] = Field(default_factory=list)
    total_latency_ms: float
    stage_latencies_ms: dict[str, float] = Field(default_factory=dict)
    created_at: datetime
    details: dict[str, Any] = Field(default_factory=dict)


class PipelineMetricsResponse(BaseModel):
    overview: PipelineMetricsOverviewResponse
    recent_runs: list[PipelineRunMetricResponse] = Field(default_factory=list)
