# app/modules/m1_gateway/router.py
"""
Public and operational endpoints for the pipeline gateway.

Purpose:
- Accept asynchronous candidate jobs and expose their status.
- Expose reviewer-only queue and retry operations.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    ReviewerAuthContext,
    enforce_batch_rate_limit,
    enforce_submit_rate_limit,
    get_db,
    require_rate_limited_reviewer,
)
from app.modules.m1_gateway.orchestrator import PipelineOrchestrator
from app.modules.m2_intake.schemas import CandidateIntakeRequest
from app.modules.m6_scoring.schemas import SignalEnvelope
from app.schemas.common import success_response

router = APIRouter(prefix="/api/v1/pipeline", tags=["pipeline"])
MAX_BATCH_SIZE = 50


@router.post("/submit-async", status_code=202)
async def submit_candidate_async(
    payload: CandidateIntakeRequest,
    _: None = Depends(enforce_submit_rate_limit),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Accept a candidate and queue a persistent background job for later processing."""
    try:
        orchestrator = PipelineOrchestrator(db)
        result = await orchestrator.submit_async(payload)
        return success_response(result.model_dump(mode="json"))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/submit-async/batch", status_code=202)
async def submit_batch_async(
    payloads: list[CandidateIntakeRequest],
    _: None = Depends(enforce_batch_rate_limit),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Accept multiple candidates and queue one background job per payload."""
    if not payloads:
        raise HTTPException(status_code=422, detail="Empty batch")
    if len(payloads) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=422,
            detail=f"Batch size exceeds limit of {MAX_BATCH_SIZE}",
        )

    try:
        orchestrator = PipelineOrchestrator(db)
        results = await orchestrator.submit_batch_async(payloads)
        return success_response([result.model_dump(mode="json") for result in results])
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/queue/metrics")
async def get_pipeline_queue_metrics(
    reviewer: ReviewerAuthContext = Depends(require_rate_limited_reviewer),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return queue depth, job counters, and stage metrics for operations."""
    _ = reviewer
    orchestrator = PipelineOrchestrator(db)
    metrics = await orchestrator.get_queue_metrics()
    return success_response(metrics)


@router.get("/ops/jobs/dead-letter")
async def list_dead_letter_jobs(
    limit: int = 100,
    reviewer: ReviewerAuthContext = Depends(require_rate_limited_reviewer),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return jobs currently held in dead-letter queue for inspection."""
    _ = reviewer
    orchestrator = PipelineOrchestrator(db)
    jobs = await orchestrator.list_dead_letter_jobs(limit=limit)
    return success_response([job.model_dump(mode="json") for job in jobs])


@router.get("/ops/jobs/delayed")
async def list_delayed_retry_jobs(
    limit: int = 100,
    reviewer: ReviewerAuthContext = Depends(require_rate_limited_reviewer),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return jobs currently waiting in delayed retry queue."""
    _ = reviewer
    orchestrator = PipelineOrchestrator(db)
    jobs = await orchestrator.list_delayed_retry_jobs(limit=limit)
    return success_response([job.model_dump(mode="json") for job in jobs])


@router.post("/ops/jobs/{job_id}/retry")
async def retry_pipeline_job(
    job_id: UUID,
    reviewer: ReviewerAuthContext = Depends(require_rate_limited_reviewer),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Manually requeue a failed or dead-lettered pipeline job."""
    orchestrator = PipelineOrchestrator(db)
    try:
        job = await orchestrator.requeue_pipeline_job(job_id, actor=reviewer.reviewer_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return success_response(job.model_dump(mode="json"))


@router.get("/ops/jobs/{job_id}/inspection")
async def inspect_pipeline_job_ops(
    job_id: UUID,
    reviewer: ReviewerAuthContext = Depends(require_rate_limited_reviewer),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Inspect queue placement and retry eligibility for one pipeline job."""
    _ = reviewer
    orchestrator = PipelineOrchestrator(db)
    try:
        inspection = await orchestrator.inspect_pipeline_job_ops(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return success_response(inspection)


@router.get("/jobs/{job_id}")
async def get_pipeline_job_status(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the persisted state of an asynchronous pipeline job."""
    orchestrator = PipelineOrchestrator(db)
    try:
        job = await orchestrator.get_job_status(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return success_response(job.model_dump(mode="json"))


@router.get("/jobs/{job_id}/events")
async def get_pipeline_job_events(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the event timeline for an asynchronous pipeline job."""
    orchestrator = PipelineOrchestrator(db)
    try:
        events = await orchestrator.list_job_events(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return success_response([event.model_dump(mode="json") for event in events])


@router.get("/candidates/{candidate_id}/status")
async def get_candidate_pipeline_status(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return candidate-level pipeline status plus the latest queued job snapshot."""
    orchestrator = PipelineOrchestrator(db)
    try:
        status = await orchestrator.get_candidate_status(candidate_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return success_response(status.model_dump(mode="json"))


@router.post("/score-signals")
async def score_signals(
    envelope: SignalEnvelope,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Score one candidate from a canonical signal envelope."""
    orchestrator = PipelineOrchestrator(db)
    score = orchestrator.score_signals(envelope)
    return success_response(score.model_dump(mode="json"))


@router.post("/score-signals/batch")
async def score_signal_batch(
    envelopes: list[SignalEnvelope],
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Score and rank a batch of signal envelopes."""
    if not envelopes:
        raise HTTPException(status_code=422, detail="Empty batch")
    if len(envelopes) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=422,
            detail=f"Batch size exceeds limit of {MAX_BATCH_SIZE}",
        )

    orchestrator = PipelineOrchestrator(db)
    scores = orchestrator.score_signal_batch(envelopes)
    return success_response([score.model_dump(mode="json") for score in scores])


@router.post("/score-signals/train-synthetic")
async def train_scoring_model(
    sample_count: int = 300,
    seed: int = 42,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Train the scoring refinement model on synthetic data."""
    orchestrator = PipelineOrchestrator(db)
    labeled = orchestrator.train_scoring_model_on_synthetic(
        sample_count=sample_count,
        seed=seed,
    )
    return success_response(
        {"status": "trained", "sample_count": len(labeled), "seed": seed}
    )


@router.post("/score-signals/evaluate-synthetic")
async def evaluate_scoring_model(
    train_sample_count: int = 300,
    test_sample_count: int = 120,
    seed: int = 42,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Run synthetic holdout evaluation for the scoring module."""
    orchestrator = PipelineOrchestrator(db)
    metrics = orchestrator.evaluate_scoring_model_on_synthetic(
        train_sample_count=train_sample_count,
        test_sample_count=test_sample_count,
        seed=seed,
    )
    return success_response(metrics)
