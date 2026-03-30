from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.core.audit import build_audit_event_hash


def test_build_audit_event_hash_is_stable_for_same_payload() -> None:
    created_at = datetime(2026, 3, 30, 20, 0, tzinfo=timezone.utc)
    entity_id = uuid4()
    payload = {"candidate_id": str(entity_id), "status": "completed"}

    first_hash = build_audit_event_hash(
        secret="audit-secret-1234567890",
        sequence_no=1,
        prev_hash=None,
        entity_type="pipeline_job",
        entity_id=entity_id,
        action="pipeline_job_completed",
        actor="system",
        details=payload,
        created_at=created_at,
    )
    second_hash = build_audit_event_hash(
        secret="audit-secret-1234567890",
        sequence_no=1,
        prev_hash=None,
        entity_type="pipeline_job",
        entity_id=entity_id,
        action="pipeline_job_completed",
        actor="system",
        details=payload,
        created_at=created_at,
    )

    assert first_hash == second_hash


def test_build_audit_event_hash_changes_when_prev_hash_changes() -> None:
    created_at = datetime(2026, 3, 30, 20, 0, tzinfo=timezone.utc)

    first_hash = build_audit_event_hash(
        secret="audit-secret-1234567890",
        sequence_no=2,
        prev_hash="prev-a",
        entity_type="candidate",
        entity_id=None,
        action="override",
        actor="reviewer.alina",
        details={"new_status": "RECOMMEND"},
        created_at=created_at,
    )
    second_hash = build_audit_event_hash(
        secret="audit-secret-1234567890",
        sequence_no=2,
        prev_hash="prev-b",
        entity_type="candidate",
        entity_id=None,
        action="override",
        actor="reviewer.alina",
        details={"new_status": "RECOMMEND"},
        created_at=created_at,
    )

    assert first_hash != second_hash
