# app/core/rate_limit.py
"""
Rate-limit primitives for public and reviewer endpoints.

Purpose:
- Provide a minimal limiter interface for API dependencies.
- Support in-memory and Redis-backed enforcement with one contract.
"""

from __future__ import annotations

import asyncio
import time
from typing import Protocol

from app.core.config import get_settings


class RateLimiter(Protocol):
    async def hit(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int, int]: ...


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._windows: dict[str, tuple[int, int]] = {}
        self._lock = asyncio.Lock()

    async def hit(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int, int]:
        current_window = int(time.time() // window_seconds)
        async with self._lock:
            window_key = f"{key}:{current_window}"
            count = 0
            if window_key in self._windows:
                _, count = self._windows[window_key]
            count += 1
            self._windows = {
                stored_key: value
                for stored_key, value in self._windows.items()
                if stored_key.endswith(f":{current_window}")
            }
            self._windows[window_key] = (current_window, count)
        allowed = count <= limit
        remaining = max(0, limit - count)
        retry_after = window_seconds - (int(time.time()) % window_seconds)
        return allowed, remaining, retry_after


class RedisRateLimiter:
    def __init__(self, redis_url: str, namespace: str = "invisionu:ratelimit") -> None:
        try:
            from redis import asyncio as redis_asyncio
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise RuntimeError("redis package is required for Redis-backed rate limiting") from exc

        self._client = redis_asyncio.from_url(redis_url, decode_responses=True)
        self._namespace = namespace

    async def hit(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int, int]:
        current_window = int(time.time() // window_seconds)
        redis_key = f"{self._namespace}:{key}:{current_window}"
        count = await self._client.incr(redis_key)
        if count == 1:
            await self._client.expire(redis_key, window_seconds)
        allowed = count <= limit
        remaining = max(0, limit - int(count))
        retry_after = window_seconds - (int(time.time()) % window_seconds)
        return allowed, remaining, retry_after


_memory_rate_limiter = InMemoryRateLimiter()
_rate_limiter_singleton: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter_singleton

    if _rate_limiter_singleton is not None:
        return _rate_limiter_singleton

    settings = get_settings()
    if settings.pipeline_queue_backend == "redis":
        _rate_limiter_singleton = RedisRateLimiter(settings.redis_url)
    else:
        _rate_limiter_singleton = _memory_rate_limiter
    return _rate_limiter_singleton


def reset_rate_limiter() -> None:
    global _rate_limiter_singleton
    _rate_limiter_singleton = None
