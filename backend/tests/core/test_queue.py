from __future__ import annotations

import pytest

from app.core.queue import InMemoryJobQueue


@pytest.mark.asyncio
async def test_in_memory_queue_enqueue_reserve_ack_cycle() -> None:
    queue = InMemoryJobQueue()

    await queue.enqueue_job("job-1")
    reserved = await queue.reserve_job(timeout_seconds=0)

    assert reserved == "job-1"
    assert await queue.get_depth() == {
        "pending": 0,
        "processing": 1,
        "delayed": 0,
        "dead": 0,
    }

    await queue.ack_job("job-1")
    assert await queue.get_depth() == {
        "pending": 0,
        "processing": 0,
        "delayed": 0,
        "dead": 0,
    }


@pytest.mark.asyncio
async def test_in_memory_queue_promotes_delayed_retries() -> None:
    queue = InMemoryJobQueue()

    await queue.enqueue_job("job-2")
    reserved = await queue.reserve_job(timeout_seconds=0)
    assert reserved == "job-2"

    await queue.retry_job("job-2", delay_seconds=0)
    promoted = await queue.promote_due_jobs()

    assert promoted == 0
    assert await queue.reserve_job(timeout_seconds=0) == "job-2"


@pytest.mark.asyncio
async def test_in_memory_queue_inspects_job_location() -> None:
    queue = InMemoryJobQueue()

    await queue.enqueue_job("job-3")
    pending_state = await queue.inspect_job("job-3")
    reserved = await queue.reserve_job(timeout_seconds=0)
    processing_state = await queue.inspect_job("job-3")
    await queue.fail_job("job-3")
    dead_state = await queue.inspect_job("job-3")

    assert reserved == "job-3"
    assert pending_state["in_pending"] is True
    assert processing_state["in_processing"] is True
    assert dead_state["in_dead_letter"] is True
