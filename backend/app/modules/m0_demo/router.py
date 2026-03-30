# app/modules/m0_demo/router.py
"""
Demo endpoints for fixture discovery and execution.

Purpose:
- Return packaged candidate fixtures for demos and testing.
- Queue fixture payloads through the asynchronous pipeline.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.modules.m0_demo.schemas import FixtureDetail, FixtureSummary
from app.modules.m0_demo.service import DemoFixtureService
from app.modules.m1_gateway.orchestrator import PipelineOrchestrator
from app.schemas.common import success_response

router = APIRouter(prefix="/api/v1/demo", tags=["demo"])

_fixture_service = DemoFixtureService()


@router.get("/candidates")
async def list_demo_candidates() -> dict:
    """List all available demo candidate fixtures."""
    fixtures = _fixture_service.list_fixtures()
    return success_response([f.model_dump(mode="json") for f in fixtures])


@router.get("/candidates/{slug}")
async def get_demo_candidate(slug: str) -> dict:
    """Get a single demo fixture with its full payload."""
    try:
        detail = _fixture_service.get_fixture(slug)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Fixture '{slug}' not found")
    return success_response(detail.model_dump(mode="json"))


@router.post("/candidates/{slug}/run")
async def run_demo_candidate(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Load a demo fixture and queue it through the asynchronous pipeline."""
    try:
        payload = _fixture_service.get_fixture_payload(slug)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Fixture '{slug}' not found")

    try:
        orchestrator = PipelineOrchestrator(db)
        result = await orchestrator.submit_async(payload, requested_by="demo_fixture")
        return success_response(result.model_dump(mode="json"))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
