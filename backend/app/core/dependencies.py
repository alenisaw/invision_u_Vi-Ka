from collections.abc import AsyncIterator
import secrets

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db_session
from app.modules.auth.schemas import RoleLiteral, UserResponse
from app.modules.auth.service import AuthService


async def get_db() -> AsyncIterator[AsyncSession]:
    async for session in get_db_session():
        yield session


def require_reviewer_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    settings = get_settings()
    configured_api_key = (settings.api_key or "").strip()

    if not configured_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reviewer API key is not configured",
        )

    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
        )

    if not secrets.compare_digest(x_api_key, configured_api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    settings = get_settings()
    session_token = request.cookies.get(settings.session_cookie_name)

    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required",
        )

    service = AuthService(db)
    user = await service.get_user_from_session_token(session_token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is invalid or expired",
        )
    return user


async def require_authenticated_user(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    return current_user


def require_roles(*allowed_roles: RoleLiteral):
    async def role_dependency(
        current_user: UserResponse = Depends(get_current_user),
    ) -> UserResponse:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this resource",
            )
        return current_user

    return role_dependency
