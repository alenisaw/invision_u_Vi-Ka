from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.modules.admin.service import AdminService


@pytest.mark.asyncio
async def test_get_pipeline_metrics_aggregates_recent_runs() -> None:
    service = AdminService(session=object())  # type: ignore[arg-type]
    service.repository = AsyncMock()

    candidate_id = uuid4()
    log_one = SimpleNamespace(
        id=uuid4(),
        entity_id=candidate_id,
        action="pipeline_completed",
        details={
            "recommendation_status": "RECOMMEND",
            "pipeline_quality_status": "healthy",
            "quality_flags": [],
            "total_latency_ms": 420.0,
            "stage_latencies_ms": {"input_intake": 10.0, "scoring": 55.0},
        },
        created_at=datetime(2026, 4, 5, 10, 0, tzinfo=timezone.utc),
    )
    log_two = SimpleNamespace(
        id=uuid4(),
        entity_id=uuid4(),
        action="pipeline_completed",
        details={
            "recommendation_status": "WAITLIST",
            "pipeline_quality_status": "manual_review_required",
            "quality_flags": ["llm_extraction_fallback_used", "manual_review_required"],
            "total_latency_ms": 820.0,
            "stage_latencies_ms": {"input_intake": 12.0, "scoring": 80.0},
        },
        created_at=datetime(2026, 4, 5, 10, 5, tzinfo=timezone.utc),
    )
    service.repository.list_audit_logs.return_value = [log_two, log_one]

    metrics = await service.get_pipeline_metrics(limit=20)

    assert metrics.overview.total_runs == 2
    assert metrics.overview.healthy_runs == 1
    assert metrics.overview.manual_review_runs == 1
    assert metrics.overview.avg_total_latency_ms == 620.0
    assert metrics.overview.avg_stage_latencies_ms["scoring"] == 67.5
    assert metrics.overview.fallback_counts["llm_extraction_fallback_used"] == 1
    assert metrics.recent_runs[0].recommendation_status == "WAITLIST"
