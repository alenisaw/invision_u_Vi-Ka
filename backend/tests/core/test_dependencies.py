from __future__ import annotations

import json

from app.core.config import get_settings
from app.core.dependencies import ReviewerAuthContext, require_reviewer_api_key


def test_require_reviewer_api_key_returns_default_reviewer(monkeypatch) -> None:
    monkeypatch.setenv("API_KEY", "reviewer-key-1234567890-abcdef")
    monkeypatch.setenv("POSTGRES_PASSWORD", "local-dev-password")
    monkeypatch.setenv("PII_ENCRYPTION_KEY", "very-secure-pii-encryption-secret-123456")
    monkeypatch.delenv("REVIEWER_API_KEYS_JSON", raising=False)
    get_settings.cache_clear()

    context = require_reviewer_api_key("reviewer-key-1234567890-abcdef")

    assert context == ReviewerAuthContext(reviewer_id="reviewer_api_client")
    get_settings.cache_clear()


def test_require_reviewer_api_key_uses_server_side_mapping(monkeypatch) -> None:
    monkeypatch.setenv("API_KEY", "reviewer-key-1234567890-abcdef")
    monkeypatch.setenv("POSTGRES_PASSWORD", "local-dev-password")
    monkeypatch.setenv("PII_ENCRYPTION_KEY", "very-secure-pii-encryption-secret-123456")
    monkeypatch.setenv(
        "REVIEWER_API_KEYS_JSON",
        json.dumps({"reviewer.alina": "mapped-key-1234567890"}),
    )
    get_settings.cache_clear()

    context = require_reviewer_api_key("mapped-key-1234567890")

    assert context == ReviewerAuthContext(reviewer_id="reviewer.alina")
    get_settings.cache_clear()

