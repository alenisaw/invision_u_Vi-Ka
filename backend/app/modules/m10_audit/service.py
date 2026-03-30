from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.m10_audit.schemas import (
    AuditFeedItemResponse,
    CandidateOverrideRequest,
    ReviewerActionCreateRequest,
    ReviewerActionResponse,
)
from app.modules.m9_storage import AuditLog, Candidate, ReviewerAction, StorageRepository


SHORTLIST_ELIGIBLE_STATUSES = {"STRONG_RECOMMEND", "RECOMMEND"}


class AuditWorkflowError(ValueError):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = StorageRepository(session)

    async def override_candidate_decision(
        self,
        candidate_id: UUID,
        payload: CandidateOverrideRequest,
    ) -> ReviewerActionResponse:
        candidate = await self._get_candidate_or_raise(candidate_id)

        if candidate.score_record is None:
            raise AuditWorkflowError(
                f"Candidate {candidate_id} has no score record",
                status_code=409,
            )

        previous_status = candidate.score_record.recommendation_status or ""
        if previous_status == payload.new_status:
            raise AuditWorkflowError(
                "Override status must differ from the current status",
                status_code=422,
            )

        shortlist_eligible = payload.new_status in SHORTLIST_ELIGIBLE_STATUSES
        updated_score_payload = self._updated_score_payload(
            candidate.score_record.score_payload,
            recommendation_status=payload.new_status,
            manual_review_required=False,
            human_in_loop_required=False,
            review_recommendation="STANDARD_REVIEW",
            shortlist_eligible=shortlist_eligible,
        )
        await self.repository.upsert_candidate_score(
            candidate_id=candidate_id,
            recommendation_status=payload.new_status,
            manual_review_required=False,
            human_in_loop_required=False,
            review_recommendation="STANDARD_REVIEW",
            shortlist_eligible=shortlist_eligible,
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

        action = await self.repository.create_reviewer_action(
            candidate_id=candidate_id,
            reviewer_id=payload.reviewer_id.strip(),
            action_type="override",
            previous_status=previous_status,
            new_status=payload.new_status,
            comment=payload.comment.strip(),
        )
        await self.repository.create_audit_log(
            entity_type="candidate",
            entity_id=candidate_id,
            action="override",
            actor=payload.reviewer_id.strip(),
            details={
                "reviewer_id": payload.reviewer_id.strip(),
                "previous_status": previous_status,
                "new_status": payload.new_status,
                "comment": payload.comment.strip(),
                "shortlist_eligible": shortlist_eligible,
            },
        )
        await self.repository.commit()
        return self._reviewer_action_response(action)

    async def create_reviewer_action(
        self,
        candidate_id: UUID,
        payload: ReviewerActionCreateRequest,
    ) -> ReviewerActionResponse:
        candidate = await self._get_candidate_or_raise(candidate_id)

        previous_status = self._current_status(candidate)
        new_status = previous_status

        if payload.action_type in {"shortlist_add", "shortlist_remove"}:
            if candidate.score_record is None:
                raise AuditWorkflowError(
                    f"Candidate {candidate_id} has no score record",
                    status_code=409,
                )

            shortlist_eligible = payload.action_type == "shortlist_add"
            updated_score_payload = self._updated_score_payload(
                candidate.score_record.score_payload,
                shortlist_eligible=shortlist_eligible,
            )
            await self.repository.upsert_candidate_score(
                candidate_id=candidate_id,
                shortlist_eligible=shortlist_eligible,
                score_payload=updated_score_payload,
            )

        action = await self.repository.create_reviewer_action(
            candidate_id=candidate_id,
            reviewer_id=payload.reviewer_id.strip(),
            action_type=payload.action_type,
            previous_status=previous_status,
            new_status=new_status,
            comment=payload.comment.strip(),
        )
        await self.repository.create_audit_log(
            entity_type="candidate",
            entity_id=candidate_id,
            action=payload.action_type,
            actor=payload.reviewer_id.strip(),
            details={
                "reviewer_id": payload.reviewer_id.strip(),
                "previous_status": previous_status,
                "new_status": new_status,
                "comment": payload.comment.strip(),
                "shortlist_eligible": self._current_shortlist_flag(candidate, payload),
            },
        )
        await self.repository.commit()
        return self._reviewer_action_response(action)

    async def list_reviewer_actions(
        self,
        candidate_id: UUID,
    ) -> list[ReviewerActionResponse]:
        candidate = await self._get_candidate_or_raise(candidate_id)
        actions = sorted(
            candidate.reviewer_actions,
            key=lambda action: action.created_at,
            reverse=True,
        )
        return [self._reviewer_action_response(action) for action in actions]

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
            reviewer_id=action.reviewer_id,
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
            reviewer_id=self._clean_text(details.get("reviewer_id")) or None,
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

    def _current_shortlist_flag(
        self,
        candidate: Candidate,
        payload: ReviewerActionCreateRequest,
    ) -> bool | None:
        if payload.action_type == "shortlist_add":
            return True
        if payload.action_type == "shortlist_remove":
            return False
        if candidate.score_record is None:
            return None
        return bool(candidate.score_record.shortlist_eligible)

    def _clean_text(self, value: Any) -> str:
        if not isinstance(value, str):
            return ""
        return value.strip()
