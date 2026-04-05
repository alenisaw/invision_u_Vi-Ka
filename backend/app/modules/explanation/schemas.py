"""
File: schemas.py
Purpose: Shared handoff and output models for the explanation stage.
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ExplanationSeverity = Literal["advisory", "warning", "critical"]
RecommendationStatus = Literal["STRONG_RECOMMEND", "RECOMMEND", "WAITLIST", "DECLINED"]
ReviewRecommendation = Literal["FAST_TRACK_REVIEW", "STANDARD_REVIEW", "REQUIRES_MANUAL_REVIEW"]


class ExplanationSignalContext(BaseModel):
    """Normalized signal context passed from extraction through scoring into explanation."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    value: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    source: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    reasoning: str = ""


class ExplanationFactor(BaseModel):
    """Positive factor derived from scoring contributions."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    factor: str
    sub_score: str
    score: float = Field(..., ge=0.0, le=1.0)
    score_contribution: float = Field(..., ge=0.0, le=0.25)


class ExplanationCautionFlag(BaseModel):
    """Normalized caution item for explanation formatting."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    flag: str
    severity: ExplanationSeverity = "advisory"
    reason: str


class ExplanationInput(BaseModel):
    """Canonical handoff payload from scoring to explanation."""

    model_config = ConfigDict(extra="ignore")

    candidate_id: UUID
    scoring_version: str
    selected_program: str = ""
    program_id: str = ""
    recommendation_status: RecommendationStatus
    review_priority_index: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    uncertainty_flag: bool = False
    manual_review_required: bool = False
    human_in_loop_required: bool = False
    review_recommendation: ReviewRecommendation = "STANDARD_REVIEW"
    review_reasons: list[str] = Field(default_factory=list)
    sub_scores: dict[str, float]
    score_breakdown: dict[str, float]
    positive_factors: list[ExplanationFactor] = Field(default_factory=list)
    caution_flags: list[ExplanationCautionFlag] = Field(default_factory=list)
    signal_context: dict[str, ExplanationSignalContext] = Field(default_factory=dict)
    data_quality_notes: list[str] = Field(default_factory=list)


class EvidenceItem(BaseModel):
    """One reviewer-facing evidence item."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    source: str
    quote: str


class FactorBlock(BaseModel):
    """UI-facing positive factor block."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    factor: str
    title: str
    summary: str
    score: float = Field(..., ge=0.0, le=1.0)
    score_contribution: float = Field(..., ge=0.0, le=0.25)
    evidence: list[EvidenceItem] = Field(default_factory=list)


class CautionBlock(BaseModel):
    """UI-facing caution block."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    flag: str
    severity: ExplanationSeverity
    title: str
    summary: str
    suggested_action: str


class ExplanationReport(BaseModel):
    """Final reviewer-facing explanation output."""

    model_config = ConfigDict(extra="ignore")

    candidate_id: UUID
    scoring_version: str
    selected_program: str = ""
    program_id: str = ""
    recommendation_status: RecommendationStatus
    review_priority_index: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    manual_review_required: bool = False
    human_in_loop_required: bool = False
    review_recommendation: ReviewRecommendation = "STANDARD_REVIEW"
    summary: str
    positive_factors: list[FactorBlock] = Field(default_factory=list)
    caution_blocks: list[CautionBlock] = Field(default_factory=list)
    reviewer_guidance: str = ""
    data_quality_notes: list[str] = Field(default_factory=list)
