from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.dependencies import get_db
from app.main import app
from app.modules.m8_dashboard.schemas import (
    DashboardCandidateDetailResponse,
    DashboardCandidateListItem,
    DashboardStatsResponse,
)
from app.modules.m6_scoring.schemas import CandidateScore as CandidateScorePayload
from app.modules.m7_explainability.schemas import ExplainabilityReport


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


def test_stats_route_wraps_success_response(
    client: TestClient,
    reviewer_settings,
) -> None:
    stats = DashboardStatsResponse(
        total_candidates=8,
        processed=6,
        shortlisted=2,
        pending_review=1,
        avg_confidence=0.79,
        by_status={
            "STRONG_RECOMMEND": 2,
            "RECOMMEND": 2,
            "WAITLIST": 1,
            "DECLINED": 1,
        },
    )

    with patch(
        "app.modules.m8_dashboard.router.DashboardService.get_stats",
        new=AsyncMock(return_value=stats),
    ):
        response = client.get(
            "/api/v1/dashboard/stats",
            headers={"X-API-Key": "test-reviewer-key"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["processed"] == 6
    assert body["data"]["by_status"]["STRONG_RECOMMEND"] == 2


def test_candidates_route_returns_list_payload(
    client: TestClient,
    reviewer_settings,
) -> None:
    candidate = DashboardCandidateListItem(
        candidate_id=uuid4(),
        name="Aida Kim",
        selected_program="Innovative IT Product Design and Development",
        review_priority_index=0.82,
        recommendation_status="RECOMMEND",
        confidence=0.77,
        shortlist_eligible=True,
        ranking_position=3,
        top_strengths=["Leadership"],
        caution_flags=["Essay mismatch"],
        created_at=datetime(2026, 3, 28, 10, 30, tzinfo=timezone.utc),
    )

    with patch(
        "app.modules.m8_dashboard.router.DashboardService.list_candidates",
        new=AsyncMock(return_value=[candidate]),
    ):
        response = client.get(
            "/api/v1/dashboard/candidates",
            headers={"X-API-Key": "test-reviewer-key"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]) == 1
    assert body["data"][0]["name"] == "Aida Kim"


def test_candidate_detail_route_returns_detail_payload(
    client: TestClient,
    reviewer_settings,
) -> None:
    candidate_id = uuid4()
    detail = DashboardCandidateDetailResponse(
        candidate_id=candidate_id,
        name="Dana Sarsen",
        score=CandidateScorePayload(
            candidate_id=candidate_id,
            selected_program="Innovative IT Product Design and Development",
            program_id="prog-it-design-001",
            sub_scores={"leadership_potential": 0.81},
            review_priority_index=0.8,
            recommendation_status="RECOMMEND",
            decision_summary="Solid overall profile.",
            confidence=0.78,
            shortlist_eligible=True,
        ),
        explanation=ExplainabilityReport(
            candidate_id=candidate_id,
            scoring_version="m6-v1",
            selected_program="Innovative IT Product Design and Development",
            program_id="prog-it-design-001",
            recommendation_status="RECOMMEND",
            review_priority_index=0.8,
            confidence=0.78,
            review_recommendation="STANDARD_REVIEW",
            summary="Promising candidate with some caution blocks.",
            positive_factors=[],
            caution_blocks=[],
            reviewer_guidance="Proceed with standard review.",
            data_quality_notes=[],
        ),
    )

    with patch(
        "app.modules.m8_dashboard.router.DashboardService.get_candidate_detail",
        new=AsyncMock(return_value=detail),
    ):
        response = client.get(
            f"/api/v1/dashboard/candidates/{candidate_id}",
            headers={"X-API-Key": "test-reviewer-key"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["name"] == "Dana Sarsen"
    assert body["data"]["candidate_id"] == str(candidate_id)
    assert body["data"]["score"]["candidate_id"] == str(candidate_id)


def test_candidate_detail_route_returns_404_when_service_raises(
    client: TestClient,
    reviewer_settings,
) -> None:
    candidate_id = uuid4()

    with patch(
        "app.modules.m8_dashboard.router.DashboardService.get_candidate_detail",
        new=AsyncMock(side_effect=ValueError("Candidate not found")),
    ):
        response = client.get(
            f"/api/v1/dashboard/candidates/{candidate_id}",
            headers={"X-API-Key": "test-reviewer-key"},
        )

    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["error"]["message"] == "Candidate not found"


def test_shortlist_route_returns_list_payload(
    client: TestClient,
    reviewer_settings,
) -> None:
    shortlist = [
        DashboardCandidateListItem(
            candidate_id=uuid4(),
            name="Arman Tulep",
            selected_program="Innovative IT Product Design and Development",
            review_priority_index=0.92,
            recommendation_status="STRONG_RECOMMEND",
            confidence=0.88,
            shortlist_eligible=True,
            ranking_position=1,
            top_strengths=["Leadership"],
            caution_flags=[],
            created_at=datetime(2026, 3, 28, 9, 0, tzinfo=timezone.utc),
        )
    ]

    with patch(
        "app.modules.m8_dashboard.router.DashboardService.list_shortlist",
        new=AsyncMock(return_value=shortlist),
    ):
        response = client.get(
            "/api/v1/dashboard/shortlist",
            headers={"X-API-Key": "test-reviewer-key"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"][0]["ranking_position"] == 1


def test_dashboard_routes_require_api_key_header(client: TestClient, reviewer_settings) -> None:
    response = client.get("/api/v1/dashboard/stats")

    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert body["error"]["message"] == "Missing X-API-Key header"


def test_dashboard_routes_reject_invalid_api_key(
    client: TestClient,
    reviewer_settings,
) -> None:
    response = client.get(
        "/api/v1/dashboard/stats",
        headers={"X-API-Key": "wrong-key"},
    )

    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "FORBIDDEN"
    assert body["error"]["message"] == "Invalid API key"


def test_dashboard_routes_fail_closed_when_server_key_missing(client: TestClient) -> None:
    with patch(
        "app.core.dependencies.get_settings",
        return_value=SimpleNamespace(api_key=None),
    ):
        response = client.get(
            "/api/v1/dashboard/stats",
            headers={"X-API-Key": "any-key"},
    )

    assert response.status_code == 503
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert body["error"]["message"] == "Reviewer API key is not configured"
