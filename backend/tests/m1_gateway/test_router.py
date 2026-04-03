from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.modules.m1_gateway.router import (
    score_signal_batch,
    score_signals,
    submit_batch,
    submit_candidate,
)
from app.modules.m2_intake.schemas import (
    AcademicInfo,
    CandidateIntakeRequest,
    ContactsInfo,
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
        contacts=ContactsInfo(email="test.user@example.com"),
        academic=AcademicInfo(selected_program="CS"),
        content=ContentInfo(
            video_url="https://youtube.com/watch?v=router123",
            essay_text="Test essay",
        ),
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
async def test_submit_batch_rejects_empty_payloads() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await submit_batch([], db=None)  # type: ignore[arg-type]

    assert exc_info.value.status_code == 422
    assert "Empty batch" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_submit_batch_returns_pipeline_results() -> None:
    payload = _make_payload()
    candidate_id = str(uuid4())

    result_stub = SimpleNamespace(
        to_dict=lambda: {
            "candidate_id": candidate_id,
            "pipeline_status": "completed",
            "score": {"recommendation_status": "RECOMMEND"},
            "completeness": 0.82,
            "data_flags": [],
        }
    )

    with patch("app.modules.m1_gateway.router.PipelineOrchestrator") as orchestrator_cls:
        orchestrator = orchestrator_cls.return_value
        orchestrator.run_batch = AsyncMock(return_value=[result_stub])

        response = await submit_batch([payload], db=None)  # type: ignore[arg-type]

    assert response["success"] is True
    assert response["data"][0]["candidate_id"] == candidate_id
    assert response["data"][0]["pipeline_status"] == "completed"


@pytest.mark.asyncio
async def test_submit_candidate_returns_pipeline_result() -> None:
    payload = _make_payload()
    candidate_id = str(uuid4())

    result_stub = SimpleNamespace(
        to_dict=lambda: {
            "candidate_id": candidate_id,
            "pipeline_status": "completed",
            "score": {"recommendation_status": "RECOMMEND"},
            "completeness": 0.9,
            "data_flags": [],
        }
    )

    with patch("app.modules.m1_gateway.router.PipelineOrchestrator") as orchestrator_cls:
        orchestrator = orchestrator_cls.return_value
        orchestrator.run_pipeline = AsyncMock(return_value=result_stub)

        response = await submit_candidate(payload, db=None)  # type: ignore[arg-type]

    assert response["success"] is True
    assert response["data"]["candidate_id"] == candidate_id
    assert response["data"]["pipeline_status"] == "completed"


@pytest.mark.asyncio
async def test_submit_candidate_translates_value_error_to_http_422() -> None:
    with patch("app.modules.m1_gateway.router.PipelineOrchestrator") as orchestrator_cls:
        orchestrator = orchestrator_cls.return_value
        orchestrator.run_pipeline = AsyncMock(side_effect=ValueError("bad payload"))

        with pytest.raises(HTTPException) as exc_info:
            await submit_candidate(_make_payload(), db=None)  # type: ignore[arg-type]

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "bad payload"


@pytest.mark.asyncio
async def test_score_signals_returns_single_score_payload() -> None:
    envelope = _make_envelope()
    score_stub = MagicMock()
    score_stub.model_dump.return_value = {
        "candidate_id": str(envelope.candidate_id),
        "recommendation_status": "RECOMMEND",
        "review_priority_index": 0.71,
    }

    with patch("app.modules.m1_gateway.router.PipelineOrchestrator") as orchestrator_cls:
        orchestrator = orchestrator_cls.return_value
        orchestrator.score_signals.return_value = score_stub

        response = await score_signals(envelope, db=None)  # type: ignore[arg-type]

    assert response["success"] is True
    assert response["data"]["candidate_id"] == str(envelope.candidate_id)
    assert response["data"]["recommendation_status"] == "RECOMMEND"


@pytest.mark.asyncio
async def test_score_signal_batch_returns_ranked_scores() -> None:
    envelopes = [_make_envelope(), _make_envelope()]
    first_score = MagicMock()
    first_score.model_dump.return_value = {
        "candidate_id": str(envelopes[0].candidate_id),
        "review_priority_index": 0.8,
    }
    second_score = MagicMock()
    second_score.model_dump.return_value = {
        "candidate_id": str(envelopes[1].candidate_id),
        "review_priority_index": 0.6,
    }

    with patch("app.modules.m1_gateway.router.PipelineOrchestrator") as orchestrator_cls:
        orchestrator = orchestrator_cls.return_value
        orchestrator.score_signal_batch.return_value = [first_score, second_score]

        response = await score_signal_batch(envelopes, db=None)  # type: ignore[arg-type]

    assert response["success"] is True
    assert len(response["data"]) == 2
    assert response["data"][0]["review_priority_index"] == 0.8
