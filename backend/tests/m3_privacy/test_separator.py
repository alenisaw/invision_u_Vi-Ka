from __future__ import annotations

from datetime import date

import pytest

from app.modules.m2_intake.schemas import (
    AcademicInfo,
    CandidateIntakeRequest,
    ContactsInfo,
    ContentInfo,
    InternalTestAnswer,
    InternalTestInfo,
    ParentContact,
    ParentsInfo,
    PersonalInfo,
)
from app.modules.m3_privacy.separator import Layer1PII, Layer2Metadata, Layer3ModelInput, separate


def _make_payload(**overrides) -> CandidateIntakeRequest:
    """Build a minimal valid intake request for testing."""
    defaults = {
        "personal": PersonalInfo(
            first_name="Алихан",
            last_name="Касымов",
            patronymic="Серикович",
            date_of_birth=date(2005, 6, 15),
            iin="050615123456",
            citizenship="KZ",
        ),
        "contacts": ContactsInfo(
            phone="+77011234567",
            instagram="@alikhan_kas",
            telegram="@alikhan_t",
        ),
        "parents": ParentsInfo(
            father=ParentContact(first_name="Серик", last_name="Касымов", phone="+77019876543"),
            mother=ParentContact(first_name="Айгуль", last_name="Касымова"),
        ),
        "academic": AcademicInfo(
            selected_program="Computer Science",
            language_exam_type="IELTS",
            language_score=6.5,
        ),
        "content": ContentInfo(
            video_url="https://example.com/video.mp4",
            essay_text="Меня зовут Алихан Касымов. Я хочу стать программистом.",
            project_descriptions=["Проект по ML от Алихан"],
            experience_summary="Стажировка в компании, телефон +77011234567",
        ),
        "internal_test": InternalTestInfo(
            answers=[
                InternalTestAnswer(question_id="q1", answer="Мой ответ от Алихан Касымов"),
            ]
        ),
    }
    defaults.update(overrides)
    return CandidateIntakeRequest(**defaults)


class TestSeparate:
    def test_returns_three_layers(self) -> None:
        payload = _make_payload()
        result = separate(
            payload,
            age_eligible=True,
            language_threshold_met=True,
            data_completeness=0.9,
            data_flags=[],
        )
        assert isinstance(result.layer1, Layer1PII)
        assert isinstance(result.layer2, Layer2Metadata)
        assert isinstance(result.layer3, Layer3ModelInput)

    def test_layer1_contains_full_snapshot(self) -> None:
        payload = _make_payload()
        result = separate(
            payload,
            age_eligible=True,
            language_threshold_met=True,
            data_completeness=0.9,
            data_flags=[],
        )
        assert result.layer1.snapshot["personal"]["first_name"] == "Алихан"
        assert result.layer1.snapshot["contacts"]["phone"] == "+77011234567"

    def test_layer2_metadata_populated(self) -> None:
        payload = _make_payload()
        result = separate(
            payload,
            age_eligible=True,
            language_threshold_met=True,
            data_completeness=0.85,
            data_flags=["missing_video"],
        )
        assert result.layer2.age_eligible is True
        assert result.layer2.language_threshold_met is True
        assert result.layer2.language_exam_type == "IELTS"
        assert result.layer2.has_video is True
        assert result.layer2.data_completeness == 0.85
        assert result.layer2.data_flags == ["missing_video"]

    def test_layer3_redacts_names_from_essay(self) -> None:
        payload = _make_payload()
        result = separate(
            payload,
            age_eligible=True,
            language_threshold_met=True,
            data_completeness=0.9,
            data_flags=[],
        )
        assert result.layer3.essay_text is not None
        assert "Алихан" not in result.layer3.essay_text
        assert "Касымов" not in result.layer3.essay_text
        assert "[NAME]" in result.layer3.essay_text

    def test_layer3_redacts_phone_from_experience(self) -> None:
        payload = _make_payload()
        result = separate(
            payload,
            age_eligible=True,
            language_threshold_met=True,
            data_completeness=0.9,
            data_flags=[],
        )
        assert result.layer3.experience_summary is not None
        assert "+77011234567" not in result.layer3.experience_summary
        assert "[PHONE]" in result.layer3.experience_summary

    def test_layer3_redacts_names_from_test_answers(self) -> None:
        payload = _make_payload()
        result = separate(
            payload,
            age_eligible=True,
            language_threshold_met=True,
            data_completeness=0.9,
            data_flags=[],
        )
        answer = result.layer3.internal_test_answers[0]
        assert answer["question_id"] == "q1"
        assert "Алихан" not in answer["answer"]
        assert "[NAME]" in answer["answer"]

    def test_layer3_redacts_names_from_projects(self) -> None:
        payload = _make_payload()
        result = separate(
            payload,
            age_eligible=True,
            language_threshold_met=True,
            data_completeness=0.9,
            data_flags=[],
        )
        assert len(result.layer3.project_descriptions) == 1
        assert "Алихан" not in result.layer3.project_descriptions[0]

    def test_layer3_strips_html(self) -> None:
        payload = _make_payload(
            content=ContentInfo(
                essay_text="<p>Привет <b>мир</b></p>",
                project_descriptions=["<div>Проект</div>"],
            ),
        )
        result = separate(
            payload,
            age_eligible=True,
            language_threshold_met=True,
            data_completeness=0.5,
            data_flags=[],
        )
        assert "<p>" not in (result.layer3.essay_text or "")
        assert "Привет мир" in (result.layer3.essay_text or "")

    def test_video_transcript_passed_through_and_redacted(self) -> None:
        payload = _make_payload()
        result = separate(
            payload,
            age_eligible=True,
            language_threshold_met=True,
            data_completeness=0.9,
            data_flags=[],
            video_transcript="Привет, я Алихан, мой номер +77011234567",
            asr_confidence=0.92,
            asr_flags=["low_volume"],
        )
        assert result.layer3.video_transcript is not None
        assert "Алихан" not in result.layer3.video_transcript
        assert "[NAME]" in result.layer3.video_transcript
        assert result.layer3.asr_confidence == 0.92
        assert result.layer3.asr_flags == ["low_volume"]

    def test_none_fields_stay_none(self) -> None:
        payload = _make_payload(
            content=ContentInfo(),
        )
        result = separate(
            payload,
            age_eligible=True,
            language_threshold_met=None,
            data_completeness=0.3,
            data_flags=["missing_essay", "missing_video"],
        )
        assert result.layer3.essay_text is None
        assert result.layer3.video_transcript is None
        assert result.layer3.experience_summary is None
