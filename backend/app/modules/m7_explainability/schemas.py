"""
File: schemas.py
Purpose: Shared handoff models for the future M7 explainability module.

Notes:
- These models define the M6 -> M7 boundary before M7 logic exists.
- M7 should explain scores, not recompute them.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ExplainabilitySignalContext(BaseModel):
    """Normalized signal context passed from M5 through M6 into M7."""

    model_config = ConfigDict(extra="ignore")

    value: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    source: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    reasoning: str = ""


class ExplainabilityFactor(BaseModel):
    """Positive factor derived from M6 score contributions."""

    factor: str
    sub_score: str
    score: float = Field(..., ge=0.0, le=1.0)
    score_contribution: float = Field(..., ge=0.0, le=1.0)


class ExplainabilityCautionFlag(BaseModel):
    """Normalized caution item for M7 formatting."""

    flag: str
    severity: str = "advisory"
    reason: str


class ExplainabilityInput(BaseModel):
    """Canonical handoff payload from M6 to M7."""

    candidate_id: UUID
    scoring_version: str
    recommendation_status: str
    review_priority_index: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    uncertainty_flag: bool = False
    sub_scores: dict[str, float]
    score_breakdown: dict[str, float]
    positive_factors: list[ExplainabilityFactor] = Field(default_factory=list)
    caution_flags: list[ExplainabilityCautionFlag] = Field(default_factory=list)
    signal_context: dict[str, ExplainabilitySignalContext] = Field(default_factory=dict)
    data_quality_notes: list[str] = Field(default_factory=list)


# File summary: schemas.py
# Declares the future M6 -> M7 handoff contract as Pydantic models.
