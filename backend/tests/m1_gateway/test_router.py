from __future__ import annotations

from datetime import date
from uuid import uuid4
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.modules.m1_gateway.router import (
    MAX_BATCH_SIZE,
    get_candidate_pipeline_status,
    get_pipeline_job_events,
    get_pipeline_job_status,
    get_pipeline_queue_metrics,
    inspect_pipeline_job_ops,
    score_signal_batch,
    submit_candidate_async,
    submit_batch_async,
)
from app.modules.m1_gateway.schemas import (
    AsyncPipelineSubmitResponse,
    CandidatePipelineStatusView,
    PipelineJobEventView,
    PipelineJobStatusView,
    PipelineStageRunView,
)
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
async def test_score_signal_batch_rejects_oversized_batches() -> None:
    envelopes = [_make_envelope() for _ in range(MAX_BATCH_SIZE + 1)]

    with pytest.raises(HTTPException) as exc_info:
        await score_signal_batch(envelopes, db=None)  # type: ignore[arg-type]

    assert exc_info.value.status_code == 422
    assert "Batch size exceeds limit" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_submit_batch_async_rejects_oversized_batches() -> None:
    payloads = [_make_payload() for _ in range(MAX_BATCH_SIZE + 1)]

    with pytest.raises(HTTPException) as exc_info:
        await submit_batch_async(payloads, None, db=None)  # type: ignore[arg-type]

    assert exc_info.value.status_code == 422
    assert "Batch size exceeds limit" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_submit_batch_async_rejects_empty_payloads() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await submit_batch_async([], None, db=None)  # type: ignore[arg-type]

    assert exc_info.value.status_code == 422
    assert "Empty batch" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_submit_batch_async_returns_queued_jobs() -> None:
    payload = _make_payload()
    candidate_id = uuid4()
    job_id = uuid4()

    with patch("app.modules.m1_gateway.router.PipelineOrchestrator") as orchestrator_cls:
        orchestrator = orchestrator_cls.return_value
        orchestrator.submit_batch_async = AsyncMock(
            return_value=[
                AsyncPipelineSubmitResponse(
                    candidate_id=str(candidate_id),
                    job_id=str(job_id),
                    pipeline_status="queued",
                    job_status="queued",
                    current_stage="privacy",
                    message="Candidate accepted and queued for asynchronous processing.",
                )
            ]
        )
        response = await submit_batch_async([payload], None, db=None)  # type: ignore[arg-type]

    assert response["success"] is True
    assert response["data"][0]["candidate_id"] == str(candidate_id)
    assert response["data"][0]["job_id"] == str(job_id)


@pytest.mark.asyncio
async def test_submit_candidate_async_returns_queued_job() -> None:
    candidate_id = uuid4()
    job_id = uuid4()
    payload = _make_payload()

    with patch("app.modules.m1_gateway.router.PipelineOrchestrator") as orchestrator_cls:
        orchestrator = orchestrator_cls.return_value
        orchestrator.submit_async = AsyncMock(
            return_value=AsyncPipelineSubmitResponse(
                candidate_id=str(candidate_id),
                job_id=str(job_id),
                pipeline_status="queued",
                job_status="queued",
                current_stage="privacy",
                message="Candidate accepted and queued for asynchronous processing.",
            )
        )
        response = await submit_candidate_async(payload, None, db=None)  # type: ignore[arg-type]

    assert response["success"] is True
    assert response["data"]["candidate_id"] == str(candidate_id)
    assert response["data"]["job_id"] == str(job_id)
    assert response["data"]["job_status"] == "queued"


@pytest.mark.asyncio
async def test_get_pipeline_job_status_returns_snapshot() -> None:
    candidate_id = uuid4()
    job_id = uuid4()

    with patch("app.modules.m1_gateway.router.PipelineOrchestrator") as orchestrator_cls:
        orchestrator = orchestrator_cls.return_value
        orchestrator.get_job_status = AsyncMock(
            return_value=PipelineJobStatusView(
                job_id=str(job_id),
                candidate_id=str(candidate_id),
                job_type="candidate_submission",
                status="queued",
                current_stage="privacy",
                requested_by="system",
                execution_mode="async",
                attempt_count=0,
                queued_at="2026-03-30T18:00:00Z",
                stage_runs=[
                    PipelineStageRunView(
                        id=str(uuid4()),
                        stage_name="intake",
                        status="completed",
                        attempt_count=1,
                        created_at="2026-03-30T18:00:00Z",
                    ),
                ],
            )
        )
        response = await get_pipeline_job_status(job_id, db=None)  # type: ignore[arg-type]

    assert response["success"] is True
    assert response["data"]["job_id"] == str(job_id)
    assert response["data"]["stage_runs"][0]["stage_name"] == "intake"


@pytest.mark.asyncio
async def test_get_pipeline_job_events_returns_timeline() -> None:
    job_id = uuid4()

    with patch("app.modules.m1_gateway.router.PipelineOrchestrator") as orchestrator_cls:
        orchestrator = orchestrator_cls.return_value
        orchestrator.list_job_events = AsyncMock(
            return_value=[
                PipelineJobEventView(
                    id=str(uuid4()),
                    event_type="job_created",
                    status="queued",
                    payload={"candidate_id": str(uuid4())},
                    created_at="2026-03-30T18:00:00Z",
                )
            ]
        )
        response = await get_pipeline_job_events(job_id, db=None)  # type: ignore[arg-type]

    assert response["success"] is True
    assert response["data"][0]["event_type"] == "job_created"


@pytest.mark.asyncio
async def test_get_candidate_pipeline_status_returns_latest_job() -> None:
    candidate_id = uuid4()
    job_id = uuid4()

    with patch("app.modules.m1_gateway.router.PipelineOrchestrator") as orchestrator_cls:
        orchestrator = orchestrator_cls.return_value
        orchestrator.get_candidate_status = AsyncMock(
            return_value=CandidatePipelineStatusView(
                candidate_id=str(candidate_id),
                pipeline_status="queued",
                selected_program="CS",
                latest_job=PipelineJobStatusView(
                    job_id=str(job_id),
                    candidate_id=str(candidate_id),
                    job_type="candidate_submission",
                    status="queued",
                    current_stage="privacy",
                    requested_by="system",
                    execution_mode="async",
                    attempt_count=0,
                    queued_at="2026-03-30T18:00:00Z",
                    stage_runs=[],
                ),
            )
        )
        response = await get_candidate_pipeline_status(candidate_id, db=None)  # type: ignore[arg-type]

    assert response["success"] is True
    assert response["data"]["candidate_id"] == str(candidate_id)
    assert response["data"]["latest_job"]["job_id"] == str(job_id)


@pytest.mark.asyncio
async def test_get_pipeline_queue_metrics_returns_observability_fields() -> None:
    reviewer = object()

    with patch("app.modules.m1_gateway.router.PipelineOrchestrator") as orchestrator_cls:
        orchestrator = orchestrator_cls.return_value
        orchestrator.get_queue_metrics = AsyncMock(
            return_value={
                "queue_depth": {"pending": 2, "processing": 1, "delayed": 1, "dead": 0},
                "job_counts": {"queued": 2, "running": 1},
                "job_stage_snapshot": [
                    {"current_stage": "nlp", "status": "running", "count": 1}
                ],
                "stage_metrics": [
                    {
                        "stage_name": "nlp",
                        "total_runs": 3,
                        "failed_runs": 1,
                        "manual_review_rate": 0.3333,
                    }
                ],
                "manual_review_rate": 0.2,
                "failure_rate": 0.1,
            }
        )
        response = await get_pipeline_queue_metrics(reviewer, db=None)  # type: ignore[arg-type]

    assert response["success"] is True
    assert response["data"]["queue_depth"]["pending"] == 2
    assert response["data"]["job_counts"]["running"] == 1
    assert response["data"]["stage_metrics"][0]["stage_name"] == "nlp"


@pytest.mark.asyncio
async def test_inspect_pipeline_job_ops_returns_retry_details() -> None:
    job_id = uuid4()
    reviewer = object()

    with patch("app.modules.m1_gateway.router.PipelineOrchestrator") as orchestrator_cls:
        orchestrator = orchestrator_cls.return_value
        orchestrator.inspect_pipeline_job_ops = AsyncMock(
            return_value={
                "job": {"job_id": str(job_id), "status": "failed", "current_stage": "nlp"},
                "queue_state": {"in_dead_letter": True, "in_delayed": False},
                "retry_decision": {"retry_eligible": False, "reason": "max_attempts_exhausted"},
            }
        )
        response = await inspect_pipeline_job_ops(job_id, reviewer, db=None)  # type: ignore[arg-type]

    assert response["success"] is True
    assert response["data"]["job"]["job_id"] == str(job_id)
    assert response["data"]["queue_state"]["in_dead_letter"] is True
    assert response["data"]["retry_decision"]["reason"] == "max_attempts_exhausted"
