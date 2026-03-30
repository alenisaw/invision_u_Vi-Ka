from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

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
    SocialStatusInfo,
)
from app.modules.m2_intake.service import CandidateIntakeService


def _build_payload() -> CandidateIntakeRequest:
    return CandidateIntakeRequest(
        personal=PersonalInfo(
            first_name="Aruzhan",
            last_name="Sarsen",
            patronymic="Bekovna",
            date_of_birth=date(2007, 4, 12),
            gender="female",
            citizenship="KZ",
            iin="123456789012",
            document_type="passport",
            document_no="N12345678",
            document_authority="MIA",
        ),
        contacts=ContactsInfo(
            phone="+77011234567",
            instagram="@candidate",
        ),
        parents=ParentsInfo(
            father=ParentContact(
                first_name="Marat",
                last_name="Sarsenov",
                phone="+77017654321",
            )
        ),
        academic=AcademicInfo(
            selected_program="Creative Engineering",
            language_exam_type="IELTS",
            language_score=7.0,
        ),
        content=ContentInfo(
            video_url="https://example.com/video.mp4",
            essay_text="This essay must stay outside Layer 1.",
            project_descriptions=["Built a robotics prototype."],
            experience_summary="Led a school club.",
        ),
        social_status=SocialStatusInfo(
            has_social_benefit=True,
            benefit_type="grant",
        ),
        internal_test=InternalTestInfo(
            answers=[InternalTestAnswer(question_id="q1", answer="A")]
        ),
    )


def test_secure_snapshot_keeps_only_pii_related_sections() -> None:
    service = CandidateIntakeService(MagicMock())
    snapshot = service._build_secure_snapshot(_build_payload())

    assert set(snapshot) == {"personal", "contacts", "parents", "social_status"}
    assert snapshot["personal"]["iin"] == "123456789012"
    assert "academic" not in snapshot
    assert "content" not in snapshot
    assert "internal_test" not in snapshot


def test_secure_snapshot_drops_empty_address_section() -> None:
    service = CandidateIntakeService(MagicMock())
    snapshot = service._build_secure_snapshot(_build_payload())

    assert "address" not in snapshot


def test_build_dedupe_key_is_stable_for_same_iin(monkeypatch) -> None:
    monkeypatch.setenv("API_KEY", "reviewer-key-1234567890-abcdef")
    monkeypatch.setenv("POSTGRES_PASSWORD", "local-dev-password")
    monkeypatch.setenv("PII_ENCRYPTION_KEY", "very-secure-pii-encryption-secret-123456")

    service = CandidateIntakeService(MagicMock())
    payload = _build_payload()

    first_key = service._build_dedupe_key(payload)
    second_key = service._build_dedupe_key(payload)

    assert first_key
    assert first_key == second_key


@pytest.mark.asyncio
async def test_intake_candidate_reuses_existing_candidate(monkeypatch) -> None:
    monkeypatch.setenv("API_KEY", "reviewer-key-1234567890-abcdef")
    monkeypatch.setenv("POSTGRES_PASSWORD", "local-dev-password")
    monkeypatch.setenv("PII_ENCRYPTION_KEY", "very-secure-pii-encryption-secret-123456")

    service = CandidateIntakeService(MagicMock())
    existing_candidate = MagicMock(id=uuid4(), selected_program="Old Program", pipeline_status="completed")
    service.repository = AsyncMock()
    service.repository.get_candidate_by_dedupe_key.return_value = existing_candidate

    response = await service.intake_candidate(_build_payload())

    assert response.candidate_id == str(existing_candidate.id)
    service.repository.create_candidate.assert_not_awaited()
    service.repository.upsert_candidate_pii.assert_awaited_once()
    service.repository.upsert_candidate_metadata.assert_awaited_once()
    service.repository.flush.assert_awaited_once()
