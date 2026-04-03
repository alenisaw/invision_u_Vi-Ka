from __future__ import annotations

import hashlib
import logging
from collections.abc import Iterable
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import encrypt_json
from app.modules.m2_intake.schemas import CandidateIntakeRequest, CandidateIntakeResponse
from app.modules.m9_storage import StorageRepository

logger = logging.getLogger(__name__)


LANGUAGE_THRESHOLDS: dict[str, float] = {
    "IELTS": 5.5,
    "TOEFL": 72.0,
    "DUOLINGO": 95.0,
}


class CandidateIntakeService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = StorageRepository(session)

    @staticmethod
    def _compute_dedupe_key(payload: CandidateIntakeRequest) -> str:
        raw = (
            f"{payload.personal.first_name.strip().lower()}"
            f"|{payload.personal.last_name.strip().lower()}"
            f"|{payload.personal.date_of_birth.isoformat()}"
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    async def intake_candidate(self, payload: CandidateIntakeRequest) -> CandidateIntakeResponse:
        dedupe_key = self._compute_dedupe_key(payload)
        existing = await self.repository.find_candidate_by_dedupe_key(dedupe_key)
        if existing is not None:
            logger.info(
                "Dedup: removing previous candidate %s (dedupe_key=%s)",
                existing.id,
                dedupe_key[:12],
            )
            await self.repository.delete_candidate(existing.id)

        candidate = await self.repository.create_candidate(
            selected_program=payload.academic.selected_program,
            pipeline_status="pending",
            dedupe_key=dedupe_key,
        )

        encrypted_snapshot = encrypt_json(self._build_secure_snapshot(payload))
        await self.repository.upsert_candidate_pii(
            candidate_id=candidate.id,
            encrypted_data=encrypted_snapshot,
        )

        completeness = self._compute_completeness(payload)
        data_flags = self._build_data_flags(payload)

        await self.repository.upsert_candidate_metadata(
            candidate_id=candidate.id,
            age_eligible=self._check_age_eligibility(payload.personal.date_of_birth),
            language_threshold_met=self._check_language_threshold(
                payload.academic.language_exam_type,
                payload.academic.language_score,
            ),
            language_exam_type=payload.academic.language_exam_type,
            has_video=bool(payload.content.video_url),
            data_completeness=completeness,
            data_flags=data_flags,
        )

        await self.repository.create_audit_log(
            entity_type="candidate",
            entity_id=candidate.id,
            action="candidate_intake_received",
            actor="system",
            details={
                "pipeline_status": candidate.pipeline_status,
                "selected_program": candidate.selected_program,
                "has_video": bool(payload.content.video_url),
                "completeness": completeness,
            },
        )
        await self.repository.commit()

        return CandidateIntakeResponse(candidate_id=str(candidate.id))

    def _build_secure_snapshot(self, payload: CandidateIntakeRequest) -> dict[str, Any]:
        snapshot = payload.model_dump(
            mode="json",
            include={"personal", "contacts", "parents", "address", "social_status"},
        )
        address = snapshot.get("address")
        if isinstance(address, dict) and not any(bool(value) for value in address.values()):
            snapshot.pop("address", None)
        return snapshot

    def _check_age_eligibility(self, date_of_birth: date) -> bool:
        today = datetime.now(timezone.utc).date()
        age = today.year - date_of_birth.year - (
            (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
        )
        return age >= 16

    def _check_language_threshold(
        self,
        exam_type: str | None,
        score: float | None,
    ) -> bool | None:
        if exam_type is None or score is None:
            return None

        threshold = LANGUAGE_THRESHOLDS.get(exam_type.upper())
        if threshold is None:
            return None
        return score >= threshold

    def _compute_completeness(self, payload: CandidateIntakeRequest) -> float:
        has_narrative_source = bool(
            payload.content.essay_text
            or payload.content.transcript_text
            or payload.content.video_url
        )
        has_language_signal = bool(
            payload.academic.language_exam_type and payload.academic.language_score is not None
        )
        checks = [
            bool(payload.personal.last_name),
            bool(payload.personal.first_name),
            bool(payload.personal.date_of_birth),
            bool(payload.academic.selected_program),
            bool(payload.content.video_url),
            bool(payload.contacts.email),
            has_narrative_source,
            has_language_signal,
        ]
        return round(sum(checks) / len(checks), 2)

    def _build_data_flags(self, payload: CandidateIntakeRequest) -> list[str]:
        flags: list[str] = []

        has_transcript_substitute = bool(payload.content.transcript_text or payload.content.video_url)
        if not payload.content.essay_text and not has_transcript_substitute:
            flags.append("missing_essay")
        if not payload.content.video_url:
            flags.append("missing_video")
        if self._compute_completeness(payload) < 0.6:
            flags.append("low_profile_completeness")

        return flags
