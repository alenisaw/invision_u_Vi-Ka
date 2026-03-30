from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.queue import JobQueue, get_job_queue
from app.core.security import decrypt_json, encrypt_json
from app.modules.m1_gateway.schemas import (
    AsyncPipelineSubmitResponse,
    CandidatePipelineStatusView,
    PipelineJobEventView,
    PipelineJobStatusView,
    PipelineStageRunView,
)
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
DEFAULT_BATCH_CONCURRENCY = 4
PIPELINE_STAGE_SEQUENCE = (
    "intake",
    "privacy",
    "asr",
    "profile",
    "nlp",
    "scoring",
    "explainability",
)
ASYNC_PIPELINE_SCHEMA_VERSION = "candidate_intake_v1"


@dataclass(frozen=True)
class NLPStageResult:
    status: str
    envelope: SignalEnvelope | None = None
    reason: str | None = None


class StageExecutionError(RuntimeError):
    def __init__(self, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code


class PipelineResult:
    """Holds the output of a full pipeline run."""

    __slots__ = ("candidate_id", "profile", "score", "pipeline_status", "processing_issue")

    def __init__(
        self,
        candidate_id: UUID,
        profile: CandidateProfile,
        score: CandidateScore | None,
        pipeline_status: str,
        processing_issue: str | None = None,
    ) -> None:
        self.candidate_id = candidate_id
        self.profile = profile
        self.score = score
        self.pipeline_status = pipeline_status
        self.processing_issue = processing_issue

    def to_dict(self) -> dict:
        return {
            "candidate_id": str(self.candidate_id),
            "pipeline_status": self.pipeline_status,
            "score": self.score.model_dump(mode="json") if self.score is not None else None,
            "completeness": self.profile.completeness,
            "data_flags": self.profile.data_flags,
            "processing_issue": self.processing_issue,
        }


class PipelineOrchestrator:
    """Coordinates the full candidate pipeline: M2 → M3 → M4 → M5 → M6 → M7."""

    def __init__(self, session: AsyncSession, job_queue: JobQueue | None = None) -> None:
        self.session = session
        self.repository = StorageRepository(session)
        self.scoring = ScoringService()
        self.job_queue = job_queue or get_job_queue()

    async def run_pipeline_inline(self, payload: CandidateIntakeRequest) -> PipelineResult:
        """Execute one full pipeline run inline for tests and local diagnostics.

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
        nlp_result = await self._run_nlp_extraction(candidate_id, profile)
        if nlp_result.status != "ok" or nlp_result.envelope is None:
            pipeline_status = (
                "requires_manual_review"
                if nlp_result.status == "insufficient_data"
                else "failed"
            )
            audit_action = (
                "nlp_insufficient_input"
                if nlp_result.status == "insufficient_data"
                else "nlp_extraction_failed"
            )
            reason = nlp_result.reason or "m5_unavailable"
            await self.repository.update_pipeline_status(candidate_id, pipeline_status)
            await self.repository.create_audit_log(
                entity_type="candidate",
                entity_id=candidate_id,
                action=audit_action,
                actor="system",
                details={
                    "reason": reason,
                    "selected_program": profile.selected_program,
                    "data_flags": profile.data_flags,
                },
            )
            await self.repository.commit()
            return PipelineResult(
                candidate_id=candidate_id,
                profile=profile,
                score=None,
                pipeline_status=pipeline_status,
                processing_issue=reason,
            )
        envelope = nlp_result.envelope

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

    async def submit_async(
        self,
        payload: CandidateIntakeRequest,
        *,
        requested_by: str = "system",
    ) -> AsyncPipelineSubmitResponse:
        """Accept a candidate, persist a queued job, and return tracking identifiers."""
        intake_service = CandidateIntakeService(self.session)
        intake_response = await intake_service.intake_candidate(payload)
        candidate_id = UUID(intake_response.candidate_id)

        queued_at = datetime.now(timezone.utc)
        payload_encrypted = encrypt_json(payload.model_dump(mode="json", exclude_none=True))

        job = await self.repository.create_pipeline_job(
            candidate_id=candidate_id,
            job_type="candidate_submission",
            status="queued",
            current_stage="privacy",
            execution_mode="async",
            requested_by=requested_by,
            payload_schema_version=ASYNC_PIPELINE_SCHEMA_VERSION,
            payload_encrypted=payload_encrypted,
        )

        await self.repository.update_pipeline_status(candidate_id, "queued")
        await self.repository.create_pipeline_stage_run(
            job_id=job.id,
            stage_name="intake",
            status="completed",
            attempt_count=1,
            started_at=queued_at,
            finished_at=queued_at,
            duration_ms=0,
            output_ref={"candidate_id": str(candidate_id)},
        )
        for stage_name in PIPELINE_STAGE_SEQUENCE[1:]:
            await self.repository.create_pipeline_stage_run(
                job_id=job.id,
                stage_name=stage_name,
                status="queued",
            )

        await self.repository.create_pipeline_job_event(
            job_id=job.id,
            event_type="job_created",
            status="queued",
            payload={
                "candidate_id": str(candidate_id),
                "requested_by": requested_by,
                "current_stage": "privacy",
            },
        )
        await self.repository.create_pipeline_job_event(
            job_id=job.id,
            event_type="stage_completed",
            stage_name="intake",
            status="completed",
            payload={"candidate_id": str(candidate_id)},
        )
        await self.repository.create_pipeline_job_event(
            job_id=job.id,
            event_type="job_queued",
            stage_name="privacy",
            status="queued",
            payload={"candidate_id": str(candidate_id)},
        )
        await self.repository.create_audit_log(
            entity_type="pipeline_job",
            entity_id=job.id,
            action="pipeline_job_queued",
            actor=requested_by,
            details={
                "candidate_id": str(candidate_id),
                "current_stage": "privacy",
                "job_type": job.job_type,
            },
        )
        await self.repository.commit()
        try:
            await self.job_queue.enqueue_job(str(job.id))
        except Exception as exc:
            logger.exception("Failed to enqueue pipeline job %s", job.id)
            await self.repository.update_pipeline_status(candidate_id, "failed")
            await self.repository.update_pipeline_job(
                job.id,
                status="failed",
                current_stage="queue",
                finished_at=datetime.now(timezone.utc),
                error_code="queue_enqueue_failed",
                error_message=f"{exc.__class__.__name__}: {exc}",
            )
            await self.repository.create_pipeline_job_event(
                job_id=job.id,
                event_type="job_enqueue_failed",
                stage_name="queue",
                status="failed",
                payload={"error": f"{exc.__class__.__name__}: {exc}"},
            )
            await self.repository.create_audit_log(
                entity_type="pipeline_job",
                entity_id=job.id,
                action="pipeline_job_enqueue_failed",
                actor=requested_by,
                details={"error": f"{exc.__class__.__name__}: {exc}"},
            )
            await self.repository.commit()
            raise RuntimeError("Pipeline job was persisted but could not be enqueued") from exc

        return AsyncPipelineSubmitResponse(
            candidate_id=str(candidate_id),
            job_id=str(job.id),
            pipeline_status="queued",
            job_status="queued",
            current_stage="privacy",
            message="Candidate accepted and queued for asynchronous processing.",
        )

    async def submit_batch_async(
        self,
        payloads: list[CandidateIntakeRequest],
        *,
        requested_by: str = "system",
    ) -> list[AsyncPipelineSubmitResponse]:
        """Queue multiple candidates for asynchronous processing."""
        responses: list[AsyncPipelineSubmitResponse] = []
        for payload in payloads:
            responses.append(
                await self.submit_async(payload, requested_by=requested_by)
            )
        return responses

    async def get_job_status(self, job_id: UUID) -> PipelineJobStatusView:
        """Return the latest persisted job state with stage details."""
        job = await self.repository.get_pipeline_job_with_related(job_id)
        if job is None:
            raise ValueError(f"Pipeline job {job_id} not found")
        return self._build_job_status_view(job)

    async def list_job_events(self, job_id: UUID) -> list[PipelineJobEventView]:
        """Return the event stream for a persisted pipeline job."""
        job = await self.repository.get_pipeline_job(job_id)
        if job is None:
            raise ValueError(f"Pipeline job {job_id} not found")

        events = await self.repository.list_pipeline_job_events(job_id)
        return [
            PipelineJobEventView(
                id=str(event.id),
                event_type=event.event_type,
                stage_name=event.stage_name,
                status=event.status,
                payload=event.payload if isinstance(event.payload, dict) else {},
                created_at=event.created_at,
            )
            for event in events
        ]

    async def get_candidate_status(self, candidate_id: UUID) -> CandidatePipelineStatusView:
        """Return candidate-level pipeline status plus the latest job snapshot."""
        candidate = await self.repository.get_candidate(candidate_id)
        if candidate is None:
            raise ValueError(f"Candidate {candidate_id} not found")

        latest_job = await self.repository.get_latest_pipeline_job_for_candidate(candidate_id)
        return CandidatePipelineStatusView(
            candidate_id=str(candidate.id),
            pipeline_status=candidate.pipeline_status,
            selected_program=candidate.selected_program,
            latest_job=self._build_job_status_view(latest_job) if latest_job is not None else None,
        )

    async def get_queue_metrics(self) -> dict[str, object]:
        """Return queue depth and persisted pipeline job counters."""
        queue_depth = await self.job_queue.get_depth()
        job_counts = await self.repository.count_pipeline_jobs_by_status()
        job_stage_snapshot = await self.repository.count_pipeline_jobs_by_stage()
        stage_metrics = await self.repository.get_pipeline_stage_metrics()
        total_jobs = sum(job_counts.values())
        manual_review_jobs = job_counts.get("requires_manual_review", 0)
        failed_jobs = job_counts.get("failed", 0) + job_counts.get("dead_letter", 0)
        return {
            "queue_depth": queue_depth,
            "job_counts": job_counts,
            "job_stage_snapshot": job_stage_snapshot,
            "stage_metrics": stage_metrics,
            "manual_review_rate": 0.0 if total_jobs == 0 else round(manual_review_jobs / total_jobs, 4),
            "failure_rate": 0.0 if total_jobs == 0 else round(failed_jobs / total_jobs, 4),
        }

    async def list_dead_letter_jobs(self, limit: int = 100) -> list[PipelineJobStatusView]:
        job_ids = await self.job_queue.list_dead_jobs(limit=limit)
        return await self._load_job_views(job_ids)

    async def list_delayed_retry_jobs(self, limit: int = 100) -> list[PipelineJobStatusView]:
        job_ids = await self.job_queue.list_delayed_jobs(limit=limit)
        return await self._load_job_views(job_ids)

    async def requeue_pipeline_job(
        self,
        job_id: UUID,
        *,
        actor: str = "system",
    ) -> PipelineJobStatusView:
        job = await self.repository.get_pipeline_job_with_related(job_id)
        if job is None:
            raise ValueError(f"Pipeline job {job_id} not found")

        requeued = await self.job_queue.requeue_job(str(job_id))
        if not requeued and job.status not in {"queued", "retry_scheduled", "dead_letter", "failed"}:
            raise ValueError(f"Pipeline job {job_id} is not eligible for requeue")
        if not requeued:
            await self.job_queue.enqueue_job(str(job_id))

        await self.repository.update_pipeline_job(
            job_id,
            status="queued",
            current_stage=job.current_stage,
            finished_at=None,
            error_code=None,
            error_message=None,
        )
        await self.repository.update_pipeline_status(job.candidate_id, "queued")
        if job.current_stage:
            await self.repository.update_pipeline_stage_run(
                job_id,
                job.current_stage,
                status="queued",
                finished_at=None,
                duration_ms=None,
                error_code=None,
                error_message=None,
            )
        await self.repository.create_pipeline_job_event(
            job_id=job_id,
            event_type="job_requeued",
            stage_name=job.current_stage,
            status="queued",
            payload={"actor": actor},
        )
        await self.repository.create_audit_log(
            entity_type="pipeline_job",
            entity_id=job_id,
            action="pipeline_job_requeued",
            actor=actor,
            details={"candidate_id": str(job.candidate_id), "current_stage": job.current_stage},
        )
        await self.repository.commit()
        return await self.get_job_status(job_id)

    async def inspect_pipeline_job_ops(self, job_id: UUID) -> dict[str, object]:
        job_status = await self.get_job_status(job_id)
        queue_state = await self.job_queue.inspect_job(str(job_id))
        from app.modules.m1_gateway.worker import PipelineWorker

        retry_decision = PipelineWorker(job_queue=self.job_queue).inspect_retry_decision(
            job_status
        )
        return {
            "job": job_status.model_dump(mode="json"),
            "queue_state": queue_state,
            "retry_decision": retry_decision,
        }

    async def process_pipeline_job(self, job_id: UUID) -> PipelineJobStatusView:
        """Execute a queued pipeline job from the current stage to completion."""
        job = await self.repository.get_pipeline_job_with_related(job_id)
        if job is None:
            raise ValueError(f"Pipeline job {job_id} not found")

        if job.payload_encrypted is None:
            await self._fail_job(
                job_id,
                current_stage=job.current_stage,
                error_code="missing_payload",
                error_message="Pipeline job is missing encrypted source payload.",
            )
            return await self.get_job_status(job_id)

        payload = CandidateIntakeRequest.model_validate(decrypt_json(job.payload_encrypted))
        candidate_id = job.candidate_id
        intake_service = CandidateIntakeService(self.session)

        await self._mark_job_running(job_id, current_stage=job.current_stage or "privacy")

        privacy_ok, _ = await self._execute_stage_operation(
            job_id,
            "privacy",
            lambda: self._run_privacy_stage(
                candidate_id=candidate_id,
                payload=payload,
                intake_service=intake_service,
                job_id=job_id,
            ),
        )
        if not privacy_ok:
            return await self.get_job_status(job_id)

        asr_ok, _ = await self._execute_stage_operation(
            job_id,
            "asr",
            lambda: self._run_asr_stage(
                candidate_id=candidate_id,
                payload=payload,
                job_id=job_id,
            ),
        )
        if not asr_ok:
            return await self.get_job_status(job_id)

        profile_ok, profile = await self._execute_stage_operation(
            job_id,
            "profile",
            lambda: self._run_profile_stage(candidate_id=candidate_id, job_id=job_id),
        )
        if not profile_ok or profile is None:
            return await self.get_job_status(job_id)

        nlp_ok, nlp_result = await self._execute_stage_operation(
            job_id,
            "nlp",
            lambda: self._run_nlp_stage(candidate_id=candidate_id, profile=profile, job_id=job_id),
        )
        if not nlp_ok or nlp_result is None:
            return await self.get_job_status(job_id)
        if nlp_result.status != "ok" or nlp_result.envelope is None:
            return await self._finish_job_without_score(
                job_id=job_id,
                candidate_id=candidate_id,
                profile=profile,
                nlp_result=nlp_result,
            )

        scoring_ok, score = await self._execute_stage_operation(
            job_id,
            "scoring",
            lambda: self._run_scoring_stage(
                candidate_id=candidate_id,
                envelope=nlp_result.envelope,
                job_id=job_id,
            ),
        )
        if not scoring_ok or score is None:
            return await self.get_job_status(job_id)

        explain_ok, _ = await self._execute_stage_operation(
            job_id,
            "explainability",
            lambda: self._run_explainability_stage(
                candidate_id=candidate_id,
                envelope=nlp_result.envelope,
                score=score,
                job_id=job_id,
            ),
        )
        if not explain_ok:
            return await self.get_job_status(job_id)

        await self.repository.update_pipeline_status(candidate_id, "completed")
        await self.repository.update_pipeline_job(
            job_id,
            status="completed",
            current_stage="completed",
            finished_at=datetime.now(timezone.utc),
            error_code=None,
            error_message=None,
        )
        await self.repository.create_pipeline_job_event(
            job_id=job_id,
            event_type="job_completed",
            status="completed",
            payload={"candidate_id": str(candidate_id)},
        )
        await self.repository.create_audit_log(
            entity_type="pipeline_job",
            entity_id=job_id,
            action="pipeline_job_completed",
            actor="system",
            details={"candidate_id": str(candidate_id)},
        )
        await self.repository.commit()
        return await self.get_job_status(job_id)

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
            result = await asr_service.transcribe_async(request)
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
    ) -> NLPStageResult:
        """Call M5 for signal extraction and keep failure semantics explicit."""
        if not self._has_minimum_nlp_input(profile):
            return NLPStageResult(
                status="insufficient_data",
                reason="insufficient_model_input",
            )

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
            envelope = await asyncio.to_thread(
                nlp_signal_extraction_service.extract_signals,
                request,
            )
            return NLPStageResult(status="ok", envelope=envelope)
        except Exception as exc:
            logger.warning(
                "M5 NLP failed for candidate %s",
                candidate_id,
                exc_info=True,
            )
            error_code = self._classify_nlp_failure(exc)
            return NLPStageResult(
                status="failed",
                reason=f"{error_code}:{exc.__class__.__name__}",
            )

    def _classify_nlp_failure(self, exc: Exception) -> str:
        exc_text = f"{exc.__class__.__name__}:{exc}".lower()
        if "429" in exc_text or "rate limit" in exc_text:
            return "llm_rate_limited"
        if "timeout" in exc_text:
            return "llm_timeout"
        if "503" in exc_text or "502" in exc_text or "bad gateway" in exc_text:
            return "llm_provider_failed"
        return "m5_processing_failed"

    def _has_minimum_nlp_input(self, profile: CandidateProfile) -> bool:
        model_input = profile.model_input
        if (model_input.video_transcript or "").strip():
            return True
        if (model_input.essay_text or "").strip():
            return True
        if (model_input.experience_summary or "").strip():
            return True
        if any((project or "").strip() for project in model_input.project_descriptions):
            return True
        for answer in model_input.internal_test_answers:
            if isinstance(answer, dict) and str(answer.get("answer") or answer.get("answer_text") or "").strip():
                return True
        return False

    # --- M7 integration (stub until teammates deliver) ---

    async def _run_explainability(
        self,
        candidate_id: UUID,
        envelope: SignalEnvelope,
        score: CandidateScore,
        *,
        strict: bool = False,
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
                exc_info=True,
            )
            if strict:
                raise StageExecutionError(
                    "m7_generation_failed",
                    f"{exc.__class__.__name__}: {exc}",
                ) from exc

    # --- Persist score to DB ---

    async def _persist_score(self, candidate_id: UUID, score: CandidateScore) -> None:
        """Save M6 scoring result to database."""
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

    async def _run_privacy_stage(
        self,
        *,
        candidate_id: UUID,
        payload: CandidateIntakeRequest,
        intake_service: CandidateIntakeService,
        job_id: UUID,
    ) -> None:
        await self._mark_stage_running(job_id, "privacy")
        privacy_service = PrivacyService(self.session)
        await privacy_service.process(
            candidate_id=candidate_id,
            payload=payload,
            age_eligible=intake_service._check_age_eligibility(payload.personal.date_of_birth),
            language_threshold_met=intake_service._check_language_threshold(
                payload.academic.language_exam_type,
                payload.academic.language_score,
            ),
            data_completeness=intake_service._compute_completeness(payload),
            data_flags=intake_service._build_data_flags(payload),
            video_transcript=None,
            asr_confidence=None,
            asr_flags=[],
        )
        await self._mark_stage_completed(
            job_id,
            "privacy",
            output_ref={"candidate_id": str(candidate_id)},
        )

    async def _run_asr_stage(
        self,
        *,
        candidate_id: UUID,
        payload: CandidateIntakeRequest,
        job_id: UUID,
    ) -> None:
        await self._mark_stage_running(job_id, "asr")
        transcript, confidence, flags = await self._run_asr_transcription(candidate_id, payload)
        await self.repository.upsert_candidate_model_input(
            candidate_id=candidate_id,
            video_transcript=transcript,
            asr_confidence=confidence,
            asr_flags=flags,
        )
        await self.repository.create_audit_log(
            entity_type="candidate",
            entity_id=candidate_id,
            action="asr_stage_completed",
            actor="system",
            details={
                "has_transcript": bool(transcript),
                "asr_confidence": confidence,
                "asr_flags": flags,
            },
        )
        if "asr_processing_failed" in flags:
            raise StageExecutionError(
                "asr_provider_failed",
                "ASR provider failed before a reliable transcript could be produced.",
            )
        await self._mark_stage_completed(
            job_id,
            "asr",
            output_ref={
                "candidate_id": str(candidate_id),
                "has_transcript": bool(transcript),
                "asr_flags": flags,
            },
        )

    async def _run_profile_stage(
        self,
        *,
        candidate_id: UUID,
        job_id: UUID,
    ) -> CandidateProfile:
        await self._mark_stage_running(job_id, "profile")
        profile_service = ProfileService(self.session)
        profile = await profile_service.build(candidate_id)
        await self._mark_stage_completed(
            job_id,
            "profile",
            output_ref={"candidate_id": str(candidate_id), "completeness": profile.completeness},
        )
        return profile

    async def _run_nlp_stage(
        self,
        *,
        candidate_id: UUID,
        profile: CandidateProfile,
        job_id: UUID,
    ) -> NLPStageResult:
        await self._mark_stage_running(job_id, "nlp")
        result = await self._run_nlp_extraction(candidate_id, profile)
        if result.status == "ok" and result.envelope is not None:
            await self._mark_stage_completed(
                job_id,
                "nlp",
                output_ref={"candidate_id": str(candidate_id), "signal_count": len(result.envelope.signals)},
            )
            return result

        terminal_status = (
            "requires_manual_review" if result.status == "insufficient_data" else "failed"
        )
        default_error_code = (
            "insufficient_data"
            if result.status == "insufficient_data"
            else "m5_processing_failed"
        )
        stage_error_code = default_error_code
        if result.reason and ":" in result.reason:
            stage_error_code = result.reason.split(":", 1)[0] or default_error_code
        await self.repository.update_pipeline_status(candidate_id, terminal_status)
        await self.repository.update_pipeline_job(
            job_id,
            status=terminal_status,
            current_stage="nlp",
            finished_at=datetime.now(timezone.utc),
            error_code=stage_error_code,
            error_message=result.reason,
        )
        await self.repository.update_pipeline_stage_run(
            job_id,
            "nlp",
            status=terminal_status,
            error_code=stage_error_code,
            error_message=result.reason,
            finished_at=datetime.now(timezone.utc),
        )
        await self.repository.create_pipeline_job_event(
            job_id=job_id,
            event_type="stage_terminal",
            stage_name="nlp",
            status=terminal_status,
            payload={"reason": result.reason or result.status},
        )
        await self.repository.commit()
        return result

    async def _run_scoring_stage(
        self,
        *,
        candidate_id: UUID,
        envelope: SignalEnvelope,
        job_id: UUID,
    ) -> CandidateScore:
        await self._mark_stage_running(job_id, "scoring")
        score = self.scoring.score_candidate(envelope)
        await self._persist_score(candidate_id, score)
        await self._mark_stage_completed(
            job_id,
            "scoring",
            output_ref={
                "candidate_id": str(candidate_id),
                "recommendation_status": score.recommendation_status,
            },
        )
        return score

    async def _run_explainability_stage(
        self,
        *,
        candidate_id: UUID,
        envelope: SignalEnvelope,
        score: CandidateScore,
        job_id: UUID,
    ) -> None:
        await self._mark_stage_running(job_id, "explainability")
        await self._run_explainability(
            candidate_id,
            envelope,
            score,
            strict=True,
        )
        await self._mark_stage_completed(
            job_id,
            "explainability",
            output_ref={"candidate_id": str(candidate_id), "status": score.recommendation_status},
        )

    async def _finish_job_without_score(
        self,
        *,
        job_id: UUID,
        candidate_id: UUID,
        profile: CandidateProfile,
        nlp_result: NLPStageResult,
    ) -> PipelineJobStatusView:
        terminal_status = (
            "requires_manual_review"
            if nlp_result.status == "insufficient_data"
            else "failed"
        )
        await self.repository.update_pipeline_status(candidate_id, terminal_status)
        await self.repository.create_audit_log(
            entity_type="pipeline_job",
            entity_id=job_id,
            action="pipeline_job_stopped_before_scoring",
            actor="system",
            details={
                "candidate_id": str(candidate_id),
                "reason": nlp_result.reason or nlp_result.status,
                "selected_program": profile.selected_program,
                "data_flags": profile.data_flags,
            },
        )
        await self.repository.commit()
        return await self.get_job_status(job_id)

    async def _mark_job_running(self, job_id: UUID, *, current_stage: str) -> None:
        now = datetime.now(timezone.utc)
        job = await self.repository.get_pipeline_job(job_id)
        attempt_count = 1 if job is None else job.attempt_count + 1
        started_at = now if job is None or job.started_at is None else job.started_at
        await self.repository.update_pipeline_job(
            job_id,
            status="running",
            current_stage=current_stage,
            started_at=started_at,
            attempt_count=attempt_count,
            error_code=None,
            error_message=None,
        )
        await self.repository.create_pipeline_job_event(
            job_id=job_id,
            event_type="job_started",
            stage_name=current_stage,
            status="running",
            payload={"attempt_count": attempt_count},
        )
        await self.repository.commit()

    async def _mark_stage_running(self, job_id: UUID, stage_name: str) -> None:
        now = datetime.now(timezone.utc)
        stage_run = await self.repository.get_pipeline_stage_run(job_id, stage_name)
        attempt_count = 1 if stage_run is None else stage_run.attempt_count + 1
        if stage_run is None:
            await self.repository.create_pipeline_stage_run(
                job_id=job_id,
                stage_name=stage_name,
                status="running",
                attempt_count=attempt_count,
                started_at=now,
            )
        else:
            await self.repository.update_pipeline_stage_run(
                job_id,
                stage_name,
                status="running",
                attempt_count=attempt_count,
                started_at=now,
                finished_at=None,
                error_code=None,
                error_message=None,
            )
        await self.repository.update_pipeline_job(
            job_id,
            status="running",
            current_stage=stage_name,
            error_code=None,
            error_message=None,
        )
        await self.repository.create_pipeline_job_event(
            job_id=job_id,
            event_type="stage_started",
            stage_name=stage_name,
            status="running",
            payload={"attempt_count": attempt_count},
        )
        await self.repository.commit()

    async def _mark_stage_completed(
        self,
        job_id: UUID,
        stage_name: str,
        *,
        output_ref: dict[str, object] | None = None,
    ) -> None:
        now = datetime.now(timezone.utc)
        stage_run = await self.repository.get_pipeline_stage_run(job_id, stage_name)
        started_at = now if stage_run is None or stage_run.started_at is None else stage_run.started_at
        duration_ms = max(
            0,
            int((now - started_at).total_seconds() * 1000),
        )
        await self.repository.update_pipeline_stage_run(
            job_id,
            stage_name,
            status="completed",
            finished_at=now,
            duration_ms=duration_ms,
            output_ref=output_ref or {},
        )
        await self.repository.create_pipeline_job_event(
            job_id=job_id,
            event_type="stage_completed",
            stage_name=stage_name,
            status="completed",
            payload=output_ref or {},
        )
        await self.repository.commit()

    async def _fail_job(
        self,
        job_id: UUID,
        *,
        current_stage: str | None,
        error_code: str,
        error_message: str,
    ) -> None:
        now = datetime.now(timezone.utc)
        stage_name = current_stage or "unknown"
        await self.repository.update_pipeline_job(
            job_id,
            status="failed",
            current_stage=stage_name,
            finished_at=now,
            error_code=error_code,
            error_message=error_message,
        )
        stage_run = await self.repository.get_pipeline_stage_run(job_id, stage_name)
        if stage_run is not None:
            await self.repository.update_pipeline_stage_run(
                job_id,
                stage_name,
                status="failed",
                finished_at=now,
                error_code=error_code,
                error_message=error_message,
            )
        await self.repository.create_pipeline_job_event(
            job_id=job_id,
            event_type="job_failed",
            stage_name=stage_name,
            status="failed",
            payload={"error_code": error_code, "error_message": error_message},
        )
        await self.repository.create_audit_log(
            entity_type="pipeline_job",
            entity_id=job_id,
            action="pipeline_job_failed",
            actor="system",
            details={"error_code": error_code, "error_message": error_message},
        )
        await self.repository.commit()

    async def _execute_stage_operation(
        self,
        job_id: UUID,
        stage_name: str,
        operation,
    ) -> tuple[bool, object | None]:
        try:
            return True, await operation()
        except StageExecutionError as exc:
            logger.warning(
                "Pipeline job %s hit classified stage error in %s: %s",
                job_id,
                stage_name,
                exc.error_code,
            )
            await self._fail_job(
                job_id,
                current_stage=stage_name,
                error_code=exc.error_code,
                error_message=str(exc),
            )
            return False, None
        except Exception as exc:
            logger.exception("Pipeline job %s failed in stage %s", job_id, stage_name)
            await self._fail_job(
                job_id,
                current_stage=stage_name,
                error_code=f"{stage_name}_stage_failed",
                error_message=f"{exc.__class__.__name__}: {exc}",
            )
            return False, None

    async def _load_job_views(self, job_ids: list[str]) -> list[PipelineJobStatusView]:
        job_views: list[PipelineJobStatusView] = []
        for raw_job_id in job_ids:
            try:
                job_view = await self.get_job_status(UUID(raw_job_id))
            except ValueError:
                continue
            job_views.append(job_view)
        return job_views

    def _build_job_status_view(self, job) -> PipelineJobStatusView:
        stage_runs = [
            PipelineStageRunView(
                id=str(stage_run.id),
                stage_name=stage_run.stage_name,
                status=stage_run.status,
                attempt_count=stage_run.attempt_count,
                started_at=stage_run.started_at,
                finished_at=stage_run.finished_at,
                duration_ms=stage_run.duration_ms,
                error_code=stage_run.error_code,
                error_message=stage_run.error_message,
                output_ref=stage_run.output_ref if isinstance(stage_run.output_ref, dict) else {},
                created_at=stage_run.created_at,
            )
            for stage_run in job.stage_runs
        ]
        return PipelineJobStatusView(
            job_id=str(job.id),
            candidate_id=str(job.candidate_id),
            job_type=job.job_type,
            status=job.status,
            current_stage=job.current_stage,
            requested_by=job.requested_by,
            execution_mode=job.execution_mode,
            attempt_count=job.attempt_count,
            error_code=job.error_code,
            error_message=job.error_message,
            queued_at=job.queued_at,
            started_at=job.started_at,
            finished_at=job.finished_at,
            payload_schema_version=job.payload_schema_version,
            stage_runs=stage_runs,
        )
