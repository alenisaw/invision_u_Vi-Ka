"""
File: common.py
Purpose: Shared API response helpers for backend routes.

Notes:
- Keep the transport envelope stable even while inner modules evolve.
- Helpers return plain dictionaries so routes stay compact.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

API_VERSION = "1.0.0"


def success_response(data: Any, version: str = API_VERSION) -> dict[str, Any]:
    """Wrap successful responses in the common API envelope."""

    return {
        "success": True,
        "data": data,
        "error": None,
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": version,
        },
    }


def error_response(
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    version: str = API_VERSION,
) -> dict[str, Any]:
    """Wrap error responses in the common API envelope."""

    return {
        "success": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": version,
        },
    }


# File summary: common.py
# Provides compact success and error response envelope helpers.
