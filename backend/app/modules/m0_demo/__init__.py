# app/modules/m0_demo/__init__.py
"""
Public exports for the demo module.

Purpose:
- Expose fixture schemas and loading helpers from one package entrypoint.
- Keep imports stable for routers and tests.
"""

from .schemas import FixtureDetail, FixtureMeta, FixtureSummary
from .service import DemoFixtureService

__all__ = [
    "DemoFixtureService",
    "FixtureDetail",
    "FixtureMeta",
    "FixtureSummary",
]
