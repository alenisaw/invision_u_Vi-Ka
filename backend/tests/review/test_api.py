from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.dependencies import get_current_user, get_db
from app.main import app
from app.modules.auth.schemas import UserResponse
from app.modules.review.schemas import AuditFeedItemResponse


async def _override_get_db():
    yield object()


def _make_user(role: str = "admin") -> UserResponse:
    now = datetime(2026, 4, 4, 12, 0, tzinfo=timezone.utc)
    return UserResponse(
        id=uuid4(),
        email=f"{role}@invisionu.local",
        full_name=f"{role.title()} User",
        role=role,  # type: ignore[arg-type]
        is_active=True,
        last_login_at=now,
        created_at=now,
    )


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = _override_get_db
    with patch("app.main.AuthService.bootstrap_admin_user", new=AsyncMock(return_value=None)):
        with TestClient(app) as test_client:
            yield test_client
    app.dependency_overrides.clear()


def test_audit_feed_route_returns_entries_for_admin(client: TestClient) -> None:
    current_user = _make_user("admin")
    app.dependency_overrides[get_current_user] = lambda: current_user
    candidate_id = uuid4()
    entries = [
        AuditFeedItemResponse(
            id=uuid4(),
            entity_type="candidate",
            entity_id=candidate_id,
            candidate_id=candidate_id,
            action_type="chair_decision",
            actor="chair@invisionu.local",
            reviewer_user_id=current_user.id,
            reviewer_name="Dana Chair",
            previous_status="WAITLIST",
            new_status="RECOMMEND",
            comment="Approved after committee review.",
            details={"source": "committee"},
            created_at=datetime(2026, 3, 29, 17, 0, tzinfo=timezone.utc),
        )
    ]

    with patch(
        "app.modules.review.router.AuditService.list_audit_feed",
        new=AsyncMock(return_value=entries),
    ):
        response = client.get("/api/v1/audit/feed?limit=50")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"][0]["action_type"] == "chair_decision"
    assert body["data"][0]["reviewer_name"] == "Dana Chair"


def test_audit_feed_route_forbids_non_admin(client: TestClient) -> None:
    app.dependency_overrides[get_current_user] = lambda: _make_user("reviewer")

    response = client.get("/api/v1/audit/feed")

    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "FORBIDDEN"
