from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import encrypt_json
from app.modules.m2_intake.schemas import CandidateIntakeRequest
from app.modules.m3_privacy.separator import SeparatedLayers, separate
from app.modules.m9_storage import StorageRepository


class PrivacyService:
    """Separates intake data into 3 privacy layers and persists them."""

    def __init__(self, session: AsyncSession) -> None:
        self.repository = StorageRepository(session)

    async def process(
        self,
        candidate_id: UUID,
        payload: CandidateIntakeRequest,
        *,
        age_eligible: bool | None,
        language_threshold_met: bool | None,
        data_completeness: float,
        data_flags: list[str],
        video_transcript: str | None = None,
        asr_confidence: float | None = None,
        asr_flags: list[str] | None = None,
    ) -> SeparatedLayers:
        """Run 3-layer separation and store results.

        Args:
            candidate_id: Existing candidate UUID (created by M2).
            payload: Raw intake request.
            age_eligible: Pre-computed from M2.
            language_threshold_met: Pre-computed from M2.
            data_completeness: Pre-computed from M2.
            data_flags: Pre-computed from M2.
            video_transcript: Optional ASR transcript from M13.
            asr_confidence: Optional ASR confidence.
            asr_flags: Optional ASR quality flags.

        Returns:
            SeparatedLayers with all three layers.
        """
        layers = separate(
            payload,
            age_eligible=age_eligible,
            language_threshold_met=language_threshold_met,
            data_completeness=data_completeness,
            data_flags=data_flags,
            video_transcript=video_transcript,
            asr_confidence=asr_confidence,
            asr_flags=asr_flags,
        )

        # Layer 1: encrypt and store PII
        encrypted_pii = encrypt_json(layers.layer1.snapshot)
        await self.repository.upsert_candidate_pii(
            candidate_id=candidate_id,
            encrypted_data=encrypted_pii,
        )

        # Layer 2: store operational metadata
        await self.repository.upsert_candidate_metadata(
            candidate_id=candidate_id,
            age_eligible=layers.layer2.age_eligible,
            language_threshold_met=layers.layer2.language_threshold_met,
            language_exam_type=layers.layer2.language_exam_type,
            has_video=layers.layer2.has_video,
            data_completeness=layers.layer2.data_completeness,
            data_flags=layers.layer2.data_flags,
        )

        # Layer 3: store redacted model input
        await self.repository.upsert_candidate_model_input(
            candidate_id=candidate_id,
            video_transcript=layers.layer3.video_transcript,
            essay_text=layers.layer3.essay_text,
            internal_test_answers=layers.layer3.internal_test_answers,
            project_descriptions=layers.layer3.project_descriptions,
            experience_summary=layers.layer3.experience_summary,
            asr_confidence=layers.layer3.asr_confidence,
            asr_flags=layers.layer3.asr_flags,
        )

        # Update pipeline status
        await self.repository.update_pipeline_status(candidate_id, "privacy_done")

        # Audit
        await self.repository.create_audit_log(
            entity_type="candidate",
            entity_id=candidate_id,
            action="privacy_separation_completed",
            actor="system",
            details={
                "data_completeness": layers.layer2.data_completeness,
                "data_flags": layers.layer2.data_flags,
                "has_video": layers.layer2.has_video,
            },
        )

        return layers
