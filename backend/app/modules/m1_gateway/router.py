"""
File: router.py
Purpose: Gateway routes for early scoring integration.

Notes:
- These routes expose M6 before the full pipeline exists.
- They accept only the canonical signal contract, not raw intake payloads.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.schemas.common import success_response

from .orchestrator import orchestrator
from ..m6_scoring.schemas import SignalEnvelope

router = APIRouter(prefix="/api/v1/pipeline", tags=["pipeline"])


@router.post("/score-signals")
async def score_signals(envelope: SignalEnvelope) -> dict:
    """Score one candidate from a canonical signal envelope."""

    score = orchestrator.score_signals(envelope)
    return success_response(score.model_dump(mode="json"))


@router.post("/score-signals/batch")
async def score_signal_batch(envelopes: list[SignalEnvelope]) -> dict:
    """Score and rank a batch of signal envelopes."""

    scores = orchestrator.score_signal_batch(envelopes)
    return success_response([score.model_dump(mode="json") for score in scores])


@router.post("/score-signals/train-synthetic")
async def train_scoring_model(sample_count: int = 300, seed: int = 42) -> dict:
    """Train the scoring refinement model on synthetic development data."""

    labeled_samples = orchestrator.train_scoring_model_on_synthetic(sample_count=sample_count, seed=seed)
    return success_response(
        {
            "status": "trained",
            "sample_count": len(labeled_samples),
            "seed": seed,
        }
    )


@router.post("/score-signals/evaluate-synthetic")
async def evaluate_scoring_model(
    train_sample_count: int = 300,
    test_sample_count: int = 120,
    seed: int = 42,
) -> dict:
    """Run synthetic holdout evaluation for the scoring module."""

    metrics = orchestrator.evaluate_scoring_model_on_synthetic(
        train_sample_count=train_sample_count,
        test_sample_count=test_sample_count,
        seed=seed,
    )
    return success_response(metrics)


# File summary: router.py
# Exposes compact pipeline endpoints for direct M6 integration and testing.
