"""
API-level tests for demo router endpoints.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.dependencies import get_db


def _override_get_db():
    session = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    yield session


@pytest.fixture(autouse=True)
def _mock_db():
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


class TestListDemoCandidates:
    def test_returns_200(self, client: TestClient) -> None:
        resp = client.get("/api/v1/demo/candidates")
        assert resp.status_code == 200

    def test_response_is_list(self, client: TestClient) -> None:
        resp = client.get("/api/v1/demo/candidates")
        body = resp.json()
        assert body["success"] is True
        assert isinstance(body["data"], list)
        assert len(body["data"]) >= 12

    def test_each_item_has_meta(self, client: TestClient) -> None:
        resp = client.get("/api/v1/demo/candidates")
        for item in resp.json()["data"]:
            assert "meta" in item
            meta = item["meta"]
            assert "slug" in meta
            assert "display_name" in meta
            assert "program" in meta
            assert "program" in meta


class TestGetDemoCandidate:
    def test_valid_slug_returns_200(self, client: TestClient) -> None:
        resp = client.get("/api/v1/demo/candidates/aisha-strong-leader")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["meta"]["slug"] == "aisha-strong-leader"

    def test_detail_has_payload(self, client: TestClient) -> None:
        resp = client.get("/api/v1/demo/candidates/aisha-strong-leader")
        data = resp.json()["data"]
        assert "payload" in data
        assert "personal" in data["payload"]
        assert "_meta" not in data["payload"]

    def test_invalid_slug_returns_404(self, client: TestClient) -> None:
        resp = client.get("/api/v1/demo/candidates/nonexistent-slug")
        assert resp.status_code == 404


class TestRunDemoCandidate:
    def test_invalid_slug_returns_404(self, client: TestClient) -> None:
        resp = client.post("/api/v1/demo/candidates/nonexistent-slug/run")
        assert resp.status_code == 404

    @patch("app.modules.m1_gateway.orchestrator.PipelineOrchestrator.submit_async")
    def test_valid_slug_calls_pipeline(self, mock_submit_async: MagicMock, client: TestClient) -> None:
        fake_result = MagicMock()
        fake_result.model_dump.return_value = {
            "candidate_id": "test-id-123",
            "job_id": "job-id-456",
            "pipeline_status": "queued",
            "job_status": "queued",
            "current_stage": "privacy",
            "message": "Candidate accepted and queued for asynchronous processing.",
        }
        mock_submit_async.return_value = fake_result

        resp = client.post("/api/v1/demo/candidates/aisha-strong-leader/run")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["candidate_id"] == "test-id-123"
        assert body["data"]["job_status"] == "queued"
        mock_submit_async.assert_awaited_once()
