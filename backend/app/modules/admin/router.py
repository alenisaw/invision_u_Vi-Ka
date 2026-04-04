from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_roles
from app.modules.admin.schemas import AdminUserCreateRequest, AdminUserUpdateRequest
from app.modules.admin.service import AdminService
from app.modules.auth.schemas import UserResponse
from app.schemas.common import success_response


router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/users")
async def list_users(
    current_user: UserResponse = Depends(require_roles("admin")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = AdminService(db)
    users = await service.list_users()
    return success_response([user.model_dump(mode="json") for user in users])


@router.post("/users")
async def create_user(
    payload: AdminUserCreateRequest,
    current_user: UserResponse = Depends(require_roles("admin")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = AdminService(db)
    user = await service.create_user(payload, actor=current_user)
    return success_response(user.model_dump(mode="json"))


@router.patch("/users/{user_id}")
async def update_user(
    user_id: UUID,
    payload: AdminUserUpdateRequest,
    current_user: UserResponse = Depends(require_roles("admin")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = AdminService(db)
    user = await service.update_user(user_id, payload, actor=current_user)
    return success_response(user.model_dump(mode="json"))
