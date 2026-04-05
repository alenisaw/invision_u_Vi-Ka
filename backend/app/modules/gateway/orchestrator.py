from __future__ import annotations

import logging
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

    __slots__ = ("candidate_id", "profile", "score", "pipeline_status")

    def __init__(
        self,
        candidate_id: UUID,
        profile: CandidateProfile,
        score: CandidateScore,
        pipeline_status: str,
    ) -> None:
        self.candidate_id = candidate_id
        self.profile = profile
        self.score = score
        self.pipeline_status = pipeline_status

    def to_dict(self) -> dict:
        return {
            "candidate_id": str(self.candidate_id),
            "pipeline_status": self.pipeline_status,
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
        """Execute the full pipeline for a single candidate.

        Steps:
            1. Input Intake вЂ” validate and create the candidate record.
            2. ASR вЂ” transcribe submitted media when present.
            3. Privacy вЂ” separate operational layers and redact PII.
            4. Profile вЂ” assemble the canonical candidate profile.
            5. Extraction вЂ” derive structured analytical signals.
            6. Scoring вЂ” compute candidate evaluation outputs.
            7. Explanation вЂ” generate reviewer-facing narrative output.
        """
        # Step 1: Input Intake
        intake_service = CandidateIntakeService(self.session)
        intake_response = await intake_service.intake_candidate(payload)
        candidate_id = UUID(intake_response.candidate_id)

        # Step 2: ASR
        asr_transcript, asr_confidence, asr_flags = await self._run_asr_transcription(
            candidate_id,
            payload,
        )

        # Step 3: Privacy
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

        # Step 4: Profile
        profile_service = ProfileService(self.session)
        profile = await profile_service.build(candidate_id)

        # Step 5: Extraction
        envelope = await self._run_nlp_extraction(candidate_id, profile)

        # Step 6: Scoring
        score = self.scoring.score_candidate(envelope)
        await self._persist_score(candidate_id, score)

        # Step 7: Explanation
        await self._run_explainability(candidate_id, envelope, score)

        await self.repository.update_pipeline_status(candidate_id, "completed")
        await self.repository.create_audit_log(
            entity_type="candidate",
            entity_id=candidate_id,
            action="pipeline_completed",
            actor="system",
            details={
                "recommendation_status": score.recommendation_status,
                "review_priority_index": score.review_priority_index,
            },
        )
        await self.repository.commit()

        return PipelineResult(
            candidate_id=candidate_id,
            profile=profile,
            score=score,
            pipeline_status="completed",
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
            flags = (
                ["essay_replaced_by_video_transcript"]
                if not (payload.content.essay_text or "").strip()
                else []
            )
            return transcript_override, 1.0, flags

        video_reference = (payload.content.video_url or "").strip()
        if not video_reference:
            return None, None, []

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

    async def _run_nlp_extraction(self, candidate_id: UUID, profile: CandidateProfile) -> SignalEnvelope:
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
            return extraction_service.extract_signals(request)
        except Exception as exc:
            logger.warning(
                "Extraction stage failed for candidate %s, using empty signals fallback: %s",
                candidate_id,
                exc.__class__.__name__,
            )
            return SignalEnvelope(
                candidate_id=candidate_id,
                signal_schema_version="v1",
                extraction_model_version="fallback",
                selected_program=profile.selected_program or "",
                completeness=profile.completeness,
                data_flags=profile.data_flags,
                signals={},
            )

    async def _run_explainability(
        self,
        candidate_id: UUID,
        envelope: SignalEnvelope,
        score: CandidateScore,
    ) -> None:
        """Run explanation generation and skip gracefully if the stage is unavailable."""
        try:
            from app.modules.explanation.service import ExplanationService

            explain_service = ExplanationService(self.session)
            await explain_service.generate(candidate_id, envelope, score)
        except Exception as exc:
            logger.warning(
                "Explanation stage failed for candidate %s, skipping: %s",
                candidate_id,
                exc.__class__.__name__,
            )

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
