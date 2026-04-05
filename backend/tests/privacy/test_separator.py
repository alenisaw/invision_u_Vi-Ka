from __future__ import annotations

from datetime import date

from app.core.text_sanitizer import mask_profanity
from app.modules.intake.schemas import (
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
from app.modules.privacy.separator import Layer1PII, Layer2Metadata, Layer3ModelInput, separate


def _make_payload(**overrides) -> CandidateIntakeRequest:
    defaults = {
        "personal": PersonalInfo(
            first_name="Alikhan",
            last_name="Kassymov",
            patronymic="Serikovich",
            date_of_birth=date(2005, 6, 15),
            iin="050615123456",
            citizenship="KZ",
        ),
        "contacts": ContactsInfo(
            email="alikhan@example.com",
            phone="+77011234567",
            instagram="@alikhan_kas",
            telegram="@alikhan_t",
        ),
        "parents": ParentsInfo(
            father=ParentContact(first_name="Serik", last_name="Kassymov", phone="+77019876543"),
            mother=ParentContact(first_name="Aigul", last_name="Kassymova"),
        ),
        "academic": AcademicInfo(
            selected_program="Computer Science",
            language_exam_type="IELTS",
            language_score=6.5,
        ),
        "content": ContentInfo(
            video_url="https://example.com/video.mp4",
            essay_text="My name is Alikhan Kassymov. I want to become a software engineer.",
        ),
        "internal_test": InternalTestInfo(
            answers=[
                InternalTestAnswer(question_id="q1", answer="My answer is from Alikhan Kassymov"),
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
        assert result.layer1.snapshot["personal"]["first_name"] == "Alikhan"
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
        assert "Alikhan" not in result.layer3.essay_text
        assert "Kassymov" not in result.layer3.essay_text
        assert "[NAME]" in result.layer3.essay_text

    def test_layer3_keeps_removed_fields_empty_for_downstream_compatibility(self) -> None:
        payload = _make_payload()
        result = separate(
            payload,
            age_eligible=True,
            language_threshold_met=True,
            data_completeness=0.9,
            data_flags=[],
        )
        assert result.layer3.experience_summary is None
        assert result.layer3.project_descriptions == []

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
        assert "Alikhan" not in answer["answer"]
        assert "[NAME]" in answer["answer"]

    def test_layer3_strips_html(self) -> None:
        payload = _make_payload(
            content=ContentInfo(
                video_url="https://example.com/video.mp4",
                essay_text="<p>Hello <b>world</b></p>",
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
        assert "Hello world" in (result.layer3.essay_text or "")

    def test_video_transcript_passed_through_and_redacted(self) -> None:
        payload = _make_payload()
        result = separate(
            payload,
            age_eligible=True,
            language_threshold_met=True,
            data_completeness=0.9,
            data_flags=[],
            video_transcript="Hello, I am Alikhan, my phone is +77011234567",
            asr_confidence=0.92,
            asr_flags=["low_volume"],
        )
        assert result.layer3.video_transcript is not None
        assert "Alikhan" not in result.layer3.video_transcript
        assert "[NAME]" in result.layer3.video_transcript
        assert result.layer3.asr_confidence == 0.92
        assert result.layer3.asr_flags == ["low_volume"]

    def test_layer3_masks_profanity_before_model_input(self) -> None:
        mask_token = mask_profanity("fuck") or ""
        payload = _make_payload(
            content=ContentInfo(
                video_url="https://example.com/video.mp4",
                essay_text="This was fuck, but I still finished the project.",
            ),
        )
        result = separate(
            payload,
            age_eligible=True,
            language_threshold_met=True,
            data_completeness=0.7,
            data_flags=[],
            video_transcript="shit, it was hard, but I finished the task.",
        )

        assert mask_token in (result.layer3.essay_text or "")
        assert mask_token in (result.layer3.video_transcript or "")

    def test_none_fields_stay_none(self) -> None:
        payload = _make_payload(
            content=ContentInfo(video_url="https://example.com/video.mp4"),
        )
        result = separate(
            payload,
            age_eligible=True,
            language_threshold_met=None,
            data_completeness=0.3,
            data_flags=["missing_essay"],
        )
        assert result.layer3.essay_text is None
        assert result.layer3.video_transcript is None
        assert result.layer3.experience_summary is None
        assert result.layer3.project_descriptions == []
