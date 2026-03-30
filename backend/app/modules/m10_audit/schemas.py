from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.m7_explainability.schemas import RecommendationStatus

ReviewerActionType = Literal["comment", "shortlist_add", "shortlist_remove", "override"]


class CandidateOverrideRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    new_status: RecommendationStatus
    comment: str = Field(..., min_length=1, max_length=5000)


class ReviewerActionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    action_type: Literal["comment", "shortlist_add", "shortlist_remove"]
    comment: str = Field(..., min_length=1, max_length=5000)


class ReviewerActionResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    candidate_id: UUID
    reviewer_id: str
    action_type: ReviewerActionType
    previous_status: str = ""
    new_status: str = ""
    comment: str = ""
    created_at: datetime


class AuditFeedItemResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    entity_type: str
    entity_id: UUID | None = None
    candidate_id: UUID | None = None
    action_type: str
    actor: str
    reviewer_id: str | None = None
    previous_status: str | None = None
    new_status: str | None = None
    comment: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
