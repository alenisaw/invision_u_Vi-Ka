from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app


def test_http_exceptions_use_common_error_envelope() -> None:
    with patch(
        "app.main.AuthService.bootstrap_admin_user",
        new=AsyncMock(return_value=None),
    ):
        with TestClient(app) as client:
            response = client.post("/api/v1/pipeline/batch", json=[])

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "Empty batch"
    assert "meta" in body


def test_request_validation_errors_use_common_error_envelope() -> None:
    with patch(
        "app.main.AuthService.bootstrap_admin_user",
        new=AsyncMock(return_value=None),
    ):
        with TestClient(app) as client:
            response = client.post("/api/v1/candidates/intake", json={})

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "Invalid request payload"
    assert body["error"]["details"]["errors"]


def test_authenticated_route_errors_use_common_error_envelope() -> None:
    with patch(
        "app.main.AuthService.bootstrap_admin_user",
        new=AsyncMock(return_value=None),
    ):
        with TestClient(app) as client:
            response = client.get("/api/v1/dashboard/stats")

    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert body["error"]["message"] == "Authentication is required"
