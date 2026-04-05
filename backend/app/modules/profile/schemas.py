from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ModelInput(BaseModel):
    """Layer 3 data — redacted, safe for LLM."""

    model_config = ConfigDict(extra="ignore")

    video_transcript: str | None = None
    essay_text: str | None = None
    internal_test_answers: list[dict[str, str]] = Field(default_factory=list)
    project_descriptions: list[str] = Field(default_factory=list)
    experience_summary: str | None = None
    asr_confidence: float | None = None
    asr_flags: list[str] = Field(default_factory=list)


class ProfileMetadata(BaseModel):
    """Layer 2 data — operational metadata."""

    model_config = ConfigDict(extra="ignore")

    age_eligible: bool | None = None
    language_threshold_met: bool | None = None
    language_exam_type: str | None = None
    has_video: bool = False
    data_completeness: float = 0.0
    data_flags: list[str] = Field(default_factory=list)


class CandidateProfile(BaseModel):
    """Unified candidate profile assembled from Layer 2 + Layer 3."""

    model_config = ConfigDict(extra="ignore")

    candidate_id: UUID
    selected_program: str | None = None
    model_input: ModelInput
    metadata: ProfileMetadata
    completeness: float = 0.0
    data_flags: list[str] = Field(default_factory=list)
    created_at: datetime
