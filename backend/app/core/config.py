from functools import lru_cache

from pydantic import Field, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PLACEHOLDER_SECRET_PREFIXES = ("change-me", "replace_with", "your_", "test-")
INSECURE_SECRET_VALUES = frozenset(
    {
        "",
        "postgres",
        "password",
        "changeme",
        "change-me-reviewer-key",
        "change-me-to-a-32-byte-minimum-secret-for-development",
        "test-reviewer-key",
    }
)
DEVELOPMENT_ENVS = {"development", "dev", "local", "test"}


def _looks_insecure_secret(value: str) -> bool:
    normalized = value.strip()
    if normalized.lower() in INSECURE_SECRET_VALUES:
        return True
    return normalized.lower().startswith(PLACEHOLDER_SECRET_PREFIXES)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "inVision U Candidate Selection System"
    app_description: str = (
        "Backend API for candidate intake, scoring pipeline, "
        "and reviewer dashboard."
    )
    app_version: str = "1.0.0"
    app_env: str = "development"
    app_debug: bool = False

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    api_v1_prefix: str = "/api/v1"
    api_key: str = Field(min_length=24)
    default_reviewer_id: str = Field(default="reviewer_api_client", min_length=3, max_length=100)
    reviewer_api_keys_json: str = ""

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "invisionu"
    postgres_user: str = "postgres"
    postgres_password: str = Field(min_length=8)

    pii_encryption_key: str = Field(min_length=32)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_development(self) -> bool:
        return self.app_env.strip().lower() in DEVELOPMENT_ENVS

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        return (
            "postgresql+asyncpg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        if self.app_debug and not self.is_development:
            raise ValueError("APP_DEBUG must remain disabled outside development")

        if _looks_insecure_secret(self.api_key):
            raise ValueError("API_KEY must be configured with a non-placeholder secret")

        if _looks_insecure_secret(self.pii_encryption_key):
            raise ValueError(
                "PII_ENCRYPTION_KEY must be configured with a strong non-placeholder secret"
            )

        if _looks_insecure_secret(self.postgres_password) and not self.is_development:
            raise ValueError(
                "POSTGRES_PASSWORD must be configured with a non-default secret outside development"
            )

        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
