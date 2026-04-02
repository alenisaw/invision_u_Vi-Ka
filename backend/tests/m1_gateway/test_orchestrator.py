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
    async def test_asr_failure_forces_human_review_flags(self) -> None:
        session = MagicMock()
        orch = PipelineOrchestrator(session)
        cid = uuid4()
        payload = CandidateIntakeRequest(
            personal=PersonalInfo(
                first_name="Test",
                last_name="User",
                date_of_birth=date(2005, 1, 1),
            ),
            academic=AcademicInfo(selected_program="CS"),
            content=ContentInfo(
                essay_text="A test essay with enough words " * 5,
                video_url="https://youtube.com/watch?v=abc123",
            ),
            internal_test=InternalTestInfo(
                answers=[InternalTestAnswer(question_id="q1", answer="answer")]
            ),
        )

        with patch(
            "app.modules.m13_asr.service.asr_service.transcribe",
            side_effect=RuntimeError("boom"),
        ):
            transcript, confidence, flags = await orch._run_asr_transcription(cid, payload)

        assert transcript is None
        assert confidence == 0.0
        assert "requires_human_review" in flags
        assert "asr_processing_failed" in flags

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

    @pytest.mark.asyncio
    async def test_persist_score_stores_reviewer_fields_and_refreshes_rankings(self) -> None:
        session = MagicMock()
        orch = PipelineOrchestrator(session)
        orch.repository = AsyncMock()
        orch.repository.upsert_candidate_score.return_value = MagicMock(ranking_position=3)

        cid = uuid4()
        score = CandidateScore(
            candidate_id=cid,
            program_id="computer_science",
            sub_scores={"leadership_potential": 0.7},
            program_weight_profile={"leadership_potential": 0.2},
            review_priority_index=0.65,
            recommendation_status="RECOMMEND",
            decision_summary="Candidate scored successfully.",
            confidence=0.8,
            confidence_band="HIGH",
            manual_review_required=True,
            human_in_loop_required=True,
            uncertainty_flag=True,
            shortlist_eligible=False,
            review_recommendation="REQUIRES_MANUAL_REVIEW",
            review_reasons=["manual review required"],
            top_strengths=["leadership_potential"],
            top_risks=["low_signal_coverage"],
            score_delta_vs_baseline=0.05,
            caution_flags=["possible_ai_use"],
            score_breakdown={"baseline_rpi": 0.6},
            model_family="gbr",
            scoring_version="m6-v1",
        )

        await orch._persist_score(cid, score)

        persisted = orch.repository.upsert_candidate_score.await_args.kwargs
        assert persisted["candidate_id"] == cid
        assert persisted["manual_review_required"] is True
        assert persisted["review_recommendation"] == "REQUIRES_MANUAL_REVIEW"
        assert persisted["top_strengths"] == ["leadership_potential"]
        assert persisted["score_payload"]["candidate_id"] == str(cid)
        orch.repository.refresh_score_rankings.assert_awaited_once()
        orch.repository.update_pipeline_status.assert_awaited_once_with(cid, "scored")
        assert score.ranking_position == 3
