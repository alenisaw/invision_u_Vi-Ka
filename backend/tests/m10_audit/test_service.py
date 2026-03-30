from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.audit import build_audit_event_hash
from app.modules.m10_audit.schemas import ReviewerActionCreateRequest
from app.modules.m10_audit.service import AuditService


@pytest.mark.asyncio
async def test_create_reviewer_action_uses_server_side_identity() -> None:
    candidate_id = uuid4()
    score_record = MagicMock(
        recommendation_status="WAITLIST",
        shortlist_eligible=False,
        score_payload={},
    )
    candidate = MagicMock(
        id=candidate_id,
        score_record=score_record,
        reviewer_actions=[],
    )
    action = MagicMock(
        id=uuid4(),
        candidate_id=candidate_id,
        reviewer_id="reviewer.alina",
        action_type="comment",
        previous_status="WAITLIST",
        new_status="WAITLIST",
        comment="Needs closer review.",
        created_at=datetime.now(timezone.utc),
    )

    service = AuditService(MagicMock())
    service.repository = AsyncMock()
    service.repository.get_candidate_with_related.return_value = candidate
    service.repository.create_reviewer_action.return_value = action

    payload = ReviewerActionCreateRequest(
        action_type="comment",
        comment="Needs closer review.",
    )
    response = await service.create_reviewer_action(
        candidate_id,
        payload,
        "reviewer.alina",
    )

    assert response.reviewer_id == "reviewer.alina"
    service.repository.create_reviewer_action.assert_awaited_once()
    kwargs = service.repository.create_reviewer_action.await_args.kwargs
    assert kwargs["reviewer_id"] == "reviewer.alina"


@pytest.mark.asyncio
async def test_verify_audit_chain_succeeds_for_signed_logs() -> None:
    service = AuditService(MagicMock())
    service.repository = AsyncMock()
    created_at = datetime.now(timezone.utc)
    first_id = uuid4()
    second_id = uuid4()

    first_hash = build_audit_event_hash(
        secret="very-secure-pii-encryption-secret-123456",
        sequence_no=1,
        prev_hash=None,
        entity_type="candidate",
        entity_id=first_id,
        action="candidate_intake_received",
        actor="system",
        details={"candidate_id": str(first_id)},
        created_at=created_at,
    )
    second_hash = build_audit_event_hash(
        secret="very-secure-pii-encryption-secret-123456",
        sequence_no=2,
        prev_hash=first_hash,
        entity_type="candidate",
        entity_id=second_id,
        action="override",
        actor="reviewer.alina",
        details={"candidate_id": str(second_id)},
        created_at=created_at,
    )
    service.repository.list_signed_audit_logs.return_value = [
        MagicMock(
            sequence_no=1,
            prev_hash=None,
            event_hash=first_hash,
            entity_type="candidate",
            entity_id=first_id,
            action="candidate_intake_received",
            actor="system",
            details={"candidate_id": str(first_id)},
            created_at=created_at,
        ),
        MagicMock(
            sequence_no=2,
            prev_hash=first_hash,
            event_hash=second_hash,
            entity_type="candidate",
            entity_id=second_id,
            action="override",
            actor="reviewer.alina",
            details={"candidate_id": str(second_id)},
            created_at=created_at,
        ),
    ]

    result = await service.verify_audit_chain(limit=100)

    assert result.verified is True
    assert result.verified_count == 2


@pytest.mark.asyncio
async def test_verify_audit_chain_detects_tampering() -> None:
    service = AuditService(MagicMock())
    service.repository = AsyncMock()
    created_at = datetime.now(timezone.utc)
    candidate_id = uuid4()
    signed_hash = build_audit_event_hash(
        secret="very-secure-pii-encryption-secret-123456",
        sequence_no=1,
        prev_hash=None,
        entity_type="candidate",
        entity_id=candidate_id,
        action="override",
        actor="reviewer.alina",
        details={"candidate_id": str(candidate_id)},
        created_at=created_at,
    )
    service.repository.list_signed_audit_logs.return_value = [
        MagicMock(
            sequence_no=1,
            prev_hash=None,
            event_hash=signed_hash,
            entity_type="candidate",
            entity_id=candidate_id,
            action="override",
            actor="reviewer.alina",
            details={"candidate_id": str(candidate_id), "comment": "tampered"},
            created_at=created_at,
        )
    ]

    result = await service.verify_audit_chain(limit=100)

    assert result.verified is False
    assert result.failed_sequence_no == 1
