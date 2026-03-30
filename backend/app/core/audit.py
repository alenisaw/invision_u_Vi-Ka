# app/core/audit.py
"""
Helpers for tamper-evident audit records.

Purpose:
- Build stable hashes for audit events.
- Verify the append-only audit chain during inspection.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime
from typing import Any
from uuid import UUID


AUDIT_SIGNATURE_VERSION = "v1"


def build_audit_event_hash(
    *,
    secret: str,
    sequence_no: int,
    prev_hash: str | None,
    entity_type: str,
    entity_id: UUID | None,
    action: str,
    actor: str,
    details: dict[str, Any],
    created_at: datetime,
) -> str:
    payload = {
        "sequence_no": sequence_no,
        "prev_hash": prev_hash,
        "entity_type": entity_type,
        "entity_id": _normalize_value(entity_id),
        "action": action,
        "actor": actor,
        "details": _normalize_value(details),
        "created_at": _normalize_value(created_at),
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hmac.new(
        secret.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _normalize_value(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _normalize_value(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return [_normalize_value(item) for item in value]
    if isinstance(value, tuple):
        return [_normalize_value(item) for item in value]
    return value
