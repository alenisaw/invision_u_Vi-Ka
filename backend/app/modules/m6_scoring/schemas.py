"""
File: schemas.py
Purpose: Shared Pydantic models for the M6 scoring module.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SignalPayload(BaseModel):
    """Structured signal produced by the NLP pipeline."""

    model_config = ConfigDict(extra="ignore")

    value: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    source: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    reasoning: str = ""


class SignalEnvelope(BaseModel):
    """Canonical M5 -> M6 contract."""

    model_config = ConfigDict(extra="ignore")

    candidate_id: UUID
    signal_schema_version: str = Field(..., min_length=1)
    m5_model_version: str = Field(default="unknown", min_length=1)
    selected_program: str = Field(default="", max_length=200)
    program_id: str = Field(default="", min_length=0, max_length=120)
    completeness: float = Field(..., ge=0.0, le=1.0)
    data_flags: list[str] = Field(default_factory=list)
    signals: dict[str, SignalPayload] = Field(default_factory=dict)


class CandidateScore(BaseModel):
    """Final M6 output for one candidate."""

    candidate_id: UUID
    selected_program: str = ""
    program_id: str = ""
    sub_scores: dict[str, float]
    program_weight_profile: dict[str, float] = Field(default_factory=dict)
    review_priority_index: float = Field(..., ge=0.0, le=1.0)
    score_status: str = ""
    recommendation_status: str
    decision_summary: str = ""
    confidence: float = Field(..., ge=0.0, le=1.0)
    confidence_band: str = "MEDIUM"
    manual_review_required: bool = False
    human_in_loop_required: bool = False
    uncertainty_flag: bool = False
    shortlist_eligible: bool = False
    review_recommendation: str = "STANDARD_REVIEW"
    review_reasons: list[str] = Field(default_factory=list)
    top_strengths: list[str] = Field(default_factory=list)
    top_risks: list[str] = Field(default_factory=list)
    score_delta_vs_baseline: float = 0.0
    ranking_position: int | None = None
    caution_flags: list[str] = Field(default_factory=list)
    score_breakdown: dict[str, float] = Field(default_factory=dict)
    model_family: str = "gbr"
    scoring_version: str = "m6-v1"


class LabeledEnvelope(BaseModel):
    """Synthetic sample used to train or validate the ML layer."""

    envelope: SignalEnvelope
    profile_type: str = "unknown"
    target_rpi: float = Field(..., ge=0.0, le=1.0)


# File summary: schemas.py
# Stores compact shared models for M6 input, output, and synthetic labels.
