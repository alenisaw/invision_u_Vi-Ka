from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_authenticated_user
from app.modules.auth.schemas import LoginRequest, UserResponse
from app.modules.auth.service import AuthService
from app.schemas.common import success_response


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login")
async def login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = AuthService(db)
    try:
        session_payload, session_token = await service.login(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    response.set_cookie(
        value=session_token,
        **service.cookie_settings(),
    )
    return success_response(session_payload.model_dump(mode="json"))


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: UserResponse = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = AuthService(db)
    session_token = request.cookies.get(service.settings.session_cookie_name)
    if session_token:
        await service.logout(session_token)

    response.delete_cookie(
        key=service.settings.session_cookie_name,
        path="/",
        samesite="lax",
    )
    return success_response({"logged_out": True, "user_id": str(current_user.id)})


@router.get("/me")
async def me(
    current_user: UserResponse = Depends(require_authenticated_user),
) -> dict:
    return success_response(current_user.model_dump(mode="json"))
