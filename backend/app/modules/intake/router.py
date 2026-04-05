from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.modules.intake.schemas import CandidateIntakeRequest
from app.modules.intake.service import CandidateIntakeService
from app.schemas.common import success_response


router = APIRouter(prefix="/api/v1/candidates", tags=["candidates"])


@router.post("/intake")
async def intake_candidate(
    payload: CandidateIntakeRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = CandidateIntakeService(db)
    result = await service.intake_candidate(payload)
    return success_response(result.model_dump())
