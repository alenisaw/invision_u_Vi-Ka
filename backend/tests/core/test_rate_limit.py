from __future__ import annotations

import pytest

from app.core.rate_limit import InMemoryRateLimiter


@pytest.mark.asyncio
async def test_in_memory_rate_limiter_allows_until_limit() -> None:
    limiter = InMemoryRateLimiter()

    allowed_first, _, _ = await limiter.hit("submit:127.0.0.1", limit=2, window_seconds=60)
    allowed_second, _, _ = await limiter.hit("submit:127.0.0.1", limit=2, window_seconds=60)
    allowed_third, _, retry_after = await limiter.hit(
        "submit:127.0.0.1",
        limit=2,
        window_seconds=60,
    )

    assert allowed_first is True
    assert allowed_second is True
    assert allowed_third is False
    assert retry_after >= 1
