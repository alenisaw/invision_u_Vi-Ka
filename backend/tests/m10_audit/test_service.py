from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.modules.auth.schemas import UserResponse
from app.modules.m10_audit.schemas import CommitteeDecisionRequest
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
        "reviewer_id": str(uuid4()),
        "reviewer_user_id": None,
        "reviewer_name": "Committee User",
        "action_type": "recommendation",
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
        role=role,  # type: ignore[arg-type]
        is_active=True,
        last_login_at=now,
        created_at=now,
    )


@pytest.mark.asyncio
async def test_reviewer_committee_recommendation_uses_session_identity() -> None:
    service = AuditService(MagicMock())
    service.repository = AsyncMock()

    reviewer = _make_user(role="reviewer", full_name="Miras Reviewer", email="reviewer@invisionu.local")
    candidate = _make_candidate(status="WAITLIST", shortlist_eligible=False)
    action = _make_action(
        candidate.id,
        reviewer_id=str(reviewer.id),
        reviewer_user_id=reviewer.id,
        reviewer_name=reviewer.full_name,
        action_type="recommendation",
        new_status="RECOMMEND",
        comment="Strong motivation and coherent program fit.",
    )
    service.repository.get_candidate_with_related.return_value = candidate
    service.repository.create_reviewer_action.return_value = action

    response = await service.submit_committee_decision(
        candidate.id,
        actor=reviewer,
        payload=CommitteeDecisionRequest(
            new_status="RECOMMEND",
            comment="Strong motivation and coherent program fit.",
        ),
    )

    service.repository.upsert_candidate_score.assert_not_awaited()
    audit_entry = service.repository.create_audit_log.await_args.kwargs
    assert audit_entry["details"]["reviewer_user_id"] == str(reviewer.id)
    assert audit_entry["details"]["reviewer_name"] == reviewer.full_name
    assert response.reviewer_user_id == reviewer.id
    assert response.reviewer_name == reviewer.full_name


@pytest.mark.asyncio
async def test_chair_decision_updates_score_and_explanation() -> None:
    service = AuditService(MagicMock())
    service.repository = AsyncMock()

    chair = _make_user(role="chair", full_name="Dana Chair", email="chair@invisionu.local")
    candidate = _make_candidate(status="WAITLIST", shortlist_eligible=False)
    action = _make_action(
        candidate.id,
        reviewer_id=str(chair.id),
        reviewer_user_id=chair.id,
        reviewer_name=chair.full_name,
        action_type="chair_decision",
        new_status="RECOMMEND",
        comment="Approved after full committee review.",
    )
    service.repository.get_candidate_with_related.return_value = candidate
    service.repository.create_reviewer_action.return_value = action

    response = await service.submit_committee_decision(
        candidate.id,
        actor=chair,
        payload=CommitteeDecisionRequest(
            new_status="RECOMMEND",
            comment="Approved after full committee review.",
        ),
    )

    persisted_score = service.repository.upsert_candidate_score.await_args.kwargs
    assert persisted_score["recommendation_status"] == "RECOMMEND"
    persisted_explanation = service.repository.upsert_candidate_explanation.await_args.kwargs
    assert persisted_explanation["recommendation_status"] == "RECOMMEND"
    assert response.action_type == "chair_decision"
    assert response.reviewer_name == chair.full_name


@pytest.mark.asyncio
async def test_record_candidate_view_deduplicates_by_user_id() -> None:
    service = AuditService(MagicMock())
    service.repository = AsyncMock()

    reviewer = _make_user(role="reviewer", full_name="Miras Reviewer", email="reviewer@invisionu.local")
    existing_view = _make_action(
        uuid4(),
        reviewer_id=str(reviewer.id),
        reviewer_user_id=reviewer.id,
        reviewer_name=reviewer.full_name,
        action_type="viewed",
    )
    candidate = _make_candidate()
    candidate.reviewer_actions = [existing_view]
    service.repository.get_candidate_with_related.return_value = candidate

    response = await service.record_candidate_view(candidate.id, actor=reviewer)

    service.repository.create_reviewer_action.assert_not_awaited()
    assert response.action_type == "viewed"
    assert response.reviewer_user_id == reviewer.id


@pytest.mark.asyncio
async def test_list_audit_feed_flattens_new_identity_fields() -> None:
    service = AuditService(MagicMock())
    service.repository = AsyncMock()

    reviewer_id = uuid4()
    candidate_id = uuid4()
    service.repository.list_audit_logs.return_value = [
        SimpleNamespace(
            id=uuid4(),
            entity_type="candidate",
            entity_id=candidate_id,
            action="recommendation",
            actor="reviewer@invisionu.local",
            details={
                "reviewer_user_id": str(reviewer_id),
                "reviewer_name": "Miras Reviewer",
                "previous_status": "WAITLIST",
                "new_status": "RECOMMEND",
                "comment": "Good fit.",
            },
            created_at=datetime(2026, 3, 29, 14, 0, tzinfo=timezone.utc),
        )
    ]

    feed = await service.list_audit_feed(limit=10)

    assert len(feed) == 1
    assert feed[0].candidate_id == candidate_id
    assert feed[0].reviewer_user_id == reviewer_id
    assert feed[0].reviewer_name == "Miras Reviewer"
