from __future__ import annotations

from pydantic import ValidationError

from app.core.config import Settings


def test_rejects_placeholder_api_key() -> None:
    try:
        Settings(
            api_key="replace_with_long_random_reviewer_api_key",
            pii_encryption_key="x" * 32,
            postgres_password="local-dev-password",
        )
    except ValidationError as exc:
        assert "API_KEY" in str(exc) or "api_key" in str(exc)
    else:  # pragma: no cover - defensive failure branch
        raise AssertionError("Expected placeholder API key to be rejected")


def test_rejects_debug_mode_outside_development() -> None:
    try:
        Settings(
            app_env="production",
            app_debug=True,
            api_key="reviewer-key-1234567890-abcdef",
            pii_encryption_key="x" * 32,
            postgres_password="production-db-password",
        )
    except ValidationError as exc:
        assert "APP_DEBUG" in str(exc)
    else:  # pragma: no cover - defensive failure branch
        raise AssertionError("Expected APP_DEBUG validation to trigger")


def test_accepts_secure_runtime_configuration() -> None:
    settings = Settings(
        app_env="production",
        app_debug=False,
        api_key="reviewer-key-1234567890-abcdef",
        pii_encryption_key="very-secure-pii-encryption-secret-123456",
        postgres_password="production-db-password",
    )

    assert settings.app_debug is False
    assert settings.is_development is False
