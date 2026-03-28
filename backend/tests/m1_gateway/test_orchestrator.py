from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.m1_gateway.orchestrator import PipelineOrchestrator, PipelineResult
from app.modules.m2_intake.schemas import (
    AcademicInfo,
    CandidateIntakeRequest,
    CandidateIntakeResponse,
    ContentInfo,
    InternalTestAnswer,
    InternalTestInfo,
    PersonalInfo,
)
from app.modules.m4_profile.schemas import CandidateProfile, ModelInput, ProfileMetadata
from app.modules.m6_scoring.schemas import CandidateScore, SignalEnvelope


def _make_payload() -> CandidateIntakeRequest:
    return CandidateIntakeRequest(
        personal=PersonalInfo(
            first_name="Test",
            last_name="User",
            date_of_birth=date(2005, 1, 1),
        ),
        academic=AcademicInfo(selected_program="CS"),
        content=ContentInfo(essay_text="A test essay with enough words " * 5),
        internal_test=InternalTestInfo(
            answers=[InternalTestAnswer(question_id="q1", answer="answer")]
        ),
    )


def _make_fake_score(candidate_id) -> CandidateScore:
    return CandidateScore(
        candidate_id=candidate_id,
        sub_scores={"leadership_potential": 0.7},
        review_priority_index=0.65,
        recommendation_status="RECOMMEND",
        confidence=0.8,
    )


class TestPipelineResult:
    def test_to_dict_contains_required_keys(self) -> None:
        cid = uuid4()
        profile = CandidateProfile(
            candidate_id=cid,
            selected_program="CS",
            model_input=ModelInput(),
            metadata=ProfileMetadata(),
            completeness=0.85,
            data_flags=["missing_video"],
            created_at="2026-03-27T12:00:00Z",
        )
        score = _make_fake_score(cid)

        result = PipelineResult(
            candidate_id=cid,
            profile=profile,
            score=score,
            pipeline_status="completed",
        )
        d = result.to_dict()

        assert d["candidate_id"] == str(cid)
        assert d["pipeline_status"] == "completed"
        assert d["score"]["recommendation_status"] == "RECOMMEND"
        assert d["completeness"] == 0.85
        assert d["data_flags"] == ["missing_video"]


class TestPipelineOrchestratorDirect:
    """Test direct M6 scoring methods (no DB required)."""

    def test_score_signals_returns_candidate_score(self) -> None:
        session = MagicMock()
        orch = PipelineOrchestrator(session)

        envelope = SignalEnvelope(
            candidate_id=uuid4(),
            signal_schema_version="v1",
            completeness=0.8,
            signals={},
        )
        score = orch.score_signals(envelope)
        assert isinstance(score, CandidateScore)
        assert 0.0 <= score.review_priority_index <= 1.0

    def test_score_signal_batch_returns_list(self) -> None:
        session = MagicMock()
        orch = PipelineOrchestrator(session)

        envelopes = [
            SignalEnvelope(
                candidate_id=uuid4(),
                signal_schema_version="v1",
                completeness=0.7,
                signals={},
            )
            for _ in range(3)
        ]
        scores = orch.score_signal_batch(envelopes)
        assert len(scores) == 3
        assert all(isinstance(s, CandidateScore) for s in scores)

    def test_train_synthetic_returns_samples(self) -> None:
        session = MagicMock()
        orch = PipelineOrchestrator(session)
        samples = orch.train_scoring_model_on_synthetic(sample_count=10, seed=1)
        assert len(samples) == 10

    def test_evaluate_synthetic_returns_metrics(self) -> None:
        session = MagicMock()
        orch = PipelineOrchestrator(session)
        metrics = orch.evaluate_scoring_model_on_synthetic(
            train_sample_count=20, test_sample_count=10, seed=1
        )
        assert "mae" in metrics or "MAE" in str(metrics)


class TestPipelineIntegrations:
    """Test that the M5/M7 integration hooks remain callable."""

    @pytest.mark.asyncio
    async def test_nlp_extraction_returns_signal_envelope(self) -> None:
        session = MagicMock()
        orch = PipelineOrchestrator(session)
        cid = uuid4()
        profile = CandidateProfile(
            candidate_id=cid,
            selected_program="CS",
            model_input=ModelInput(),
            metadata=ProfileMetadata(data_completeness=0.8),
            completeness=0.8,
            data_flags=[],
            created_at="2026-03-27T12:00:00Z",
        )

        envelope = await orch._run_nlp_extraction(cid, profile)

        assert isinstance(envelope, SignalEnvelope)
        assert envelope.candidate_id == cid
        assert envelope.selected_program == "CS"
        assert envelope.program_id
        assert envelope.signal_schema_version == "v1"

    @pytest.mark.asyncio
    async def test_explainability_generation_does_not_raise(self) -> None:
        session = MagicMock()
        orch = PipelineOrchestrator(session)
        cid = uuid4()
        envelope = SignalEnvelope(
            candidate_id=cid,
            signal_schema_version="v1",
            completeness=0.8,
            signals={},
        )
        score = _make_fake_score(cid)

        await orch._run_explainability(cid, envelope, score)
