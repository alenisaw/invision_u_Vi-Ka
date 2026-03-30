"""
File: schemas.py
Purpose: Demo module API contracts.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class FixtureMeta(BaseModel):
    model_config = ConfigDict(frozen=True)

    slug: str
    display_name: str
    archetype: str
    program: str
    language: str = "ru"
    essay_preview: str = ""


class FixtureSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    meta: FixtureMeta


class FixtureDetail(BaseModel):
    meta: FixtureMeta
    payload: dict
