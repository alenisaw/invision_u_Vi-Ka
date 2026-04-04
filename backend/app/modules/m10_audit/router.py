from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_roles
from app.modules.auth.schemas import UserResponse
from app.modules.m10_audit.service import AuditService
from app.schemas.common import success_response

audit_router = APIRouter(
    prefix="/api/v1/audit",
    tags=["audit"],
)


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
router.include_router(audit_router)
