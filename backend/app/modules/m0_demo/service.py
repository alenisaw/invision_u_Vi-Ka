"""
File: service.py
Purpose: Loads demo fixture files and converts them to intake payloads.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Sequence

from app.modules.m0_demo.schemas import FixtureDetail, FixtureMeta, FixtureSummary
from app.modules.m2_intake.schemas import CandidateIntakeRequest

logger = logging.getLogger(__name__)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
_PREVIEW_LENGTH = 120


@lru_cache(maxsize=1)
def _load_all_fixtures() -> dict[str, dict]:
    """Read every .json file in the fixtures directory once."""

    fixtures: dict[str, dict] = {}
    if not FIXTURES_DIR.is_dir():
        logger.warning("Fixtures directory not found: %s", FIXTURES_DIR)
        return fixtures

    for path in sorted(FIXTURES_DIR.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8-sig"))
            slug = raw.get("_meta", {}).get("slug", path.stem)
            fixtures[slug] = raw
        except Exception:
            logger.exception("Failed to load fixture %s", path.name)
    return fixtures


def _extract_meta(raw: dict) -> FixtureMeta:
    meta_fields = dict(raw["_meta"])
    content = raw.get("content") or {}
    narrative = (content.get("transcript_text") or content.get("essay_text") or "").strip()
    preview = narrative[:_PREVIEW_LENGTH].rstrip() + ("..." if len(narrative) > _PREVIEW_LENGTH else "")
    meta_fields["content_preview"] = preview or "Transcript preview is not available"
    return FixtureMeta(**meta_fields)


def _strip_meta(raw: dict) -> dict:
    """Return a normalized payload copy without fixture-only metadata."""

    payload = {key: value for key, value in raw.items() if key != "_meta"}
    slug = str(raw.get("_meta", {}).get("slug", "demo-candidate")).strip() or "demo-candidate"

    content = payload.get("content")
    if not isinstance(content, dict):
        content = {}
        payload["content"] = content

    if not str(content.get("video_url", "")).strip():
        content["video_url"] = f"https://youtube.com/watch?v={slug}"

    return payload


class DemoFixtureService:
    """Stateless service that exposes pre-built candidate fixtures."""

    def list_fixtures(self) -> Sequence[FixtureSummary]:
        return [FixtureSummary(meta=_extract_meta(raw)) for raw in _load_all_fixtures().values()]

    def get_fixture(self, slug: str) -> FixtureDetail:
        raw = _load_all_fixtures().get(slug)
        if raw is None:
            raise KeyError(slug)
        return FixtureDetail(meta=_extract_meta(raw), payload=_strip_meta(raw))

    def get_fixture_payload(self, slug: str) -> CandidateIntakeRequest:
        raw = _load_all_fixtures().get(slug)
        if raw is None:
            raise KeyError(slug)
        return CandidateIntakeRequest(**_strip_meta(raw))
