from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, RootModel

from app.modules.m6_scoring.schemas import CandidateScore as CandidateScorePayload
from app.modules.m7_explainability.schemas import (
    ExplainabilityReport,
    RecommendationStatus,
)


def _default_status_counts() -> dict[RecommendationStatus, int]:
    return {
        "STRONG_RECOMMEND": 0,
        "RECOMMEND": 0,
        "WAITLIST": 0,
        "DECLINED": 0,
    }


class DashboardStatsResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    total_candidates: int = 0
    processed: int = 0
    shortlisted: int = 0
    pending_review: int = 0
    avg_confidence: float = 0.0
    by_status: dict[RecommendationStatus, int] = Field(default_factory=_default_status_counts)


class ReviewerCandidateIdentity(BaseModel):
    model_config = ConfigDict(extra="ignore")

    candidate_id: UUID
    name: str


class DashboardCandidateListItem(ReviewerCandidateIdentity):
    model_config = ConfigDict(extra="ignore")

    selected_program: str = ""
    review_priority_index: float = 0.0
    recommendation_status: RecommendationStatus
    confidence: float = 0.0
    shortlist_eligible: bool = False
    ranking_position: int | None = None
    top_strengths: list[str] = Field(default_factory=list)
    caution_flags: list[str] = Field(default_factory=list)
    created_at: datetime


class DashboardCandidatePoolItem(ReviewerCandidateIdentity):
    model_config = ConfigDict(extra="ignore")

    selected_program: str = ""
    pipeline_status: str = "pending"
    stage: str = "raw"
    data_completeness: float | None = None
    data_flags: list[str] = Field(default_factory=list)
    review_priority_index: float | None = None
    recommendation_status: RecommendationStatus | None = None
    confidence: float | None = None
    shortlist_eligible: bool = False
    ranking_position: int | None = None
    top_strengths: list[str] = Field(default_factory=list)
    caution_flags: list[str] = Field(default_factory=list)
    created_at: datetime


class RawCandidateContent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    essay_text: str | None = None
    video_transcript: str | None = None


class ReviewerActionItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    candidate_id: UUID
    reviewer_id: str
    action_type: str
    previous_status: str | None = None
    new_status: str | None = None
    comment: str | None = None
    created_at: datetime


class CommitteeMemberStatus(BaseModel):
    model_config = ConfigDict(extra="ignore")

    user_id: UUID
    full_name: str
    role: str
    has_viewed: bool = False
    has_recommendation: bool = False
    recommendation_status: RecommendationStatus | None = None
    recommendation_comment: str | None = None
    last_activity_at: datetime | None = None


class DashboardCandidateDetailResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    candidate_id: UUID
    name: str
    score: CandidateScorePayload
    explanation: ExplainabilityReport
    raw_content: RawCandidateContent | None = None
    audit_logs: list[ReviewerActionItem] = Field(default_factory=list)
    committee_members: list[CommitteeMemberStatus] = Field(default_factory=list)


class DashboardShortlistResponse(RootModel[list[DashboardCandidateListItem]]):
    root: list[DashboardCandidateListItem]
