from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.modules.m4_profile.assembler import assemble
from app.modules.m4_profile.schemas import CandidateProfile


def _mock_candidate(**overrides):
    candidate = MagicMock()
    candidate.id = overrides.get("id", uuid4())
    candidate.selected_program = overrides.get("selected_program", "Computer Science")
    candidate.created_at = overrides.get("created_at", datetime.now(timezone.utc))
    return candidate


def _mock_metadata(**overrides):
    meta = MagicMock()
    meta.age_eligible = overrides.get("age_eligible", True)
    meta.language_threshold_met = overrides.get("language_threshold_met", True)
    meta.language_exam_type = overrides.get("language_exam_type", "IELTS")
    meta.has_video = overrides.get("has_video", True)
    meta.data_completeness = overrides.get("data_completeness", 0.85)
    meta.data_flags = overrides.get("data_flags", [])
    return meta


def _mock_model_input(**overrides):
    mi = MagicMock()
    mi.video_transcript = overrides.get("video_transcript", "Transcript text")
    mi.essay_text = overrides.get("essay_text", "A " * 50)  # 50 words
    mi.internal_test_answers = overrides.get("internal_test_answers", [
        {"question_id": "q1", "answer": "answer1"},
    ])
    mi.project_descriptions = overrides.get("project_descriptions", ["Project A"])
    mi.experience_summary = overrides.get("experience_summary", "Internship at company")
    mi.asr_confidence = overrides.get("asr_confidence", 0.92)
    mi.asr_flags = overrides.get("asr_flags", [])
    return mi


class TestAssemble:
    def test_returns_candidate_profile(self) -> None:
        profile = assemble(_mock_candidate(), _mock_metadata(), _mock_model_input())
        assert isinstance(profile, CandidateProfile)

    def test_candidate_id_propagated(self) -> None:
        cid = uuid4()
        profile = assemble(
            _mock_candidate(id=cid),
            _mock_metadata(),
            _mock_model_input(),
        )
        assert profile.candidate_id == cid

    def test_selected_program_propagated(self) -> None:
        profile = assemble(
            _mock_candidate(selected_program="Data Science"),
            _mock_metadata(),
            _mock_model_input(),
        )
        assert profile.selected_program == "Data Science"

    def test_completeness_from_metadata(self) -> None:
        profile = assemble(
            _mock_candidate(),
            _mock_metadata(data_completeness=0.72),
            _mock_model_input(),
        )
        assert profile.completeness == 0.72

    def test_metadata_fields_mapped(self) -> None:
        profile = assemble(
            _mock_candidate(),
            _mock_metadata(
                age_eligible=False,
                language_threshold_met=None,
                language_exam_type="TOEFL",
                has_video=False,
            ),
            _mock_model_input(),
        )
        assert profile.metadata.age_eligible is False
        assert profile.metadata.language_threshold_met is None
        assert profile.metadata.language_exam_type == "TOEFL"
        assert profile.metadata.has_video is False

    def test_model_input_fields_mapped(self) -> None:
        profile = assemble(
            _mock_candidate(),
            _mock_metadata(),
            _mock_model_input(
                essay_text="My long essay " * 10,
                video_transcript="Hello world",
            ),
        )
        assert profile.model_input.video_transcript == "Hello world"
        assert "My long essay" in profile.model_input.essay_text

    def test_data_flags_include_metadata_flags(self) -> None:
        profile = assemble(
            _mock_candidate(),
            _mock_metadata(data_flags=["missing_essay", "missing_video"]),
            _mock_model_input(),
        )
        assert "missing_essay" in profile.data_flags
        assert "missing_video" in profile.data_flags

    def test_low_asr_confidence_flagged(self) -> None:
        profile = assemble(
            _mock_candidate(),
            _mock_metadata(),
            _mock_model_input(asr_confidence=0.4),
        )
        assert "low_asr_confidence" in profile.data_flags

    def test_high_asr_confidence_not_flagged(self) -> None:
        profile = assemble(
            _mock_candidate(),
            _mock_metadata(),
            _mock_model_input(asr_confidence=0.95),
        )
        assert "low_asr_confidence" not in profile.data_flags

    def test_short_essay_flagged(self) -> None:
        profile = assemble(
            _mock_candidate(),
            _mock_metadata(),
            _mock_model_input(essay_text="Very short essay"),
        )
        assert "short_essay" in profile.data_flags

    def test_long_essay_not_flagged(self) -> None:
        profile = assemble(
            _mock_candidate(),
            _mock_metadata(),
            _mock_model_input(essay_text="word " * 50),
        )
        assert "short_essay" not in profile.data_flags

    def test_none_essay_no_short_flag(self) -> None:
        profile = assemble(
            _mock_candidate(),
            _mock_metadata(),
            _mock_model_input(essay_text=None),
        )
        assert "short_essay" not in profile.data_flags

    def test_none_asr_confidence_no_flag(self) -> None:
        profile = assemble(
            _mock_candidate(),
            _mock_metadata(),
            _mock_model_input(asr_confidence=None),
        )
        assert "low_asr_confidence" not in profile.data_flags

    def test_asr_flags_propagated_into_profile_data_flags(self) -> None:
        profile = assemble(
            _mock_candidate(),
            _mock_metadata(data_flags=["missing_video"]),
            _mock_model_input(asr_flags=["requires_human_review", "asr_processing_failed"]),
        )
        assert "missing_video" in profile.data_flags
        assert "requires_human_review" in profile.data_flags
        assert "asr_processing_failed" in profile.data_flags

    def test_created_at_propagated(self) -> None:
        ts = datetime(2026, 3, 27, 12, 0, 0, tzinfo=timezone.utc)
        profile = assemble(
            _mock_candidate(created_at=ts),
            _mock_metadata(),
            _mock_model_input(),
        )
        assert profile.created_at == ts
