from __future__ import annotations

from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.m9_storage.models import (
    AuditLog,
    Candidate,
    CandidateExplanation,
    CandidateMetadata,
    CandidateModelInput,
    CandidatePII,
    CandidateScore,
    NLPSignal,
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
        )
        if intake_id is not None:
            candidate.intake_id = intake_id
        if dedupe_key is not None:
            candidate.dedupe_key = dedupe_key

        self.session.add(candidate)
        await self.session.flush()
        await self.session.refresh(candidate)
        return candidate

    async def find_candidate_by_dedupe_key(self, dedupe_key: str) -> Candidate | None:
        stmt = select(Candidate).where(Candidate.dedupe_key == dedupe_key)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_candidate(self, candidate_id: UUID) -> None:
        candidate = await self.get_candidate_with_related(candidate_id)
        if candidate is not None:
            await self.session.delete(candidate)
            await self.session.flush()

    async def get_candidate(self, candidate_id: UUID) -> Candidate | None:
        stmt = select(Candidate).where(Candidate.id == candidate_id)
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

    async def list_candidates_with_related(self, limit: int | None = None) -> list[Candidate]:
        stmt = (
            select(Candidate)
            .options(
                selectinload(Candidate.pii_record),
                selectinload(Candidate.metadata_record),
                selectinload(Candidate.score_record),
                selectinload(Candidate.explanation_record),
            )
            .order_by(Candidate.created_at.desc())
        )
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
        audit_log = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor=actor,
            details=details or {},
        )
        self.session.add(audit_log)
        await self.session.flush()
        await self.session.refresh(audit_log)
        return audit_log

    async def list_audit_logs(self, limit: int = 100) -> list[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
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
