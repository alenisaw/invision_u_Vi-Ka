from collections.abc import AsyncIterator
import json
import secrets
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db_session
from app.core.rate_limit import get_rate_limiter


async def get_db() -> AsyncIterator[AsyncSession]:
    async for session in get_db_session():
        yield session


@dataclass(frozen=True)
class ReviewerAuthContext:
    reviewer_id: str
    auth_scheme: str = "api_key"


def _load_reviewer_api_keys() -> dict[str, str]:
    settings = get_settings()
    raw_value = str(getattr(settings, "reviewer_api_keys_json", "") or "").strip()
    if not raw_value:
        return {}
    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reviewer API key mapping is invalid",
        ) from exc
    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reviewer API key mapping must be an object",
        )
    normalized: dict[str, str] = {}
    for reviewer_id, reviewer_key in parsed.items():
        if not isinstance(reviewer_id, str) or not isinstance(reviewer_key, str):
            continue
        if reviewer_id.strip() and reviewer_key.strip():
            normalized[reviewer_id.strip()] = reviewer_key.strip()
    return normalized


def require_reviewer_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> ReviewerAuthContext:
    settings = get_settings()

    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
        )

    reviewer_api_keys = _load_reviewer_api_keys()
    for reviewer_id, reviewer_key in reviewer_api_keys.items():
        if secrets.compare_digest(x_api_key, reviewer_key):
            return ReviewerAuthContext(reviewer_id=reviewer_id)

    configured_api_key = str(getattr(settings, "api_key", "") or "").strip()
    if secrets.compare_digest(x_api_key, configured_api_key):
        return ReviewerAuthContext(
            reviewer_id=str(getattr(settings, "default_reviewer_id", "reviewer_api_client")),
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid API key",
    )


async def enforce_submit_rate_limit(request: Request) -> None:
    settings = get_settings()
    client_host = request.client.host if request.client is not None else "unknown"
    limiter = get_rate_limiter()
    allowed, _, retry_after = await limiter.hit(
        key=f"submit:{client_host}",
        limit=int(getattr(settings, "submit_rate_limit_per_minute", 60)),
        window_seconds=60,
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": "Submit rate limit exceeded",
                "retry_after_seconds": retry_after,
            },
        )


async def enforce_batch_rate_limit(request: Request) -> None:
    settings = get_settings()
    client_host = request.client.host if request.client is not None else "unknown"
    limiter = get_rate_limiter()
    allowed, _, retry_after = await limiter.hit(
        key=f"batch:{client_host}",
        limit=int(getattr(settings, "batch_rate_limit_per_minute", 10)),
        window_seconds=60,
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": "Batch submit rate limit exceeded",
                "retry_after_seconds": retry_after,
            },
        )


async def require_rate_limited_reviewer(
    request: Request,
    reviewer: ReviewerAuthContext = Depends(require_reviewer_api_key),
) -> ReviewerAuthContext:
    settings = get_settings()
    limiter = get_rate_limiter()
    allowed, _, retry_after = await limiter.hit(
        key=f"reviewer:{reviewer.reviewer_id}",
        limit=int(getattr(settings, "reviewer_rate_limit_per_minute", 120)),
        window_seconds=60,
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": "Reviewer rate limit exceeded",
                "retry_after_seconds": retry_after,
            },
        )
    _ = request
    return reviewer
