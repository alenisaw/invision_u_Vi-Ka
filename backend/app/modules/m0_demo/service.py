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


@lru_cache(maxsize=1)
def _load_all_fixtures() -> dict[str, dict]:
    """Read every .json file in the fixtures directory once."""
    fixtures: dict[str, dict] = {}
    if not FIXTURES_DIR.is_dir():
        logger.warning("Fixtures directory not found: %s", FIXTURES_DIR)
        return fixtures

    for path in sorted(FIXTURES_DIR.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            slug = raw.get("_meta", {}).get("slug", path.stem)
            fixtures[slug] = raw
        except Exception:
            logger.exception("Failed to load fixture %s", path.name)
    return fixtures


def _extract_meta(raw: dict) -> FixtureMeta:
    return FixtureMeta(**raw["_meta"])


def _strip_meta(raw: dict) -> dict:
    """Return a copy of the fixture without the _meta key."""
    return {k: v for k, v in raw.items() if k != "_meta"}


class DemoFixtureService:
    """Stateless service that exposes pre-built candidate fixtures."""

    def list_fixtures(self) -> Sequence[FixtureSummary]:
        return [
            FixtureSummary(meta=_extract_meta(raw))
            for raw in _load_all_fixtures().values()
        ]

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
