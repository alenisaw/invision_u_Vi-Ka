from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.modules.gateway.schemas import PipelineJobStatusView
from app.modules.gateway.worker import PipelineWorker


@pytest.mark.asyncio
async def test_worker_acks_completed_jobs() -> None:
    queue = AsyncMock()
    job_id = str(uuid4())
    queue.reserve_job = AsyncMock(return_value=job_id)
    queue.promote_due_jobs = AsyncMock(return_value=0)

    with patch("app.modules.gateway.worker.AsyncSessionLocal") as session_local, patch(
        "app.modules.gateway.worker.PipelineOrchestrator"
    ) as orchestrator_cls, patch.object(
        PipelineWorker,
        "_schedule_retry_if_allowed",
        AsyncMock(return_value=True),
    ):
        session_local.return_value.__aenter__ = AsyncMock(return_value=AsyncMock())
        session_local.return_value.__aexit__ = AsyncMock(return_value=False)
        orchestrator = orchestrator_cls.return_value
        orchestrator.process_pipeline_job = AsyncMock(
            return_value=PipelineJobStatusView(
                job_id=job_id,
                candidate_id=str(uuid4()),
                job_type="candidate_submission",
                status="completed",
                current_stage="completed",
                requested_by="system",
                execution_mode="async",
                attempt_count=1,
                queued_at="2026-03-30T20:00:00Z",
                stage_runs=[],
            )
        )

        worker = PipelineWorker(job_queue=queue, poll_timeout_seconds=0)
        processed = await worker.run_once()

    assert processed is True
    queue.ack_job.assert_awaited_once_with(job_id)
    queue.fail_job.assert_not_called()


@pytest.mark.asyncio
async def test_worker_retries_retryable_failed_jobs() -> None:
    queue = AsyncMock()
    job_id = str(uuid4())
    queue.reserve_job = AsyncMock(return_value=job_id)
    queue.promote_due_jobs = AsyncMock(return_value=0)

    with patch("app.modules.gateway.worker.AsyncSessionLocal") as session_local, patch(
        "app.modules.gateway.worker.PipelineOrchestrator"
    ) as orchestrator_cls, patch.object(
        PipelineWorker,
        "_schedule_retry_if_allowed",
        AsyncMock(return_value=True),
    ):
        session_local.return_value.__aenter__ = AsyncMock(return_value=AsyncMock())
        session_local.return_value.__aexit__ = AsyncMock(return_value=False)
        orchestrator = orchestrator_cls.return_value
        orchestrator.process_pipeline_job = AsyncMock(
            return_value=PipelineJobStatusView(
                job_id=job_id,
                candidate_id=str(uuid4()),
                job_type="candidate_submission",
                status="failed",
                current_stage="nlp",
                requested_by="system",
                execution_mode="async",
                attempt_count=1,
                queued_at="2026-03-30T20:00:00Z",
                error_code="m5_processing_failed",
                stage_runs=[],
            )
        )

        worker = PipelineWorker(job_queue=queue, poll_timeout_seconds=0)
        processed = await worker.run_once()

    assert processed is True
    queue.retry_job.assert_awaited_once()
    queue.fail_job.assert_not_called()


@pytest.mark.asyncio
async def test_worker_moves_non_retryable_failed_jobs_to_dead_letter_queue() -> None:
    queue = AsyncMock()
    job_id = str(uuid4())
    queue.reserve_job = AsyncMock(return_value=job_id)
    queue.promote_due_jobs = AsyncMock(return_value=0)

    with patch("app.modules.gateway.worker.AsyncSessionLocal") as session_local, patch(
        "app.modules.gateway.worker.PipelineOrchestrator"
    ) as orchestrator_cls, patch.object(
        PipelineWorker,
        "_schedule_retry_if_allowed",
        AsyncMock(return_value=False),
    ), patch.object(
        PipelineWorker,
        "_mark_dead_letter",
        AsyncMock(),
    ):
        session_local.return_value.__aenter__ = AsyncMock(return_value=AsyncMock())
        session_local.return_value.__aexit__ = AsyncMock(return_value=False)
        orchestrator = orchestrator_cls.return_value
        orchestrator.process_pipeline_job = AsyncMock(
            return_value=PipelineJobStatusView(
                job_id=job_id,
                candidate_id=str(uuid4()),
                job_type="candidate_submission",
                status="failed",
                current_stage="scoring",
                requested_by="system",
                execution_mode="async",
                attempt_count=1,
                queued_at="2026-03-30T20:00:00Z",
                error_code="job_processing_failed",
                stage_runs=[],
            )
        )

        worker = PipelineWorker(job_queue=queue, poll_timeout_seconds=0)
        processed = await worker.run_once()

    assert processed is True
    queue.fail_job.assert_awaited_once_with(job_id)


def test_inspect_retry_decision_marks_exhausted_attempts_as_non_retryable() -> None:
    worker = PipelineWorker(job_queue=AsyncMock(), poll_timeout_seconds=0)
    job_status = PipelineJobStatusView(
        job_id=str(uuid4()),
        candidate_id=str(uuid4()),
        job_type="candidate_submission",
        status="failed",
        current_stage="nlp",
        requested_by="system",
        execution_mode="async",
        attempt_count=3,
        queued_at="2026-03-30T20:00:00Z",
        error_code="llm_rate_limited",
        stage_runs=[
            {
                "id": str(uuid4()),
                "stage_name": "nlp",
                "status": "failed",
                "attempt_count": 3,
                "created_at": "2026-03-30T20:00:00Z",
            }
        ],
    )

    retry_decision = worker.inspect_retry_decision(job_status)

    assert retry_decision["retry_eligible"] is False
    assert retry_decision["reason"] == "max_attempts_exhausted"


def test_inspect_retry_decision_marks_provider_failure_as_retryable() -> None:
    worker = PipelineWorker(job_queue=AsyncMock(), poll_timeout_seconds=0)
    job_status = PipelineJobStatusView(
        job_id=str(uuid4()),
        candidate_id=str(uuid4()),
        job_type="candidate_submission",
        status="failed",
        current_stage="asr",
        requested_by="system",
        execution_mode="async",
        attempt_count=1,
        queued_at="2026-03-30T20:00:00Z",
        error_code="asr_provider_failed",
        stage_runs=[
            {
                "id": str(uuid4()),
                "stage_name": "asr",
                "status": "failed",
                "attempt_count": 1,
                "created_at": "2026-03-30T20:00:00Z",
            }
        ],
    )

    retry_decision = worker.inspect_retry_decision(job_status)

    assert retry_decision["retry_eligible"] is True
    assert retry_decision["retry_delay_seconds"] == 2
