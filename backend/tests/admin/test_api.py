from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.dependencies import get_current_user, get_db
from app.main import app
from app.modules.admin.schemas import (
    PipelineMetricsOverviewResponse,
    PipelineMetricsResponse,
    PipelineRunMetricResponse,
)
from app.modules.auth.schemas import UserResponse


async def _override_get_db():
    yield object()


def _make_user(role: str = "admin") -> UserResponse:
    now = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
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


def test_pipeline_metrics_route_returns_admin_metrics(client: TestClient) -> None:
    app.dependency_overrides[get_current_user] = lambda: _make_user("admin")
    payload = PipelineMetricsResponse(
        overview=PipelineMetricsOverviewResponse(
            total_runs=3,
            healthy_runs=1,
            degraded_runs=1,
            partial_runs=0,
            manual_review_runs=1,
            degraded_rate=0.3333,
            manual_review_rate=0.3333,
            avg_total_latency_ms=640.0,
            p50_total_latency_ms=620.0,
            p95_total_latency_ms=910.0,
            avg_stage_latencies_ms={"scoring": 73.0},
            fallback_counts={"llm_extraction_fallback_used": 1},
            quality_flag_counts={"manual_review_required": 1},
        ),
        recent_runs=[
            PipelineRunMetricResponse(
                audit_id=uuid4(),
                candidate_id=uuid4(),
                recommendation_status="RECOMMEND",
                pipeline_quality_status="healthy",
                quality_flags=[],
                total_latency_ms=420.0,
                stage_latencies_ms={"scoring": 55.0},
                created_at=datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
                details={},
            )
        ],
    )

    with patch(
        "app.modules.admin.router.AdminService.get_pipeline_metrics",
        new=AsyncMock(return_value=payload),
    ):
        response = client.get("/api/v1/admin/metrics/pipeline?limit=50")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["overview"]["total_runs"] == 3
    assert body["data"]["recent_runs"][0]["pipeline_quality_status"] == "healthy"


def test_pipeline_metrics_route_forbids_non_admin(client: TestClient) -> None:
    app.dependency_overrides[get_current_user] = lambda: _make_user("reviewer")

    response = client.get("/api/v1/admin/metrics/pipeline")

    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "FORBIDDEN"
