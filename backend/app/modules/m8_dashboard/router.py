from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_reviewer_api_key
from app.modules.m10_audit.schemas import CandidateOverrideRequest
from app.modules.m10_audit.service import AuditService, AuditWorkflowError
from app.modules.m8_dashboard.service import DashboardService
from app.schemas.common import success_response


router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["dashboard"],
    dependencies=[Depends(require_reviewer_api_key)],
)


@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = DashboardService(db)
    stats = await service.get_stats()
    return success_response(stats.model_dump(mode="json"))


@router.get("/candidates")
async def list_dashboard_candidates(
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = DashboardService(db)
    candidates = await service.list_candidates()
    return success_response([candidate.model_dump(mode="json") for candidate in candidates])


@router.get("/candidates/{candidate_id}")
async def get_dashboard_candidate_detail(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = DashboardService(db)
    try:
        detail = await service.get_candidate_detail(candidate_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return success_response(detail.model_dump(mode="json"))


@router.post("/candidates/{candidate_id}/override")
async def override_dashboard_candidate(
    candidate_id: UUID,
    payload: CandidateOverrideRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = AuditService(db)
    try:
        action = await service.override_candidate_decision(candidate_id, payload)
    except AuditWorkflowError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    return success_response(action.model_dump(mode="json"))


@router.get("/shortlist")
async def list_dashboard_shortlist(
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = DashboardService(db)
    shortlisted = await service.list_shortlist()
    return success_response([candidate.model_dump(mode="json") for candidate in shortlisted])
