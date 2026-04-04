from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.schemas import UserResponse
from app.modules.m10_audit.schemas import (
    AuditFeedItemResponse,
    CommitteeDecisionRequest,
    ReviewerActionResponse,
)
from app.modules.m9_storage import AuditLog, Candidate, ReviewerAction, StorageRepository


class AuditWorkflowError(ValueError):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = StorageRepository(session)

    async def submit_committee_decision(
        self,
        candidate_id: UUID,
        *,
        actor: UserResponse,
        payload: CommitteeDecisionRequest,
    ) -> ReviewerActionResponse:
        candidate = await self._get_candidate_or_raise(candidate_id)

        if actor.role not in {"reviewer", "chair"}:
            raise AuditWorkflowError(
                "Only committee members can submit decisions",
                status_code=403,
            )

        previous_status = self._current_status(candidate)
        reviewer_name = actor.full_name.strip() or actor.email.strip()
        comment = payload.comment.strip()

        if actor.role == "chair":
            if candidate.score_record is None:
                raise AuditWorkflowError(
                    f"Candidate {candidate_id} has no score record",
                    status_code=409,
                )

            updated_score_payload = self._updated_score_payload(
                candidate.score_record.score_payload,
                recommendation_status=payload.new_status,
                manual_review_required=False,
                human_in_loop_required=False,
                review_recommendation="STANDARD_REVIEW",
            )
            await self.repository.upsert_candidate_score(
                candidate_id=candidate_id,
                recommendation_status=payload.new_status,
                manual_review_required=False,
                human_in_loop_required=False,
                review_recommendation="STANDARD_REVIEW",
                score_payload=updated_score_payload,
            )

            if candidate.explanation_record is not None:
                updated_report_payload = self._updated_report_payload(
                    candidate.explanation_record.report_payload,
                    recommendation_status=payload.new_status,
                    manual_review_required=False,
                    human_in_loop_required=False,
                    review_recommendation="STANDARD_REVIEW",
                )
                await self.repository.upsert_candidate_explanation(
                    candidate_id=candidate_id,
                    recommendation_status=payload.new_status,
                    manual_review_required=False,
                    human_in_loop_required=False,
                    review_recommendation="STANDARD_REVIEW",
                    report_payload=updated_report_payload,
                )

            action_type = "chair_decision"
            audit_action = "chair_decision"
        else:
            action_type = "recommendation"
            audit_action = "recommendation"

        action = await self.repository.create_reviewer_action(
            candidate_id=candidate_id,
            reviewer_user_id=actor.id,
            reviewer_name=reviewer_name,
            action_type=action_type,
            previous_status=previous_status,
            new_status=payload.new_status,
            comment=comment,
        )
        await self.repository.create_audit_log(
            entity_type="candidate",
            entity_id=candidate_id,
            action=audit_action,
            actor=actor.email,
            details={
                "reviewer_user_id": str(actor.id),
                "reviewer_name": reviewer_name,
                "previous_status": previous_status,
                "new_status": payload.new_status,
                "comment": comment,
                "role": actor.role,
            },
        )
        await self.repository.commit()
        return self._reviewer_action_response(action)

    async def record_candidate_view(
        self,
        candidate_id: UUID,
        *,
        actor: UserResponse,
    ) -> ReviewerActionResponse:
        candidate = await self._get_candidate_or_raise(candidate_id)

        if actor.role not in {"reviewer", "chair"}:
            raise AuditWorkflowError(
                "Only committee members can record view activity",
                status_code=403,
            )

        reviewer_name = actor.full_name.strip() or actor.email.strip()
        for existing in candidate.reviewer_actions or []:
            if existing.reviewer_user_id == actor.id and existing.action_type == "viewed":
                return self._reviewer_action_response(existing)

        current_status = self._current_status(candidate)
        action = await self.repository.create_reviewer_action(
            candidate_id=candidate_id,
            reviewer_user_id=actor.id,
            reviewer_name=reviewer_name,
            action_type="viewed",
            previous_status=current_status,
            new_status=current_status,
            comment="",
        )
        await self.repository.create_audit_log(
            entity_type="candidate",
            entity_id=candidate_id,
            action="viewed",
            actor=actor.email,
            details={
                "reviewer_user_id": str(actor.id),
                "reviewer_name": reviewer_name,
                "previous_status": current_status,
                "new_status": current_status,
                "role": actor.role,
            },
        )
        await self.repository.commit()
        return self._reviewer_action_response(action)

    async def list_audit_feed(self, limit: int = 100) -> list[AuditFeedItemResponse]:
        logs = await self.repository.list_audit_logs(limit=limit)
        return [self._audit_feed_item(log) for log in logs]

    async def _get_candidate_or_raise(self, candidate_id: UUID) -> Candidate:
        candidate = await self.repository.get_candidate_with_related(candidate_id)
        if candidate is None:
            raise AuditWorkflowError(f"Candidate {candidate_id} not found", status_code=404)
        return candidate

    def _reviewer_action_response(self, action: ReviewerAction) -> ReviewerActionResponse:
        return ReviewerActionResponse(
            id=action.id,
            candidate_id=action.candidate_id,
            reviewer_user_id=action.reviewer_user_id,
            reviewer_name=action.reviewer_name or "Unknown reviewer",
            action_type=action.action_type,
            previous_status=action.previous_status or "",
            new_status=action.new_status or "",
            comment=action.comment or "",
            created_at=action.created_at,
        )

    def _audit_feed_item(self, log: AuditLog) -> AuditFeedItemResponse:
        details = log.details if isinstance(log.details, dict) else {}
        candidate_id = details.get("candidate_id")
        if log.entity_type == "candidate" and log.entity_id is not None:
            candidate_id = log.entity_id

        return AuditFeedItemResponse(
            id=log.id,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            candidate_id=candidate_id,
            action_type=log.action,
            actor=log.actor,
            reviewer_user_id=self._coerce_uuid(details.get("reviewer_user_id")),
            reviewer_name=self._clean_text(details.get("reviewer_name")) or None,
            previous_status=self._clean_text(details.get("previous_status")) or None,
            new_status=self._clean_text(details.get("new_status")) or None,
            comment=self._clean_text(details.get("comment")) or None,
            details=details,
            created_at=log.created_at,
        )

    def _updated_score_payload(
        self,
        score_payload: dict[str, Any] | None,
        **updates: Any,
    ) -> dict[str, Any]:
        payload = dict(score_payload or {})
        payload.update(updates)
        return payload

    def _updated_report_payload(
        self,
        report_payload: dict[str, Any] | None,
        **updates: Any,
    ) -> dict[str, Any]:
        payload = dict(report_payload or {})
        payload.update(updates)
        return payload

    def _current_status(self, candidate: Candidate) -> str:
        if candidate.score_record is None:
            return ""
        return candidate.score_record.recommendation_status or ""

    def _clean_text(self, value: Any) -> str:
        if not isinstance(value, str):
            return ""
        return value.strip()

    def _coerce_uuid(self, value: Any) -> UUID | None:
        if not isinstance(value, str) or not value.strip():
            return None
        try:
            return UUID(value.strip())
        except ValueError:
            return None
