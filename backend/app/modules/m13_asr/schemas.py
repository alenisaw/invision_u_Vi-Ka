"""
File: schemas.py
Purpose: Shared request and response models for the M13 ASR module.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ASRRequest(BaseModel):
    """Input contract for the ASR service."""

    model_config = ConfigDict(extra="ignore")

    candidate_id: UUID
    video_url: str | None = Field(default=None, max_length=2048)
    media_path: str | None = Field(default=None, max_length=500)
    language_hint: str = Field(default="auto", min_length=1, max_length=20)
    selected_program: str = Field(default="", max_length=200)

    @model_validator(mode="after")
    def validate_media_source(self) -> "ASRRequest":
        source_count = int(bool(self.video_url)) + int(bool(self.media_path))
        if source_count != 1:
            raise ValueError("exactly one of video_url or media_path must be provided")
        return self


class ASRSegment(BaseModel):
    """Normalized transcript segment."""

    model_config = ConfigDict(extra="ignore")

    start: float = Field(default=0.0, ge=0.0)
    end: float = Field(default=0.0, ge=0.0)
    text: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    language: str = ""
    is_unclear: bool = False


class ASRQualitySummary(BaseModel):
    """Operational ASR quality metrics and review flags."""

    model_config = ConfigDict(extra="ignore")

    mean_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    unclear_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    audio_duration_seconds: float = Field(default=0.0, ge=0.0)
    flags: list[str] = Field(default_factory=list)
    requires_human_review: bool = False
    review_reasons: list[str] = Field(default_factory=list)


class ASRTranscriptResult(BaseModel):
    """Final M13 output passed to the pipeline."""

    model_config = ConfigDict(extra="ignore")

    candidate_id: UUID
    transcript: str = ""
    segments: list[ASRSegment] = Field(default_factory=list)
    mean_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    unclear_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    detected_languages: list[str] = Field(default_factory=list)
    audio_duration_seconds: float = Field(default=0.0, ge=0.0)
    flags: list[str] = Field(default_factory=list)
    requires_human_review: bool = False
    review_reasons: list[str] = Field(default_factory=list)
    transcriber_backend: str = "groq"
    transcriber_model: str = "whisper-large-v3-turbo"


