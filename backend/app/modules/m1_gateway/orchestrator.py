from __future__ import annotations

import logging
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.m2_intake.schemas import CandidateIntakeRequest
from app.modules.m2_intake.service import CandidateIntakeService
from app.modules.m3_privacy.service import PrivacyService
from app.modules.m4_profile.schemas import CandidateProfile
from app.modules.m4_profile.service import ProfileService
from app.modules.m6_scoring.schemas import (
    CandidateScore,
    LabeledEnvelope,
    SignalEnvelope,
)
from app.modules.m6_scoring.service import ScoringService
from app.modules.m9_storage import StorageRepository

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
    """Coordinates the full candidate pipeline: M2 → M3 → M4 → M5 → M6 → M7."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = StorageRepository(session)
        self.scoring = ScoringService()

    async def run_pipeline(self, payload: CandidateIntakeRequest) -> PipelineResult:
        """Execute the full pipeline for a single candidate.

        Steps:
            1. M2 Intake — validate and create candidate record
            2. M3 Privacy — separate into 3 layers, redact PII
            3. M4 Profile — assemble unified profile
            4. M5 NLP — extract signals (skipped if M5 not ready)
            5. M6 Scoring — compute scores
            6. M7 Explainability — generate explanation (skipped if M7 not ready)
        """
        # Step 1: M2 Intake
        intake_service = CandidateIntakeService(self.session)
        intake_result = intake_service.intake_candidate(payload)
        intake_response = await intake_result
        candidate_id = UUID(intake_response.candidate_id)

        # Step 1.5: M13 ASR
        asr_transcript, asr_confidence, asr_flags = await self._run_asr_transcription(candidate_id, payload)

        # Step 2: M3 Privacy
        privacy_service = PrivacyService(self.session)
        intake_svc = CandidateIntakeService(self.session)
        layers = await privacy_service.process(
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

        # Step 3: M4 Profile
        profile_service = ProfileService(self.session)
        profile = await profile_service.build(candidate_id)

        # Step 4: M5 NLP Signal Extraction
        envelope = await self._run_nlp_extraction(candidate_id, profile)

        # Step 5: M6 Scoring
        score = self.scoring.score_candidate(envelope)
        await self._persist_score(candidate_id, score)

        # Step 6: M7 Explainability (skip if not ready)
        await self._run_explainability(candidate_id, envelope, score)

        # Final status
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

    async def run_batch(
        self, payloads: list[CandidateIntakeRequest]
    ) -> list[PipelineResult]:
        """Run the pipeline for multiple candidates sequentially."""
        results: list[PipelineResult] = []
        for payload in payloads:
            result = await self.run_pipeline(payload)
            results.append(result)
        return results

    # --- M5 integration (stub until teammates deliver) ---

    async def _run_asr_transcription(
        self,
        candidate_id: UUID,
        payload: CandidateIntakeRequest,
    ) -> tuple[str | None, float | None, list[str]]:
        """Call M13 before privacy separation so transcript enters Layer 3 safely."""

        video_reference = (payload.content.video_url or "").strip()
        if not video_reference:
            return None, None, []

        try:
            from app.modules.m13_asr.schemas import ASRRequest
            from app.modules.m13_asr.service import asr_service

            parsed = urlparse(video_reference)
            request = ASRRequest(
                candidate_id=candidate_id,
                video_url=video_reference if parsed.scheme in {"http", "https"} else None,
                media_path=video_reference if parsed.scheme not in {"http", "https"} else None,
                selected_program=payload.academic.selected_program,
            )
            result = asr_service.transcribe(request)
            return result.transcript, result.mean_confidence, result.flags
        except (ImportError, AttributeError, NotImplementedError, ValueError, RuntimeError, FileNotFoundError) as exc:
            logger.warning(
                "M13 ASR failed for candidate %s, forcing human review: %s",
                candidate_id,
                exc.__class__.__name__,
            )
            return None, 0.0, ["asr_processing_failed", "requires_human_review"]

    async def _run_nlp_extraction(
        self, candidate_id: UUID, profile: CandidateProfile
    ) -> SignalEnvelope:
        """Call M5 for signal extraction. Falls back to empty signals if M5 is not ready."""
        try:
            from app.modules.m5_nlp.schemas import M5ExtractionRequest
            from app.modules.m5_nlp.service import nlp_signal_extraction_service

            request = M5ExtractionRequest(
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
            return nlp_signal_extraction_service.extract_signals(request)
        except Exception as exc:
            logger.warning(
                "M5 NLP failed for candidate %s, using empty signals fallback: %s",
                candidate_id,
                exc.__class__.__name__,
            )
            return SignalEnvelope(
                candidate_id=candidate_id,
                signal_schema_version="v1",
                m5_model_version="stub",
                selected_program=profile.selected_program or "",
                completeness=profile.completeness,
                data_flags=profile.data_flags,
                signals={},
            )

    # --- M7 integration (stub until teammates deliver) ---

    async def _run_explainability(
        self,
        candidate_id: UUID,
        envelope: SignalEnvelope,
        score: CandidateScore,
        ) -> None:
        """Call M7 for explanation generation. Skips gracefully if M7 is not ready."""
        try:
            from app.modules.m7_explainability.service import ExplainabilityService

            explain_service = ExplainabilityService(self.session)
            await explain_service.generate(candidate_id, envelope, score)
        except Exception as exc:
            logger.warning(
                "M7 Explainability failed for candidate %s, skipping: %s",
                candidate_id,
                exc.__class__.__name__,
            )

    # --- Persist score to DB ---

    async def _persist_score(self, candidate_id: UUID, score: CandidateScore) -> None:
        """Save M6 scoring result to database."""
        await self.repository.upsert_candidate_score(
            candidate_id=candidate_id,
            sub_scores=score.sub_scores,
            review_priority_index=score.review_priority_index,
            recommendation_status=score.recommendation_status,
            confidence=score.confidence,
            shortlist_eligible=score.shortlist_eligible,
            scoring_version=score.scoring_version,
        )
        await self.repository.update_pipeline_status(candidate_id, "scored")

    # --- Direct M6 scoring (kept for backward compatibility) ---

    def score_signals(self, envelope: SignalEnvelope) -> CandidateScore:
        """Score one canonical signal envelope directly (bypasses full pipeline)."""
        return self.scoring.score_candidate(envelope)

    def score_signal_batch(self, envelopes: list[SignalEnvelope]) -> list[CandidateScore]:
        """Score and rank a batch of signal envelopes directly."""
        return self.scoring.score_batch(envelopes)

    def train_scoring_model_on_synthetic(
        self, sample_count: int = 300, seed: int = 42
    ) -> list[LabeledEnvelope]:
        """Train the M6 refinement layer on synthetic data."""
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
