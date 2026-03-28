"""
File: program_policy.py
Purpose: Canonical program normalization and program-aware weight helpers for M6.

Notes:
- Program context is safe operational context, not a demographic signal.
- The policy adjusts relevance weighting only across approved sub-scores.
"""

from __future__ import annotations

from .m6_scoring_config import DEFAULT_POLICY_CONFIG, DEFAULT_PROGRAM_ID, PROGRAM_CATALOG, PROGRAM_WEIGHT_PROFILES


def normalize_program_id(selected_program: str | None, default_program_id: str = DEFAULT_PROGRAM_ID) -> str:
    """Resolve raw program text into a canonical program id."""

    normalized = (selected_program or "").strip().lower()
    if not normalized:
        return default_program_id

    for program_id, payload in PROGRAM_CATALOG.items():
        aliases = [str(alias).strip().lower() for alias in payload.get("aliases", [])]
        display_name = str(payload.get("display_name", "")).strip().lower()
        if normalized == program_id or normalized == display_name or normalized in aliases:
            return program_id
    return default_program_id


def get_program_definition(program_id: str | None) -> dict[str, str | list[str]]:
    """Return the configured program definition or the default one."""

    resolved_program_id = normalize_program_id(program_id, default_program_id=DEFAULT_POLICY_CONFIG.default_program_id)
    return dict(PROGRAM_CATALOG.get(resolved_program_id, PROGRAM_CATALOG.get(DEFAULT_PROGRAM_ID, {})))


def get_program_weight_profile(program_id: str | None) -> dict[str, float]:
    """Return the per-program sub-score weights or the base scoring weights."""

    resolved_program_id = normalize_program_id(program_id, default_program_id=DEFAULT_POLICY_CONFIG.default_program_id)
    profile = PROGRAM_WEIGHT_PROFILES.get(resolved_program_id)
    if not profile:
        return dict(DEFAULT_POLICY_CONFIG.scoring_weights)
    return dict(profile)


# File summary: program_policy.py
# Normalizes selected programs and exposes explicit program-aware scoring weight profiles.
