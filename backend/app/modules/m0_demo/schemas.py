# app/modules/m0_demo/schemas.py
"""
Schema models for demo fixtures.

Purpose:
- Describe demo metadata returned by the API.
- Keep fixture payload contracts explicit and typed.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class FixtureMeta(BaseModel):
    model_config = ConfigDict(frozen=True)

    slug: str
    display_name: str
    program: str
    language: str = "ru"
    essay_preview: str = ""


class FixtureSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    meta: FixtureMeta


class FixtureDetail(BaseModel):
    meta: FixtureMeta
    payload: dict
