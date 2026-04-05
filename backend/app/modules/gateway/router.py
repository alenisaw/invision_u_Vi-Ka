from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.modules.gateway.orchestrator import PipelineOrchestrator
from app.modules.intake.schemas import CandidateIntakeRequest
from app.modules.scoring.schemas import SignalEnvelope
from app.schemas.common import success_response

router = APIRouter(prefix="/api/v1/pipeline", tags=["pipeline"])


@router.post("/submit")
async def submit_candidate(
    payload: CandidateIntakeRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Submit a single candidate through the full pipeline."""
    try:
        orchestrator = PipelineOrchestrator(db)
        result = await orchestrator.run_pipeline(payload)
        return success_response(result.to_dict())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/batch")
async def submit_batch(
    payloads: list[CandidateIntakeRequest],
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Submit multiple candidates through the full pipeline."""
    if not payloads:
        raise HTTPException(status_code=422, detail="Empty batch")

    orchestrator = PipelineOrchestrator(db)
    results = await orchestrator.run_batch(payloads)
    return success_response([r.to_dict() for r in results])


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
    orchestrator = PipelineOrchestrator(db)
    scores = orchestrator.score_signal_batch(envelopes)
    return success_response([s.model_dump(mode="json") for s in scores])


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
    """Run synthetic holdout evaluation for the scoring stage."""
    orchestrator = PipelineOrchestrator(db)
    metrics = orchestrator.evaluate_scoring_model_on_synthetic(
        train_sample_count=train_sample_count,
        test_sample_count=test_sample_count,
        seed=seed,
    )
    return success_response(metrics)
