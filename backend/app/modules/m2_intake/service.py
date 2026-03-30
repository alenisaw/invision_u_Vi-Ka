from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime, timezone
import hashlib
import hmac
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import encrypt_json
from app.modules.m2_intake.schemas import CandidateIntakeRequest, CandidateIntakeResponse
from app.modules.m9_storage import StorageRepository


LANGUAGE_THRESHOLDS: dict[str, float] = {
    "IELTS": 5.5,
    "TOEFL": 72.0,
    "DUOLINGO": 95.0,
}


class CandidateIntakeService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = StorageRepository(session)

    async def intake_candidate(self, payload: CandidateIntakeRequest) -> CandidateIntakeResponse:
        dedupe_key = self._build_dedupe_key(payload)
        candidate = (
            await self.repository.get_candidate_by_dedupe_key(dedupe_key)
            if dedupe_key
            else None
        )
        if candidate is None:
            candidate = await self.repository.create_candidate(
                selected_program=payload.academic.selected_program,
                pipeline_status="pending",
                dedupe_key=dedupe_key,
            )
        else:
            candidate.selected_program = payload.academic.selected_program
            candidate.pipeline_status = "pending"
            await self.repository.flush()

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
        return self._compact_mapping(
            {
                "personal": payload.personal.model_dump(mode="json", exclude_none=True),
                "contacts": payload.contacts.model_dump(mode="json", exclude_none=True),
                "parents": payload.parents.model_dump(mode="json", exclude_none=True),
                "address": payload.address.model_dump(mode="json", exclude_none=True),
                "social_status": payload.social_status.model_dump(
                    mode="json",
                    exclude_none=True,
                ),
            }
        )

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
        checks = [
            bool(payload.personal.last_name),
            bool(payload.personal.first_name),
            bool(payload.personal.date_of_birth),
            bool(payload.academic.selected_program),
            bool(payload.content.essay_text),
            bool(payload.content.video_url),
            bool(payload.content.project_descriptions),
            bool(payload.content.experience_summary),
            bool(payload.internal_test.answers),
            bool(payload.contacts.phone),
        ]
        return round(sum(checks) / len(checks), 2)

    def _build_data_flags(self, payload: CandidateIntakeRequest) -> list[str]:
        flags: list[str] = []

        if not payload.content.essay_text:
            flags.append("missing_essay")
        if not payload.content.video_url:
            flags.append("missing_video")
        if not payload.internal_test.answers:
            flags.append("missing_internal_test")
        if not payload.content.project_descriptions:
            flags.append("missing_project_descriptions")
        if self._compute_completeness(payload) < 0.6:
            flags.append("low_profile_completeness")

        return flags

    def _compact_mapping(self, payload: dict[str, Any]) -> dict[str, Any]:
        compacted: dict[str, Any] = {}
        for key, value in payload.items():
            if value is None:
                continue
            if isinstance(value, dict):
                nested = self._compact_mapping(value)
                if nested:
                    compacted[key] = nested
                continue
            if isinstance(value, list):
                filtered_list = [item for item in value if item not in (None, "", [], {})]
                if filtered_list:
                    compacted[key] = filtered_list
                continue
            if value == "":
                continue
            compacted[key] = value
        return compacted

    def _build_dedupe_key(self, payload: CandidateIntakeRequest) -> str | None:
        dedupe_source = self._normalized_dedupe_source(payload)
        if not dedupe_source:
            return None
        secret = get_settings().pii_encryption_key.encode("utf-8")
        return hmac.new(
            secret,
            dedupe_source.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _normalized_dedupe_source(self, payload: CandidateIntakeRequest) -> str | None:
        iin = (payload.personal.iin or "").strip()
        if iin:
            return f"iin:{iin}"

        document_parts = [
            (payload.personal.citizenship or "").strip().upper(),
            (payload.personal.document_type or "").strip().upper(),
            (payload.personal.document_no or "").strip().upper(),
        ]
        if any(document_parts):
            normalized = "|".join(document_parts).strip("|")
            if normalized:
                return f"document:{normalized}"
        return None
