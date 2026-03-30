from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import AUDIT_SIGNATURE_VERSION, build_audit_event_hash
from app.core.config import get_settings
from app.modules.m9_storage.models import (
    AuditLog,
    Candidate,
    CandidateExplanation,
    CandidateMetadata,
    CandidateModelInput,
    CandidatePII,
    CandidateScore,
    NLPSignal,
    PipelineJob,
    PipelineJobEvent,
    PipelineStageRun,
    Program,
    ReviewerAction,
)


ModelT = TypeVar("ModelT")


class StorageRepository(Generic[ModelT]):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    async def flush(self) -> None:
        await self.session.flush()

    async def create_candidate(
        self,
        *,
        selected_program: str | None = None,
        pipeline_status: str = "pending",
        intake_id: UUID | None = None,
        dedupe_key: str | None = None,
    ) -> Candidate:
        candidate = Candidate(
            selected_program=selected_program,
            pipeline_status=pipeline_status,
            dedupe_key=dedupe_key,
        )
        if intake_id is not None:
            candidate.intake_id = intake_id

        self.session.add(candidate)
        await self.session.flush()
        await self.session.refresh(candidate)
        return candidate

    async def get_candidate(self, candidate_id: UUID) -> Candidate | None:
        stmt = select(Candidate).where(Candidate.id == candidate_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_candidate_by_dedupe_key(self, dedupe_key: str) -> Candidate | None:
        stmt = select(Candidate).where(Candidate.dedupe_key == dedupe_key)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_candidate_with_related(self, candidate_id: UUID) -> Candidate | None:
        stmt = (
            select(Candidate)
            .where(Candidate.id == candidate_id)
            .options(
                selectinload(Candidate.pii_record),
                selectinload(Candidate.metadata_record),
                selectinload(Candidate.model_input_record),
                selectinload(Candidate.nlp_signal_record),
                selectinload(Candidate.score_record),
                selectinload(Candidate.explanation_record),
                selectinload(Candidate.reviewer_actions),
                selectinload(Candidate.pipeline_jobs),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_candidates(self, limit: int | None = None) -> list[Candidate]:
        stmt = select(Candidate).order_by(Candidate.created_at.desc())
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_pipeline_status(self, candidate_id: UUID, status: str) -> Candidate | None:
        candidate = await self.get_candidate(candidate_id)
        if candidate is None:
            return None

        candidate.pipeline_status = status
        await self.session.flush()
        await self.session.refresh(candidate)
        return candidate

    async def create_pipeline_job(
        self,
        *,
        candidate_id: UUID,
        job_type: str = "candidate_submission",
        status: str = "queued",
        current_stage: str | None = None,
        execution_mode: str = "async",
        requested_by: str = "system",
        attempt_count: int = 0,
        payload_schema_version: str | None = None,
        payload_encrypted: bytes | None = None,
    ) -> PipelineJob:
        job = PipelineJob(
            candidate_id=candidate_id,
            job_type=job_type,
            status=status,
            current_stage=current_stage,
            execution_mode=execution_mode,
            requested_by=requested_by,
            attempt_count=attempt_count,
            payload_schema_version=payload_schema_version,
            payload_encrypted=payload_encrypted,
        )
        self.session.add(job)
        await self.session.flush()
        await self.session.refresh(job)
        return job

    async def get_pipeline_job(self, job_id: UUID) -> PipelineJob | None:
        stmt = select(PipelineJob).where(PipelineJob.id == job_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_pipeline_job_with_related(self, job_id: UUID) -> PipelineJob | None:
        stmt = (
            select(PipelineJob)
            .where(PipelineJob.id == job_id)
            .options(
                selectinload(PipelineJob.stage_runs),
                selectinload(PipelineJob.events),
                selectinload(PipelineJob.candidate),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_pipeline_job_for_candidate(
        self,
        candidate_id: UUID,
    ) -> PipelineJob | None:
        stmt = (
            select(PipelineJob)
            .where(PipelineJob.candidate_id == candidate_id)
            .options(
                selectinload(PipelineJob.stage_runs),
                selectinload(PipelineJob.events),
            )
            .order_by(PipelineJob.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_pipeline_job(
        self,
        job_id: UUID,
        **values: Any,
    ) -> PipelineJob | None:
        job = await self.get_pipeline_job(job_id)
        if job is None:
            return None

        for field_name, value in values.items():
            setattr(job, field_name, value)

        await self.session.flush()
        await self.session.refresh(job)
        return job

    async def create_pipeline_stage_run(
        self,
        *,
        job_id: UUID,
        stage_name: str,
        status: str = "queued",
        attempt_count: int = 0,
        started_at: Any | None = None,
        finished_at: Any | None = None,
        duration_ms: int | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        output_ref: dict[str, Any] | None = None,
    ) -> PipelineStageRun:
        stage_run = PipelineStageRun(
            job_id=job_id,
            stage_name=stage_name,
            status=status,
            attempt_count=attempt_count,
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
            error_code=error_code,
            error_message=error_message,
            output_ref=output_ref or {},
        )
        self.session.add(stage_run)
        await self.session.flush()
        await self.session.refresh(stage_run)
        return stage_run

    async def get_pipeline_stage_run(
        self,
        job_id: UUID,
        stage_name: str,
    ) -> PipelineStageRun | None:
        stmt = select(PipelineStageRun).where(
            PipelineStageRun.job_id == job_id,
            PipelineStageRun.stage_name == stage_name,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_pipeline_stage_run(
        self,
        job_id: UUID,
        stage_name: str,
        **values: Any,
    ) -> PipelineStageRun | None:
        stage_run = await self.get_pipeline_stage_run(job_id, stage_name)
        if stage_run is None:
            return None

        for field_name, value in values.items():
            setattr(stage_run, field_name, value)

        await self.session.flush()
        await self.session.refresh(stage_run)
        return stage_run

    async def list_pipeline_stage_runs(self, job_id: UUID) -> list[PipelineStageRun]:
        stmt = (
            select(PipelineStageRun)
            .where(PipelineStageRun.job_id == job_id)
            .order_by(PipelineStageRun.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_pipeline_job_event(
        self,
        *,
        job_id: UUID,
        event_type: str,
        stage_name: str | None = None,
        status: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> PipelineJobEvent:
        event = PipelineJobEvent(
            job_id=job_id,
            event_type=event_type,
            stage_name=stage_name,
            status=status,
            payload=payload or {},
        )
        self.session.add(event)
        await self.session.flush()
        await self.session.refresh(event)
        return event

    async def list_pipeline_job_events(self, job_id: UUID) -> list[PipelineJobEvent]:
        stmt = (
            select(PipelineJobEvent)
            .where(PipelineJobEvent.job_id == job_id)
            .order_by(PipelineJobEvent.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_pipeline_jobs_by_status(self) -> dict[str, int]:
        stmt = select(PipelineJob.status, func.count(PipelineJob.id)).group_by(PipelineJob.status)
        result = await self.session.execute(stmt)
        return {str(status): int(count) for status, count in result.all()}

    async def count_pipeline_jobs_by_stage(self) -> list[dict[str, object]]:
        stmt = (
            select(
                PipelineJob.current_stage,
                PipelineJob.status,
                func.count(PipelineJob.id),
            )
            .group_by(PipelineJob.current_stage, PipelineJob.status)
            .order_by(PipelineJob.current_stage.asc(), PipelineJob.status.asc())
        )
        result = await self.session.execute(stmt)
        return [
            {
                "current_stage": None if current_stage is None else str(current_stage),
                "status": str(status),
                "count": int(count),
            }
            for current_stage, status, count in result.all()
        ]

    async def get_pipeline_stage_metrics(self) -> list[dict[str, object]]:
        stmt = select(PipelineStageRun).order_by(PipelineStageRun.stage_name.asc())
        result = await self.session.execute(stmt)
        stage_runs = list(result.scalars().all())
        grouped: dict[str, list[PipelineStageRun]] = {}
        for stage_run in stage_runs:
            grouped.setdefault(str(stage_run.stage_name), []).append(stage_run)

        metrics: list[dict[str, object]] = []
        for stage_name in sorted(grouped):
            runs = grouped[stage_name]
            total_runs = len(runs)
            completed_runs = sum(1 for run in runs if run.status == "completed")
            failed_runs = sum(1 for run in runs if run.status == "failed")
            manual_review_runs = sum(
                1 for run in runs if run.status == "requires_manual_review"
            )
            running_runs = sum(1 for run in runs if run.status == "running")
            queued_runs = sum(1 for run in runs if run.status == "queued")
            retry_scheduled_runs = sum(
                1 for run in runs if run.status == "retry_scheduled"
            )
            retry_observations = sum(max(0, int(run.attempt_count) - 1) for run in runs)
            durations = sorted(
                int(run.duration_ms)
                for run in runs
                if run.duration_ms is not None and run.duration_ms >= 0
            )
            avg_duration_ms = (
                None
                if not durations
                else round(sum(durations) / len(durations), 2)
            )
            p95_duration_ms = None
            if durations:
                percentile_index = max(0, int(round((len(durations) - 1) * 0.95)))
                p95_duration_ms = durations[percentile_index]

            metrics.append(
                {
                    "stage_name": stage_name,
                    "total_runs": total_runs,
                    "completed_runs": completed_runs,
                    "failed_runs": failed_runs,
                    "manual_review_runs": manual_review_runs,
                    "running_runs": running_runs,
                    "queued_runs": queued_runs,
                    "retry_scheduled_runs": retry_scheduled_runs,
                    "retry_observations": retry_observations,
                    "failure_rate": 0.0
                    if total_runs == 0
                    else round(failed_runs / total_runs, 4),
                    "manual_review_rate": 0.0
                    if total_runs == 0
                    else round(manual_review_runs / total_runs, 4),
                    "avg_duration_ms": avg_duration_ms,
                    "p95_duration_ms": p95_duration_ms,
                    "max_duration_ms": None if not durations else durations[-1],
                }
            )
        return metrics

    async def upsert_candidate_pii(self, candidate_id: UUID, encrypted_data: bytes) -> CandidatePII:
        return await self._upsert_singleton(
            CandidatePII,
            candidate_id,
            encrypted_data=encrypted_data,
        )

    async def upsert_candidate_metadata(
        self,
        candidate_id: UUID,
        **values: Any,
    ) -> CandidateMetadata:
        return await self._upsert_singleton(CandidateMetadata, candidate_id, **values)

    async def upsert_candidate_model_input(
        self,
        candidate_id: UUID,
        **values: Any,
    ) -> CandidateModelInput:
        return await self._upsert_singleton(CandidateModelInput, candidate_id, **values)

    async def upsert_nlp_signals(self, candidate_id: UUID, **values: Any) -> NLPSignal:
        return await self._upsert_singleton(NLPSignal, candidate_id, **values)

    async def upsert_candidate_score(
        self,
        candidate_id: UUID,
        **values: Any,
    ) -> CandidateScore:
        return await self._upsert_singleton(CandidateScore, candidate_id, **values)

    async def upsert_candidate_explanation(
        self,
        candidate_id: UUID,
        **values: Any,
    ) -> CandidateExplanation:
        return await self._upsert_singleton(CandidateExplanation, candidate_id, **values)

    async def get_candidate_score(self, candidate_id: UUID) -> CandidateScore | None:
        stmt = select(CandidateScore).where(CandidateScore.candidate_id == candidate_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_ranked_scores(self) -> list[CandidateScore]:
        stmt = (
            select(CandidateScore)
            .options(
                selectinload(CandidateScore.candidate).selectinload(Candidate.pii_record),
                selectinload(CandidateScore.candidate).selectinload(
                    Candidate.explanation_record
                ),
            )
            .order_by(
                CandidateScore.ranking_position.asc().nullslast(),
                CandidateScore.review_priority_index.desc().nullslast(),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_candidate_explanation(self, candidate_id: UUID) -> CandidateExplanation | None:
        stmt = select(CandidateExplanation).where(
            CandidateExplanation.candidate_id == candidate_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_reviewer_action(
        self,
        *,
        candidate_id: UUID,
        reviewer_id: str,
        action_type: str,
        previous_status: str | None = None,
        new_status: str | None = None,
        comment: str | None = None,
    ) -> ReviewerAction:
        action = ReviewerAction(
            candidate_id=candidate_id,
            reviewer_id=reviewer_id,
            action_type=action_type,
            previous_status=previous_status,
            new_status=new_status,
            comment=comment,
        )
        self.session.add(action)
        await self.session.flush()
        await self.session.refresh(action)
        return action

    async def create_audit_log(
        self,
        *,
        entity_type: str,
        action: str,
        actor: str,
        entity_id: UUID | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        latest_audit_log = await self.get_latest_signed_audit_log()
        created_at = datetime.now(timezone.utc)
        sequence_no = 1 if latest_audit_log is None or latest_audit_log.sequence_no is None else latest_audit_log.sequence_no + 1
        prev_hash = None if latest_audit_log is None else latest_audit_log.event_hash
        event_hash = build_audit_event_hash(
            secret=get_settings().effective_audit_signing_key,
            sequence_no=sequence_no,
            prev_hash=prev_hash,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor=actor,
            details=details or {},
            created_at=created_at,
        )
        audit_log = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor=actor,
            details=details or {},
            sequence_no=sequence_no,
            prev_hash=prev_hash,
            event_hash=event_hash,
            signature_version=AUDIT_SIGNATURE_VERSION,
            created_at=created_at,
        )
        self.session.add(audit_log)
        await self.session.flush()
        await self.session.refresh(audit_log)
        return audit_log

    async def list_audit_logs(self, limit: int = 100) -> list[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_signed_audit_log(self) -> AuditLog | None:
        stmt = (
            select(AuditLog)
            .where(AuditLog.sequence_no.is_not(None))
            .order_by(AuditLog.sequence_no.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_signed_audit_logs(self, limit: int = 1000) -> list[AuditLog]:
        stmt = (
            select(AuditLog)
            .where(AuditLog.sequence_no.is_not(None))
            .order_by(AuditLog.sequence_no.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def refresh_score_rankings(self) -> None:
        stmt = select(CandidateScore).order_by(
            CandidateScore.review_priority_index.desc().nullslast(),
            CandidateScore.created_at.asc(),
        )
        result = await self.session.execute(stmt)
        ranked_scores = list(result.scalars().all())

        for position, score in enumerate(ranked_scores, start=1):
            score.ranking_position = position

        await self.session.flush()

    async def create_program(
        self,
        *,
        name: str,
        description: str | None = None,
        key_competencies: list[str] | None = None,
    ) -> Program:
        program = Program(
            name=name,
            description=description,
            key_competencies=key_competencies or [],
        )
        self.session.add(program)
        await self.session.flush()
        await self.session.refresh(program)
        return program

    async def list_programs(self) -> list[Program]:
        stmt = select(Program).order_by(Program.name.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def _upsert_singleton(
        self,
        model: type[ModelT],
        candidate_id: UUID,
        **values: Any,
    ) -> ModelT:
        stmt = select(model).where(model.candidate_id == candidate_id)  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        instance = result.scalar_one_or_none()

        if instance is None:
            instance = model(candidate_id=candidate_id, **values)  # type: ignore[call-arg]
            self.session.add(instance)
        else:
            for field_name, value in values.items():
                setattr(instance, field_name, value)

        await self.session.flush()
        await self.session.refresh(instance)
        return instance
