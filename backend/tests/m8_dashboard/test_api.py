from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.dependencies import get_current_user, get_db
from app.main import app
from app.modules.auth.schemas import UserResponse
from app.modules.m6_scoring.schemas import CandidateScore as CandidateScorePayload
from app.modules.m7_explainability.schemas import ExplainabilityReport
from app.modules.m8_dashboard.schemas import (
    DashboardCandidateDetailResponse,
    DashboardCandidateListItem,
    DashboardStatsResponse,
)


async def _override_get_db():
    yield object()


def _make_user(role: str = "reviewer") -> UserResponse:
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


def test_stats_route_wraps_success_response(client: TestClient) -> None:
    app.dependency_overrides[get_current_user] = lambda: _make_user("reviewer")
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
        response = client.get("/api/v1/dashboard/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["processed"] == 6
    assert body["data"]["by_status"]["STRONG_RECOMMEND"] == 2


def test_candidates_route_returns_list_payload(client: TestClient) -> None:
    app.dependency_overrides[get_current_user] = lambda: _make_user("chair")
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
        response = client.get("/api/v1/dashboard/candidates")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]) == 1
    assert body["data"][0]["name"] == "Aida Kim"


def test_candidate_detail_route_returns_detail_payload(client: TestClient) -> None:
    current_user = _make_user("reviewer")
    app.dependency_overrides[get_current_user] = lambda: current_user
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
        response = client.get(f"/api/v1/dashboard/candidates/{candidate_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["name"] == "Dana Sarsen"
    assert body["data"]["candidate_id"] == str(candidate_id)


def test_dashboard_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/dashboard/stats")

    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"


def test_dashboard_forbids_non_committee_role(client: TestClient) -> None:
    app.dependency_overrides[get_current_user] = lambda: _make_user("admin")

    with patch(
        "app.modules.m8_dashboard.router.DashboardService.get_candidate_detail",
        new=AsyncMock(side_effect=ValueError("Candidate not found")),
    ):
        response = client.post(
            f"/api/v1/dashboard/candidates/{uuid4()}/viewed",
        )

    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "FORBIDDEN"
