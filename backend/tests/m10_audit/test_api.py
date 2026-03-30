from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.dependencies import get_db
from app.main import app
from app.modules.m10_audit.schemas import AuditFeedItemResponse, ReviewerActionResponse
from app.modules.m10_audit.service import AuditWorkflowError


async def _override_get_db():
    yield object()


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def reviewer_settings():
    with patch(
        "app.core.dependencies.get_settings",
        return_value=SimpleNamespace(api_key="test-reviewer-key"),
    ):
        yield


def test_override_route_returns_action_payload(
    client: TestClient,
    reviewer_settings,
) -> None:
    candidate_id = uuid4()
    action = ReviewerActionResponse(
        id=uuid4(),
        candidate_id=candidate_id,
        reviewer_id="reviewer-1",
        action_type="override",
        previous_status="WAITLIST",
        new_status="RECOMMEND",
        comment="Manual review clears the flag.",
        created_at=datetime(2026, 3, 29, 14, 0, tzinfo=timezone.utc),
    )

    with patch(
        "app.modules.m8_dashboard.router.AuditService.override_candidate_decision",
        new=AsyncMock(return_value=action),
    ):
        response = client.post(
            f"/api/v1/dashboard/candidates/{candidate_id}/override",
            headers={"X-API-Key": "test-reviewer-key"},
            json={
                "new_status": "RECOMMEND",
                "comment": "Manual review clears the flag.",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["action_type"] == "override"
    assert body["data"]["new_status"] == "RECOMMEND"


def test_override_route_maps_workflow_errors(
    client: TestClient,
    reviewer_settings,
) -> None:
    candidate_id = uuid4()

    with patch(
        "app.modules.m8_dashboard.router.AuditService.override_candidate_decision",
        new=AsyncMock(
            side_effect=AuditWorkflowError(
                "Override status must differ from the current status",
                status_code=422,
            )
        ),
    ):
        response = client.post(
            f"/api/v1/dashboard/candidates/{candidate_id}/override",
            headers={"X-API-Key": "test-reviewer-key"},
            json={
                "new_status": "WAITLIST",
                "comment": "No-op override.",
            },
        )

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "Override status must differ from the current status"


def test_create_reviewer_action_route_returns_action_payload(
    client: TestClient,
    reviewer_settings,
) -> None:
    candidate_id = uuid4()
    action = ReviewerActionResponse(
        id=uuid4(),
        candidate_id=candidate_id,
        reviewer_id="reviewer-2",
        action_type="shortlist_add",
        previous_status="RECOMMEND",
        new_status="RECOMMEND",
        comment="Add to shortlist.",
        created_at=datetime(2026, 3, 29, 15, 0, tzinfo=timezone.utc),
    )

    with patch(
        "app.modules.m10_audit.router.AuditService.create_reviewer_action",
        new=AsyncMock(return_value=action),
    ):
        response = client.post(
            f"/api/v1/dashboard/candidates/{candidate_id}/actions",
            headers={"X-API-Key": "test-reviewer-key"},
            json={
                "action_type": "shortlist_add",
                "comment": "Add to shortlist.",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["action_type"] == "shortlist_add"


def test_list_reviewer_actions_route_returns_action_list(
    client: TestClient,
    reviewer_settings,
) -> None:
    candidate_id = uuid4()
    actions = [
        ReviewerActionResponse(
            id=uuid4(),
            candidate_id=candidate_id,
            reviewer_id="reviewer-1",
            action_type="comment",
            previous_status="RECOMMEND",
            new_status="RECOMMEND",
            comment="Looks consistent.",
            created_at=datetime(2026, 3, 29, 16, 0, tzinfo=timezone.utc),
        )
    ]

    with patch(
        "app.modules.m10_audit.router.AuditService.list_reviewer_actions",
        new=AsyncMock(return_value=actions),
    ):
        response = client.get(
            f"/api/v1/dashboard/candidates/{candidate_id}/actions",
            headers={"X-API-Key": "test-reviewer-key"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"][0]["comment"] == "Looks consistent."


def test_audit_feed_route_returns_entries(
    client: TestClient,
    reviewer_settings,
) -> None:
    candidate_id = uuid4()
    entries = [
        AuditFeedItemResponse(
            id=uuid4(),
            entity_type="candidate",
            entity_id=candidate_id,
            candidate_id=candidate_id,
            action_type="override",
            actor="reviewer-1",
            reviewer_id="reviewer-1",
            previous_status="WAITLIST",
            new_status="RECOMMEND",
            comment="Manual review complete.",
            details={"source": "manual"},
            created_at=datetime(2026, 3, 29, 17, 0, tzinfo=timezone.utc),
        )
    ]

    with patch(
        "app.modules.m10_audit.router.AuditService.list_audit_feed",
        new=AsyncMock(return_value=entries),
    ):
        response = client.get(
            "/api/v1/audit/feed?limit=50",
            headers={"X-API-Key": "test-reviewer-key"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"][0]["action_type"] == "override"
    assert body["data"][0]["candidate_id"] == str(candidate_id)


def test_audit_feed_route_requires_api_key(client: TestClient, reviewer_settings) -> None:
    response = client.get("/api/v1/audit/feed")

    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert body["error"]["message"] == "Missing X-API-Key header"
