from functools import lru_cache

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    app_debug: bool = True

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    api_v1_prefix: str = "/api/v1"
    session_cookie_name: str = "invisionu_session"
    session_ttl_hours: int = 168
    session_secret: str = "change-me-auth-session-secret"
    bootstrap_admin_email: str = "admin@invisionu.local"
    bootstrap_admin_password: str = "admin"
    bootstrap_admin_full_name: str = "Main Admin"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "invisionu"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"

    pii_encryption_key: str = (
        "change-me-to-a-32-byte-minimum-secret-for-development"
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        return (
            "postgresql+asyncpg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
