from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.modules.m1_gateway.router import MAX_BATCH_SIZE, score_signal_batch, submit_batch
from app.modules.m2_intake.schemas import (
    AcademicInfo,
    CandidateIntakeRequest,
    ContentInfo,
    InternalTestAnswer,
    InternalTestInfo,
    PersonalInfo,
)
from app.modules.m6_scoring.schemas import SignalEnvelope


def _make_payload() -> CandidateIntakeRequest:
    return CandidateIntakeRequest(
        personal=PersonalInfo(
            first_name="Test",
            last_name="User",
            date_of_birth=date(2005, 1, 1),
        ),
        academic=AcademicInfo(selected_program="CS"),
        content=ContentInfo(essay_text="Test essay"),
        internal_test=InternalTestInfo(
            answers=[InternalTestAnswer(question_id="q1", answer="answer")]
        ),
    )


def _make_envelope() -> SignalEnvelope:
    return SignalEnvelope(
        candidate_id=uuid4(),
        signal_schema_version="v1",
        completeness=0.8,
        signals={},
    )


@pytest.mark.asyncio
async def test_submit_batch_rejects_oversized_batches() -> None:
    payloads = [_make_payload() for _ in range(MAX_BATCH_SIZE + 1)]

    with pytest.raises(HTTPException) as exc_info:
        await submit_batch(payloads, db=None)  # type: ignore[arg-type]

    assert exc_info.value.status_code == 422
    assert "Batch size exceeds limit" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_score_signal_batch_rejects_oversized_batches() -> None:
    envelopes = [_make_envelope() for _ in range(MAX_BATCH_SIZE + 1)]

    with pytest.raises(HTTPException) as exc_info:
        await score_signal_batch(envelopes, db=None)  # type: ignore[arg-type]

    assert exc_info.value.status_code == 422
    assert "Batch size exceeds limit" in str(exc_info.value.detail)

