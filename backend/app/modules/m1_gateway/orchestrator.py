"""
File: orchestrator.py
Purpose: Minimal gateway orchestration for M6 scoring routes.

Notes:
- This orchestrator exposes M6 safely before the rest of the pipeline is ready.
- It accepts the canonical signal contract instead of raw candidate intake payloads.
"""

from __future__ import annotations

from ..m6_scoring.schemas import CandidateScore, LabeledEnvelope, SignalEnvelope
from ..m6_scoring.service import ScoringService


class PipelineOrchestrator:
    """Small orchestration layer around the scoring service."""

    def __init__(self) -> None:
        self.scoring_service = ScoringService()

    def score_signals(self, envelope: SignalEnvelope) -> CandidateScore:
        """Score one canonical signal envelope."""

        return self.scoring_service.score_candidate(envelope)

    def score_signal_batch(self, envelopes: list[SignalEnvelope]) -> list[CandidateScore]:
        """Score and rank a batch of canonical signal envelopes."""

        return self.scoring_service.score_batch(envelopes)

    def train_scoring_model_on_synthetic(self, sample_count: int = 300, seed: int = 42) -> list[LabeledEnvelope]:
        """Train the optional M6 refinement layer on generated development data."""

        return self.scoring_service.train_on_synthetic(sample_count=sample_count, seed=seed)

    def evaluate_scoring_model_on_synthetic(
        self,
        train_sample_count: int = 300,
        test_sample_count: int = 120,
        seed: int = 42,
    ) -> dict[str, float | int]:
        """Run a compact synthetic holdout evaluation for the current scoring setup."""

        return self.scoring_service.evaluate_on_synthetic(
            train_sample_count=train_sample_count,
            test_sample_count=test_sample_count,
            seed=seed,
        )


orchestrator = PipelineOrchestrator()


# File summary: orchestrator.py
# Exposes a compact orchestration layer for early M6 API integration.
