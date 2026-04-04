from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_reviewer_api_key, require_roles
from app.modules.auth.schemas import UserResponse
from app.modules.m10_audit.schemas import ReviewerActionCreateRequest
from app.modules.m10_audit.service import AuditService, AuditWorkflowError
from app.schemas.common import success_response


dashboard_router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["dashboard"],
    dependencies=[Depends(require_reviewer_api_key)],
)

audit_router = APIRouter(
    prefix="/api/v1/audit",
    tags=["audit"],
)


@dashboard_router.post("/candidates/{candidate_id}/actions")
async def create_candidate_reviewer_action(
    candidate_id: UUID,
    payload: ReviewerActionCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = AuditService(db)
    try:
        action = await service.create_reviewer_action(candidate_id, payload)
    except AuditWorkflowError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    return success_response(action.model_dump(mode="json"))


@dashboard_router.get("/candidates/{candidate_id}/actions")
async def list_candidate_reviewer_actions(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = AuditService(db)
    try:
        actions = await service.list_reviewer_actions(candidate_id)
    except AuditWorkflowError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    return success_response([action.model_dump(mode="json") for action in actions])


@audit_router.get("/feed")
async def get_audit_feed(
    limit: int = Query(default=100, ge=1, le=500),
    current_user: UserResponse = Depends(require_roles("admin")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = AuditService(db)
    entries = await service.list_audit_feed(limit=limit)
    return success_response([entry.model_dump(mode="json") for entry in entries])


router = APIRouter()
router.include_router(dashboard_router)
router.include_router(audit_router)
