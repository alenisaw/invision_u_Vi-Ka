"""
File: schemas.py
Purpose: Request models for the M5 NLP signal extraction service.
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class InternalTestAnswer(BaseModel):
    """One normalized internal test answer."""

    model_config = ConfigDict(extra="ignore")

    question_id: str = Field(default="unknown")
    answer_text: str = ""

    @model_validator(mode="before")
    @classmethod
    def coerce_answer_text(cls, value: object) -> object:
        """Accept both `answer` and `answer_text` payloads."""

        if not isinstance(value, dict):
            return value

        normalized = dict(value)
        if "answer_text" not in normalized and "answer" in normalized:
            normalized["answer_text"] = normalized["answer"]
        return normalized


class M5ExtractionRequest(BaseModel):
    """Safe model-input payload consumed by the NLP extraction module."""

    model_config = ConfigDict(extra="ignore")

    candidate_id: UUID = Field(default_factory=uuid4)
    signal_schema_version: str = Field(default="v1", min_length=1)
    m5_model_version: str = Field(default="heuristic-groq-v1", min_length=1)
    completeness: float = Field(default=1.0, ge=0.0, le=1.0)
    data_flags: list[str] = Field(default_factory=list)
    selected_program: str = Field(default="", max_length=200)
    essay_text: str = Field(default="", max_length=12000)
    video_transcript: str = Field(default="", max_length=24000)
    interview_media_path: str | None = Field(default=None, max_length=500)
    experience_summary: str = Field(default="", max_length=6000)
    project_descriptions: list[str] = Field(default_factory=list)
    internal_test_answers: list[InternalTestAnswer] = Field(default_factory=list)
    language: Literal["auto", "en", "ru"] = Field(default="auto")


# File summary: schemas.py
# Defines the request shape for M5 extraction and transcription orchestration.
