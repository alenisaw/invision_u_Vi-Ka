"""
File: io_utils.py
Purpose: Shared safe path helpers for M6 artifacts and report exports.
"""

from __future__ import annotations

from pathlib import Path

from .m6_scoring_config import TRUSTED_MODEL_ARTIFACT_DIRS, TRUSTED_REPORT_DIRS

REPO_ROOT = Path(__file__).resolve().parents[4]


def _resolve_within_repo(path: str | Path) -> Path:
    """Resolve a path and ensure it remains inside the repository root."""

    resolved = Path(path).expanduser()
    if not resolved.is_absolute():
        resolved = (REPO_ROOT / resolved).resolve()
    else:
        resolved = resolved.resolve()

    try:
        resolved.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise ValueError(f"path escapes the repository root: {resolved}") from exc
    return resolved


def _trusted_roots(raw_roots: tuple[str, ...]) -> tuple[Path, ...]:
    """Resolve configured trusted roots into absolute repository paths."""

    return tuple(_resolve_within_repo(raw_root) for raw_root in raw_roots)


def ensure_trusted_artifact_path(path: str | Path) -> Path:
    """Validate that a model artifact path stays within trusted artifact roots."""

    resolved = _resolve_within_repo(path)
    for root in _trusted_roots(TRUSTED_MODEL_ARTIFACT_DIRS):
        if resolved == root or root in resolved.parents:
            return resolved
    raise ValueError(f"model artifact path is outside trusted roots: {resolved}")


def ensure_trusted_report_dir(path: str | Path) -> Path:
    """Validate that an evaluation output directory stays within trusted report roots."""

    resolved = _resolve_within_repo(path)
    for root in _trusted_roots(TRUSTED_REPORT_DIRS):
        if resolved == root or root in resolved.parents:
            return resolved
    raise ValueError(f"report output path is outside trusted roots: {resolved}")


# File summary: io_utils.py
# Provides repository-bound path validation for model artifacts and report exports.
