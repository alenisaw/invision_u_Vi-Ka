"""
Shared LLM helpers for extraction-stage provider clients.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any


logger = logging.getLogger(__name__)

MAX_LLM_ATTEMPTS = 3
BACKOFF_BASE_SECONDS = 0.75
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


@dataclass(frozen=True)
class SignalGroupSpec:
    name: str
    signals: tuple[str, ...]
    source_fields: tuple[str, ...]
    purpose: str
    model_tier: str = "primary"


def normalize_signal_container(parsed: dict[str, Any], group_name: str) -> dict[str, Any]:
    raw_signals = parsed.get("signals", {})
    if isinstance(raw_signals, dict):
        return raw_signals
    if isinstance(raw_signals, list):
        normalized: dict[str, Any] = {}
        for item in raw_signals:
            if not isinstance(item, dict):
                continue
            signal_name = item.get("signal_name")
            if not isinstance(signal_name, str) or not signal_name.strip():
                continue
            normalized[signal_name.strip()] = {
                key: value
                for key, value in item.items()
                if key != "signal_name"
            }
        if normalized:
            logger.info(
                "Normalized list-based LLM signals for group %s (%d items)",
                group_name,
                len(normalized),
            )
            return normalized
    logger.error(
        "Structured response for group %s has unexpected signals payload type: %s",
        group_name,
        type(raw_signals).__name__,
    )
    raise ValueError("LLM response does not contain a valid `signals` payload.")
