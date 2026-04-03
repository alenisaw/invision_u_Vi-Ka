from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.modules.auth.schemas import UserResponse
from app.modules.m10_audit.schemas import (
    CandidateOverrideRequest,
    CommitteeDecisionRequest,
    ReviewerActionCreateRequest,
)
from app.modules.m10_audit.service import AuditService


def _make_candidate(
    *,
    status: str = "WAITLIST",
    shortlist_eligible: bool = False,
):
    candidate_id = uuid4()
    return SimpleNamespace(
        id=candidate_id,
        score_record=SimpleNamespace(
            recommendation_status=status,
            shortlist_eligible=shortlist_eligible,
            score_payload={
                "candidate_id": str(candidate_id),
                "recommendation_status": status,
                "manual_review_required": True,
                "review_recommendation": "REQUIRES_MANUAL_REVIEW",
                "shortlist_eligible": shortlist_eligible,
            },
        ),
        explanation_record=SimpleNamespace(
            report_payload={
                "candidate_id": str(candidate_id),
                "recommendation_status": status,
                "manual_review_required": True,
                "review_recommendation": "REQUIRES_MANUAL_REVIEW",
            }
        ),
        reviewer_actions=[],
    )


def _make_action(candidate_id, **overrides):
    defaults = {
        "id": uuid4(),
        "candidate_id": candidate_id,
        "reviewer_id": "reviewer-1",
        "action_type": "comment",
        "previous_status": "WAITLIST",
        "new_status": "WAITLIST",
        "comment": "Looks good.",
        "created_at": datetime(2026, 3, 29, 12, 0, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_user(*, role: str, full_name: str, email: str) -> UserResponse:
    now = datetime(2026, 4, 4, 9, 0, tzinfo=timezone.utc)
    return UserResponse(
        id=uuid4(),
        email=email,
        full_name=full_name,
        role=role,
        is_active=True,
        last_login_at=now,
        created_at=now,
    )


@pytest.mark.asyncio
async def test_override_updates_score_and_explanation_and_writes_audit_trail() -> None:
    service = AuditService(MagicMock())
    service.repository = AsyncMock()

    candidate = _make_candidate(status="WAITLIST", shortlist_eligible=False)
    action = _make_action(
        candidate.id,
        action_type="override",
        previous_status="WAITLIST",
        new_status="RECOMMEND",
        comment="Manual review clears the essay flag.",
    )
    service.repository.get_candidate_with_related.return_value = candidate
    service.repository.create_reviewer_action.return_value = action

    response = await service.override_candidate_decision(
        candidate.id,
        CandidateOverrideRequest(
            reviewer_id="reviewer-1",
            new_status="RECOMMEND",
            comment="Manual review clears the essay flag.",
        ),
    )

    persisted_score = service.repository.upsert_candidate_score.await_args.kwargs
    assert persisted_score["recommendation_status"] == "RECOMMEND"
    assert persisted_score["manual_review_required"] is False
    assert persisted_score["review_recommendation"] == "STANDARD_REVIEW"
    assert persisted_score["score_payload"]["recommendation_status"] == "RECOMMEND"
    assert persisted_score["score_payload"]["shortlist_eligible"] is True

    persisted_explanation = service.repository.upsert_candidate_explanation.await_args.kwargs
    assert persisted_explanation["recommendation_status"] == "RECOMMEND"
    assert persisted_explanation["report_payload"]["review_recommendation"] == "STANDARD_REVIEW"

    audit_entry = service.repository.create_audit_log.await_args.kwargs
    assert audit_entry["action"] == "override"
    assert audit_entry["actor"] == "reviewer-1"
    assert audit_entry["details"]["new_status"] == "RECOMMEND"
    assert audit_entry["details"]["shortlist_eligible"] is True
    service.repository.commit.assert_awaited_once()

    assert response.action_type == "override"
    assert response.new_status == "RECOMMEND"


@pytest.mark.asyncio
async def test_create_shortlist_action_updates_shortlist_flag() -> None:
    service = AuditService(MagicMock())
    service.repository = AsyncMock()

    candidate = _make_candidate(status="RECOMMEND", shortlist_eligible=False)
    action = _make_action(
        candidate.id,
        action_type="shortlist_add",
        previous_status="RECOMMEND",
        new_status="RECOMMEND",
        comment="Add to shortlist after committee sync.",
    )
    service.repository.get_candidate_with_related.return_value = candidate
    service.repository.create_reviewer_action.return_value = action

    response = await service.create_reviewer_action(
        candidate.id,
        ReviewerActionCreateRequest(
            reviewer_id="reviewer-2",
            action_type="shortlist_add",
            comment="Add to shortlist after committee sync.",
        ),
    )

    persisted_score = service.repository.upsert_candidate_score.await_args.kwargs
    assert persisted_score["shortlist_eligible"] is True
    assert persisted_score["score_payload"]["shortlist_eligible"] is True

    audit_entry = service.repository.create_audit_log.await_args.kwargs
    assert audit_entry["action"] == "shortlist_add"
    assert audit_entry["details"]["shortlist_eligible"] is True
    service.repository.commit.assert_awaited_once()

    assert response.action_type == "shortlist_add"
    assert response.reviewer_id == "reviewer-1"


@pytest.mark.asyncio
async def test_list_reviewer_actions_returns_newest_first() -> None:
    service = AuditService(MagicMock())
    service.repository = AsyncMock()

    candidate = _make_candidate(status="RECOMMEND", shortlist_eligible=True)
    older = _make_action(
        candidate.id,
        created_at=datetime(2026, 3, 29, 10, 0, tzinfo=timezone.utc),
        comment="Older note.",
    )
    newer = _make_action(
        candidate.id,
        created_at=datetime(2026, 3, 29, 13, 0, tzinfo=timezone.utc),
        comment="Newer note.",
    )
    candidate.reviewer_actions = [older, newer]
    service.repository.get_candidate_with_related.return_value = candidate

    actions = await service.list_reviewer_actions(candidate.id)

    assert [item.comment for item in actions] == ["Newer note.", "Older note."]


@pytest.mark.asyncio
async def test_list_audit_feed_flattens_audit_log_details() -> None:
    service = AuditService(MagicMock())
    service.repository = AsyncMock()

    candidate_id = uuid4()
    service.repository.list_audit_logs.return_value = [
        SimpleNamespace(
            id=uuid4(),
            entity_type="candidate",
            entity_id=candidate_id,
            action="override",
            actor="reviewer-1",
            details={
                "reviewer_id": "reviewer-1",
                "previous_status": "WAITLIST",
                "new_status": "RECOMMEND",
                "comment": "Manual review complete.",
            },
            created_at=datetime(2026, 3, 29, 14, 0, tzinfo=timezone.utc),
        )
    ]

    feed = await service.list_audit_feed(limit=10)

    assert len(feed) == 1
    assert feed[0].candidate_id == candidate_id
    assert feed[0].action_type == "override"
    assert feed[0].reviewer_id == "reviewer-1"
    assert feed[0].new_status == "RECOMMEND"


@pytest.mark.asyncio
async def test_reviewer_committee_recommendation_is_recorded_without_overwriting_final_score() -> None:
    service = AuditService(MagicMock())
    service.repository = AsyncMock()

    candidate = _make_candidate(status="WAITLIST", shortlist_eligible=False)
    action = _make_action(
        candidate.id,
        reviewer_id="Miras Reviewer",
        action_type="recommendation",
        previous_status="WAITLIST",
        new_status="RECOMMEND",
        comment="Strong motivation and a coherent program fit.",
    )
    service.repository.get_candidate_with_related.return_value = candidate
    service.repository.create_reviewer_action.return_value = action

    response = await service.submit_committee_decision(
        candidate.id,
        actor=_make_user(role="reviewer", full_name="Miras Reviewer", email="reviewer@invisionu.local"),
        payload=CommitteeDecisionRequest(
            new_status="RECOMMEND",
            comment="Strong motivation and a coherent program fit.",
        ),
    )

    service.repository.upsert_candidate_score.assert_not_awaited()
    service.repository.upsert_candidate_explanation.assert_not_awaited()
    audit_entry = service.repository.create_audit_log.await_args.kwargs
    assert audit_entry["action"] == "recommendation"
    assert audit_entry["details"]["role"] == "reviewer"
    assert response.action_type == "recommendation"
    assert response.reviewer_id == "Miras Reviewer"


@pytest.mark.asyncio
async def test_chair_committee_decision_updates_final_score() -> None:
    service = AuditService(MagicMock())
    service.repository = AsyncMock()

    candidate = _make_candidate(status="WAITLIST", shortlist_eligible=False)
    action = _make_action(
        candidate.id,
        reviewer_id="Dana Chair",
        action_type="chair_decision",
        previous_status="WAITLIST",
        new_status="STRONG_RECOMMEND",
        comment="The committee recommendation is approved for admission priority.",
    )
    service.repository.get_candidate_with_related.return_value = candidate
    service.repository.create_reviewer_action.return_value = action

    response = await service.submit_committee_decision(
        candidate.id,
        actor=_make_user(role="chair", full_name="Dana Chair", email="chair@invisionu.local"),
        payload=CommitteeDecisionRequest(
            new_status="STRONG_RECOMMEND",
            comment="The committee recommendation is approved for admission priority.",
        ),
    )

    persisted_score = service.repository.upsert_candidate_score.await_args.kwargs
    assert persisted_score["recommendation_status"] == "STRONG_RECOMMEND"
    assert persisted_score["shortlist_eligible"] is True

    persisted_explanation = service.repository.upsert_candidate_explanation.await_args.kwargs
    assert persisted_explanation["recommendation_status"] == "STRONG_RECOMMEND"

    audit_entry = service.repository.create_audit_log.await_args.kwargs
    assert audit_entry["action"] == "chair_decision"
    assert audit_entry["details"]["role"] == "chair"
    assert response.action_type == "chair_decision"
