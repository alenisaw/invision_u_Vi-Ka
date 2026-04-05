from __future__ import annotations

import logging
from time import perf_counter
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.intake.schemas import CandidateIntakeRequest
from app.modules.intake.service import CandidateIntakeService
from app.modules.privacy.service import PrivacyService
from app.modules.profile.schemas import CandidateProfile
from app.modules.profile.service import ProfileService
from app.modules.scoring.schemas import CandidateScore, LabeledEnvelope, SignalEnvelope
from app.modules.scoring.service import ScoringService
from app.modules.storage import StorageRepository

logger = logging.getLogger(__name__)


class PipelineResult:
    """Holds the output of a full pipeline run."""

    __slots__ = (
        "candidate_id",
        "profile",
        "score",
        "pipeline_status",
        "pipeline_quality_status",
        "quality_flags",
        "stage_latencies_ms",
        "total_latency_ms",
    )

    def __init__(
        self,
        candidate_id: UUID,
        profile: CandidateProfile,
        score: CandidateScore,
        pipeline_status: str,
        pipeline_quality_status: str = "healthy",
        quality_flags: list[str] | None = None,
        stage_latencies_ms: dict[str, float] | None = None,
        total_latency_ms: float = 0.0,
    ) -> None:
        self.candidate_id = candidate_id
        self.profile = profile
        self.score = score
        self.pipeline_status = pipeline_status
        self.pipeline_quality_status = pipeline_quality_status
        self.quality_flags = quality_flags or []
        self.stage_latencies_ms = stage_latencies_ms or {}
        self.total_latency_ms = total_latency_ms

    def to_dict(self) -> dict:
        return {
            "candidate_id": str(self.candidate_id),
            "pipeline_status": self.pipeline_status,
            "pipeline_quality_status": self.pipeline_quality_status,
            "quality_flags": self.quality_flags,
            "stage_latencies_ms": self.stage_latencies_ms,
            "total_latency_ms": self.total_latency_ms,
            "score": self.score.model_dump(mode="json"),
            "completeness": self.profile.completeness,
            "data_flags": self.profile.data_flags,
        }


class PipelineOrchestrator:
    """Coordinates the candidate pipeline from input intake through explanation."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = StorageRepository(session)
        self.scoring = ScoringService()

    async def run_pipeline(self, payload: CandidateIntakeRequest) -> PipelineResult:
        """Execute the full pipeline for a single candidate."""

        stage_latencies_ms: dict[str, float] = {}
        total_started_at = perf_counter()

        started_at = perf_counter()
        intake_service = CandidateIntakeService(self.session)
        intake_response = await intake_service.intake_candidate(payload)
        stage_latencies_ms["input_intake"] = round((perf_counter() - started_at) * 1000.0, 2)
        candidate_id = UUID(intake_response.candidate_id)

        started_at = perf_counter()
        asr_transcript, asr_confidence, asr_flags = await self._run_asr_transcription(
            candidate_id,
            payload,
        )
        stage_latencies_ms["asr"] = round((perf_counter() - started_at) * 1000.0, 2)

        started_at = perf_counter()
        privacy_service = PrivacyService(self.session)
        intake_svc = CandidateIntakeService(self.session)
        await privacy_service.process(
            candidate_id=candidate_id,
            payload=payload,
            age_eligible=intake_svc._check_age_eligibility(payload.personal.date_of_birth),
            language_threshold_met=intake_svc._check_language_threshold(
                payload.academic.language_exam_type,
                payload.academic.language_score,
            ),
            data_completeness=intake_svc._compute_completeness(payload),
            data_flags=intake_svc._build_data_flags(payload),
            video_transcript=asr_transcript,
            asr_confidence=asr_confidence,
            asr_flags=asr_flags,
        )
        stage_latencies_ms["privacy"] = round((perf_counter() - started_at) * 1000.0, 2)

        started_at = perf_counter()
        profile_service = ProfileService(self.session)
        profile = await profile_service.build(candidate_id)
        stage_latencies_ms["profile"] = round((perf_counter() - started_at) * 1000.0, 2)

        started_at = perf_counter()
        envelope, extraction_flags = await self._run_extraction(candidate_id, profile)
        stage_latencies_ms["extraction"] = round((perf_counter() - started_at) * 1000.0, 2)

        started_at = perf_counter()
        score = self.scoring.score_candidate(envelope)
        await self._persist_score(candidate_id, score)
        stage_latencies_ms["scoring"] = round((perf_counter() - started_at) * 1000.0, 2)

        started_at = perf_counter()
        explanation_flags = await self._run_explanation(candidate_id, envelope, score)
        stage_latencies_ms["explanation"] = round((perf_counter() - started_at) * 1000.0, 2)

        quality_flags = self._build_quality_flags(
            asr_flags=asr_flags,
            extraction_flags=extraction_flags,
            explanation_flags=explanation_flags,
            score=score,
            envelope=envelope,
        )
        pipeline_quality_status = self._build_pipeline_quality_status(quality_flags, score)
        total_latency_ms = round((perf_counter() - total_started_at) * 1000.0, 2)

        await self.repository.update_pipeline_status(candidate_id, "completed")
        await self.repository.create_audit_log(
            entity_type="candidate",
            entity_id=candidate_id,
            action="pipeline_completed",
            actor="system",
            details={
                "recommendation_status": score.recommendation_status,
                "review_priority_index": score.review_priority_index,
                "pipeline_quality_status": pipeline_quality_status,
                "quality_flags": quality_flags,
                "stage_latencies_ms": stage_latencies_ms,
                "total_latency_ms": total_latency_ms,
            },
        )
        await self.repository.commit()
        logger.info(
            "pipeline_completed candidate=%s recommendation=%s quality=%s total_latency_ms=%.2f flags=%s",
            candidate_id,
            score.recommendation_status,
            pipeline_quality_status,
            total_latency_ms,
            ",".join(quality_flags) or "-",
        )

        return PipelineResult(
            candidate_id=candidate_id,
            profile=profile,
            score=score,
            pipeline_status="completed",
            pipeline_quality_status=pipeline_quality_status,
            quality_flags=quality_flags,
            stage_latencies_ms=stage_latencies_ms,
            total_latency_ms=total_latency_ms,
        )

    async def run_batch(self, payloads: list[CandidateIntakeRequest]) -> list[PipelineResult]:
        """Run the pipeline for multiple candidates sequentially."""

        results: list[PipelineResult] = []
        for payload in payloads:
            results.append(await self.run_pipeline(payload))
        return results

    async def _run_asr_transcription(
        self,
        candidate_id: UUID,
        payload: CandidateIntakeRequest,
    ) -> tuple[str | None, float | None, list[str]]:
        """Run ASR before privacy separation so transcript enters the safe content layer."""

        transcript_override = (payload.content.transcript_text or "").strip()
        if transcript_override:
            flags = ["transcript_provided_by_input"]
            if not (payload.content.essay_text or "").strip():
                flags.append("essay_replaced_by_video_transcript")
            return transcript_override, 1.0, flags

        video_reference = (payload.content.video_url or "").strip()
        if not video_reference:
            return None, None, ["missing_transcript"]

        try:
            from app.modules.asr.schemas import ASRRequest
            from app.modules.asr.service import asr_service

            parsed = urlparse(video_reference)
            request = ASRRequest(
                candidate_id=candidate_id,
                video_url=video_reference if parsed.scheme in {"http", "https"} else None,
                media_path=video_reference if parsed.scheme not in {"http", "https"} else None,
                selected_program=payload.academic.selected_program,
            )
            result = asr_service.transcribe(request)
            flags = list(result.flags)
            if result.transcript and not (payload.content.essay_text or "").strip():
                flags.append("essay_replaced_by_video_transcript")
            return result.transcript, result.mean_confidence, list(dict.fromkeys(flags))
        except (
            ImportError,
            AttributeError,
            NotImplementedError,
            ValueError,
            RuntimeError,
            FileNotFoundError,
        ) as exc:
            logger.warning(
                "ASR stage failed for candidate %s, forcing human review: %s",
                candidate_id,
                exc.__class__.__name__,
            )
            return None, 0.0, ["asr_processing_failed", "requires_human_review"]

    async def _run_extraction(
        self,
        candidate_id: UUID,
        profile: CandidateProfile,
    ) -> tuple[SignalEnvelope, list[str]]:
        """Run extraction and fall back to an empty envelope when the stage is unavailable."""

        try:
            from app.modules.extraction.schemas import ExtractionRequest
            from app.modules.extraction.service import extraction_service

            request = ExtractionRequest(
                candidate_id=candidate_id,
                completeness=profile.completeness,
                data_flags=profile.data_flags,
                selected_program=profile.selected_program or "",
                essay_text=profile.model_input.essay_text or "",
                video_transcript=profile.model_input.video_transcript or "",
                experience_summary=profile.model_input.experience_summary or "",
                project_descriptions=list(profile.model_input.project_descriptions),
                internal_test_answers=list(profile.model_input.internal_test_answers),
            )
            envelope = extraction_service.extract_signals(request)
            flags: list[str] = []
            if not envelope.signals:
                flags.append("empty_signal_envelope")
            if envelope.extraction_model_version == "fallback":
                flags.append("llm_extraction_fallback_used")
            if any(flag == "requires_human_review" for flag in envelope.data_flags):
                flags.append("extraction_requires_human_review")
            return envelope, flags
        except Exception as exc:
            logger.warning(
                "Extraction stage failed for candidate %s, using empty signals fallback: %s",
                candidate_id,
                exc.__class__.__name__,
            )
            return (
                SignalEnvelope(
                    candidate_id=candidate_id,
                    signal_schema_version="v1",
                    extraction_model_version="fallback",
                    selected_program=profile.selected_program or "",
                    completeness=profile.completeness,
                    data_flags=profile.data_flags,
                    signals={},
                ),
                ["llm_extraction_fallback_used", "empty_signal_envelope", "requires_human_review"],
            )

    async def _run_explanation(
        self,
        candidate_id: UUID,
        envelope: SignalEnvelope,
        score: CandidateScore,
    ) -> list[str]:
        """Run explanation generation and skip gracefully if the stage is unavailable."""

        try:
            from app.modules.explanation.service import ExplanationService

            explain_service = ExplanationService(self.session)
            await explain_service.generate(candidate_id, envelope, score)
            return []
        except Exception as exc:
            logger.warning(
                "Explanation stage failed for candidate %s, skipping: %s",
                candidate_id,
                exc.__class__.__name__,
            )
            return ["explanation_partial"]

    async def _run_nlp_extraction(
        self,
        candidate_id: UUID,
        profile: CandidateProfile,
    ) -> SignalEnvelope:
        """Backward-compatible wrapper for legacy extraction hook."""

        envelope, _ = await self._run_extraction(candidate_id, profile)
        return envelope

    async def _run_explainability(
        self,
        candidate_id: UUID,
        envelope: SignalEnvelope,
        score: CandidateScore,
    ) -> None:
        """Backward-compatible wrapper for legacy explanation hook."""

        await self._run_explanation(candidate_id, envelope, score)

    async def _persist_score(self, candidate_id: UUID, score: CandidateScore) -> None:
        """Persist scoring output to storage."""

        score_payload = score.model_dump(mode="json")
        persisted_score = await self.repository.upsert_candidate_score(
            candidate_id=candidate_id,
            sub_scores=score.sub_scores,
            program_id=score.program_id or None,
            program_weight_profile=score.program_weight_profile,
            review_priority_index=score.review_priority_index,
            recommendation_status=score.recommendation_status,
            decision_summary=score.decision_summary or None,
            confidence=score.confidence,
            confidence_band=score.confidence_band,
            manual_review_required=score.manual_review_required,
            human_in_loop_required=score.human_in_loop_required,
            uncertainty_flag=score.uncertainty_flag,
            shortlist_eligible=score.shortlist_eligible,
            review_recommendation=score.review_recommendation,
            review_reasons=score.review_reasons,
            top_strengths=score.top_strengths,
            top_risks=score.top_risks,
            score_delta_vs_baseline=score.score_delta_vs_baseline,
            ranking_position=score.ranking_position,
            caution_flags=score.caution_flags,
            score_breakdown=score.score_breakdown,
            model_family=score.model_family,
            scoring_version=score.scoring_version,
            score_payload=score_payload,
        )
        await self.repository.refresh_score_rankings()
        score.ranking_position = persisted_score.ranking_position
        await self.repository.update_pipeline_status(candidate_id, "scored")

    def score_signals(self, envelope: SignalEnvelope) -> CandidateScore:
        """Score one canonical signal envelope directly without the full pipeline."""

        return self.scoring.score_candidate(envelope)

    def score_signal_batch(self, envelopes: list[SignalEnvelope]) -> list[CandidateScore]:
        """Score and rank a batch of signal envelopes directly."""

        return self.scoring.score_batch(envelopes)

    def train_scoring_model_on_synthetic(
        self,
        sample_count: int = 300,
        seed: int = 42,
    ) -> list[LabeledEnvelope]:
        """Train the scoring refinement layer on synthetic data."""

        return self.scoring.train_on_synthetic(sample_count=sample_count, seed=seed)

    def evaluate_scoring_model_on_synthetic(
        self,
        train_sample_count: int = 300,
        test_sample_count: int = 120,
        seed: int = 42,
    ) -> dict[str, float | int]:
        """Run synthetic holdout evaluation."""

        return self.scoring.evaluate_on_synthetic(
            train_sample_count=train_sample_count,
            test_sample_count=test_sample_count,
            seed=seed,
        )

    @staticmethod
    def _build_quality_flags(
        *,
        asr_flags: list[str],
        extraction_flags: list[str],
        explanation_flags: list[str],
        score: CandidateScore,
        envelope: SignalEnvelope,
    ) -> list[str]:
        flags = list(asr_flags) + list(extraction_flags) + list(explanation_flags)
        if score.manual_review_required:
            flags.append("manual_review_required")
        if score.uncertainty_flag:
            flags.append("uncertainty_flag")
        if not envelope.signals:
            flags.append("empty_signal_envelope")
        return list(dict.fromkeys(flags))

    @staticmethod
    def _build_pipeline_quality_status(
        quality_flags: list[str],
        score: CandidateScore,
    ) -> str:
        degraded_flags = {
            "asr_processing_failed",
            "llm_extraction_fallback_used",
            "empty_signal_envelope",
            "explanation_partial",
        }
        if score.manual_review_required:
            return "manual_review_required"
        if any(flag in degraded_flags for flag in quality_flags):
            return "degraded"
        if quality_flags:
            return "partial"
        return "healthy"
