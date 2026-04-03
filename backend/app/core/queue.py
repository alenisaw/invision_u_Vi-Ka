# app/core/queue.py
"""
Queue abstraction for asynchronous pipeline execution.

Purpose:
- Provide one interface for in-memory and Redis-backed job queues.
- Keep transport concerns separate from pipeline business logic.
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from typing import Protocol

from app.core.config import get_settings


class JobQueue(Protocol):
    async def enqueue_job(self, job_id: str) -> None: ...

    async def reserve_job(self, timeout_seconds: int = 1) -> str | None: ...

    async def ack_job(self, job_id: str) -> None: ...

    async def retry_job(self, job_id: str, delay_seconds: int = 0) -> None: ...

    async def fail_job(self, job_id: str) -> None: ...

    async def promote_due_jobs(self, limit: int = 100) -> int: ...

    async def get_depth(self) -> dict[str, int]: ...

    async def list_dead_jobs(self, limit: int = 100) -> list[str]: ...

    async def list_delayed_jobs(self, limit: int = 100) -> list[str]: ...

    async def requeue_job(self, job_id: str) -> bool: ...

    async def inspect_job(self, job_id: str) -> dict[str, object]: ...


class InMemoryJobQueue:
    def __init__(self) -> None:
        self._pending: deque[str] = deque()
        self._processing: list[str] = []
        self._dead: deque[str] = deque()
        self._delayed: list[tuple[float, str]] = []

    async def enqueue_job(self, job_id: str) -> None:
        self._pending.appendleft(job_id)

    async def reserve_job(self, timeout_seconds: int = 1) -> str | None:
        await self.promote_due_jobs()
        if self._pending:
            job_id = self._pending.pop()
            self._processing.append(job_id)
            return job_id
        if timeout_seconds > 0:
            await asyncio.sleep(timeout_seconds)
        return None

    async def ack_job(self, job_id: str) -> None:
        self._remove_processing(job_id)

    async def retry_job(self, job_id: str, delay_seconds: int = 0) -> None:
        self._remove_processing(job_id)
        if delay_seconds <= 0:
            self._pending.appendleft(job_id)
            return
        self._delayed.append((time.time() + delay_seconds, job_id))

    async def fail_job(self, job_id: str) -> None:
        self._remove_processing(job_id)
        self._dead.appendleft(job_id)

    async def promote_due_jobs(self, limit: int = 100) -> int:
        now = time.time()
        promoted = 0
        remaining: list[tuple[float, str]] = []
        for due_at, job_id in sorted(self._delayed, key=lambda item: item[0]):
            if promoted < limit and due_at <= now:
                self._pending.appendleft(job_id)
                promoted += 1
            else:
                remaining.append((due_at, job_id))
        self._delayed = remaining
        return promoted

    async def get_depth(self) -> dict[str, int]:
        return {
            "pending": len(self._pending),
            "processing": len(self._processing),
            "delayed": len(self._delayed),
            "dead": len(self._dead),
        }

    async def list_dead_jobs(self, limit: int = 100) -> list[str]:
        return list(self._dead)[:limit]

    async def list_delayed_jobs(self, limit: int = 100) -> list[str]:
        return [job_id for _, job_id in sorted(self._delayed, key=lambda item: item[0])[:limit]]

    async def requeue_job(self, job_id: str) -> bool:
        removed = False
        try:
            self._dead.remove(job_id)
            removed = True
        except ValueError:
            pass

        remaining: list[tuple[float, str]] = []
        for due_at, delayed_job_id in self._delayed:
            if delayed_job_id == job_id:
                removed = True
                continue
            remaining.append((due_at, delayed_job_id))
        self._delayed = remaining

        if removed:
            self._pending.appendleft(job_id)
        return removed

    async def inspect_job(self, job_id: str) -> dict[str, object]:
        delayed_until = None
        for due_at, delayed_job_id in self._delayed:
            if delayed_job_id == job_id:
                delayed_until = due_at
                break
        return {
            "job_id": job_id,
            "in_pending": job_id in self._pending,
            "in_processing": job_id in self._processing,
            "in_delayed": delayed_until is not None,
            "in_dead_letter": job_id in self._dead,
            "delayed_until_epoch": None if delayed_until is None else int(delayed_until),
        }

    def _remove_processing(self, job_id: str) -> None:
        try:
            self._processing.remove(job_id)
        except ValueError:
            return


class RedisJobQueue:
    def __init__(self, redis_url: str, queue_name: str) -> None:
        try:
            from redis import asyncio as redis_asyncio
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise RuntimeError("redis package is required for Redis-backed job queue") from exc

        self._client = redis_asyncio.from_url(redis_url, decode_responses=True)
        self._pending_key = f"{queue_name}:pending"
        self._processing_key = f"{queue_name}:processing"
        self._dead_key = f"{queue_name}:dead"
        self._delayed_key = f"{queue_name}:delayed"

    async def enqueue_job(self, job_id: str) -> None:
        await self._client.lpush(self._pending_key, job_id)

    async def reserve_job(self, timeout_seconds: int = 1) -> str | None:
        await self.promote_due_jobs()
        job_id = await self._client.brpoplpush(
            self._pending_key,
            self._processing_key,
            timeout_seconds,
        )
        return str(job_id) if job_id is not None else None

    async def ack_job(self, job_id: str) -> None:
        await self._client.lrem(self._processing_key, 1, job_id)

    async def retry_job(self, job_id: str, delay_seconds: int = 0) -> None:
        await self.ack_job(job_id)
        if delay_seconds <= 0:
            await self.enqueue_job(job_id)
            return
        await self._client.zadd(
            self._delayed_key,
            {job_id: time.time() + delay_seconds},
        )

    async def fail_job(self, job_id: str) -> None:
        await self.ack_job(job_id)
        await self._client.lpush(self._dead_key, job_id)

    async def promote_due_jobs(self, limit: int = 100) -> int:
        due_job_ids = await self._client.zrangebyscore(
            self._delayed_key,
            min=0,
            max=time.time(),
            start=0,
            num=limit,
        )
        promoted = 0
        for job_id in due_job_ids:
            removed = await self._client.zrem(self._delayed_key, job_id)
            if removed:
                await self._client.lpush(self._pending_key, job_id)
                promoted += 1
        return promoted

    async def get_depth(self) -> dict[str, int]:
        pending, processing, delayed, dead = await asyncio.gather(
            self._client.llen(self._pending_key),
            self._client.llen(self._processing_key),
            self._client.zcard(self._delayed_key),
            self._client.llen(self._dead_key),
        )
        return {
            "pending": int(pending),
            "processing": int(processing),
            "delayed": int(delayed),
            "dead": int(dead),
        }

    async def list_dead_jobs(self, limit: int = 100) -> list[str]:
        job_ids = await self._client.lrange(self._dead_key, 0, max(0, limit - 1))
        return [str(job_id) for job_id in job_ids]

    async def list_delayed_jobs(self, limit: int = 100) -> list[str]:
        job_ids = await self._client.zrange(self._delayed_key, 0, max(0, limit - 1))
        return [str(job_id) for job_id in job_ids]

    async def requeue_job(self, job_id: str) -> bool:
        removed_dead = await self._client.lrem(self._dead_key, 1, job_id)
        removed_delayed = await self._client.zrem(self._delayed_key, job_id)
        if not removed_dead and not removed_delayed:
            return False
        await self._client.lpush(self._pending_key, job_id)
        return True

    async def inspect_job(self, job_id: str) -> dict[str, object]:
        pending_pos, processing_pos, dead_pos, delayed_until = await asyncio.gather(
            self._client.lpos(self._pending_key, job_id),
            self._client.lpos(self._processing_key, job_id),
            self._client.lpos(self._dead_key, job_id),
            self._client.zscore(self._delayed_key, job_id),
        )
        return {
            "job_id": job_id,
            "in_pending": pending_pos is not None,
            "in_processing": processing_pos is not None,
            "in_delayed": delayed_until is not None,
            "in_dead_letter": dead_pos is not None,
            "delayed_until_epoch": None if delayed_until is None else int(float(delayed_until)),
        }


_memory_queue = InMemoryJobQueue()
_queue_singleton: JobQueue | None = None


def get_job_queue() -> JobQueue:
    global _queue_singleton

    if _queue_singleton is not None:
        return _queue_singleton

    settings = get_settings()
    if settings.pipeline_queue_backend == "redis":
        _queue_singleton = RedisJobQueue(
            redis_url=settings.redis_url,
            queue_name=settings.pipeline_queue_name,
        )
    else:
        _queue_singleton = _memory_queue
    return _queue_singleton


def reset_job_queue() -> None:
    global _queue_singleton
    _queue_singleton = None
