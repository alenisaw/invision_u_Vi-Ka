from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.schemas import (
    AdminUserCreateRequest,
    AdminUserResponse,
    AdminUserUpdateRequest,
)
from app.modules.auth.schemas import UserResponse
from app.modules.auth.service import hash_password, normalize_email
from app.modules.storage import StorageRepository, User


class AdminService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = StorageRepository(session)

    async def list_users(self) -> list[AdminUserResponse]:
        users = await self.repository.list_users()
        return [self._to_response(user) for user in users]

    async def create_user(
        self,
        payload: AdminUserCreateRequest,
        *,
        actor: UserResponse,
    ) -> AdminUserResponse:
        email = normalize_email(payload.email)
        existing = await self.repository.get_user_by_email(email)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists",
            )

        user = await self.repository.create_user(
            email=email,
            full_name=payload.full_name.strip(),
            password_hash=hash_password(payload.password),
            role=payload.role,
            is_active=payload.is_active,
        )
        await self.repository.create_audit_log(
            entity_type="user",
            entity_id=user.id,
            action="user_created",
            actor=actor.email,
            details={"role": user.role, "email": user.email, "is_active": user.is_active},
        )
        await self.repository.commit()
        return self._to_response(user)

    async def update_user(
        self,
        user_id: UUID,
        payload: AdminUserUpdateRequest,
        *,
        actor: UserResponse,
    ) -> AdminUserResponse:
        user = await self.repository.get_user(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        changed_fields: dict[str, object] = {}
        if payload.full_name is not None and payload.full_name != user.full_name:
            user.full_name = payload.full_name
            changed_fields["full_name"] = payload.full_name
        if payload.password is not None:
            user.password_hash = hash_password(payload.password)
            changed_fields["password_reset"] = True
        if payload.role is not None and payload.role != user.role:
            user.role = payload.role
            changed_fields["role"] = payload.role
        if payload.is_active is not None and payload.is_active != user.is_active:
            user.is_active = payload.is_active
            changed_fields["is_active"] = payload.is_active

        if not changed_fields:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No user changes were provided",
            )

        if actor.id == user.id and payload.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="You cannot deactivate your own account",
            )

        if payload.password is not None or payload.is_active is False:
            await self.repository.delete_user_sessions_for_user(user.id)

        await self.repository.create_audit_log(
            entity_type="user",
            entity_id=user.id,
            action="user_updated",
            actor=actor.email,
            details=changed_fields,
        )
        await self.repository.commit()
        return self._to_response(user)

    def _to_response(self, user: User) -> AdminUserResponse:
        return AdminUserResponse.model_validate(user)
