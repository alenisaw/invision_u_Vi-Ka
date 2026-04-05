from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.profile.assembler import assemble
from app.modules.profile.schemas import CandidateProfile
from app.modules.storage import StorageRepository


class ProfileService:
    """Loads Layer 2 + Layer 3 from storage and assembles a CandidateProfile."""

    def __init__(self, session: AsyncSession) -> None:
        self.repository = StorageRepository(session)

    async def build(self, candidate_id: UUID) -> CandidateProfile:
        """Build a unified profile for the given candidate.

        Raises:
            ValueError: If candidate or required layers are missing.
        """
        candidate = await self.repository.get_candidate_with_related(candidate_id)
        if candidate is None:
            raise ValueError(f"Candidate {candidate_id} not found")

        if candidate.metadata_record is None:
            raise ValueError(f"Candidate {candidate_id} missing metadata (Layer 2)")

        if candidate.model_input_record is None:
            raise ValueError(f"Candidate {candidate_id} missing model input (Layer 3)")

        profile = assemble(
            candidate=candidate,
            metadata=candidate.metadata_record,
            model_input=candidate.model_input_record,
        )

        await self.repository.update_pipeline_status(candidate_id, "profile_ready")

        await self.repository.create_audit_log(
            entity_type="candidate",
            entity_id=candidate_id,
            action="profile_assembled",
            actor="system",
            details={
                "completeness": profile.completeness,
                "data_flags": profile.data_flags,
                "selected_program": profile.selected_program,
            },
        )

        return profile
