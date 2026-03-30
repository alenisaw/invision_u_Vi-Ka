from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

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
