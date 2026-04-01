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


class RawCandidateContent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    essay_text: str | None = None
    video_transcript: str | None = None
    project_descriptions: list[str] = Field(default_factory=list)
    experience_summary: str | None = None


class DashboardCandidateDetailResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    candidate_id: UUID
    name: str
    score: CandidateScorePayload
    explanation: ExplainabilityReport
    raw_content: RawCandidateContent | None = None


class DashboardShortlistResponse(RootModel[list[DashboardCandidateListItem]]):
    root: list[DashboardCandidateListItem]
