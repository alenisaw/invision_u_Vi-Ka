from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_json
from app.modules.m6_scoring.schemas import CandidateScore as CandidateScorePayload
from app.modules.m7_explainability.schemas import ExplainabilityReport
from app.modules.m8_dashboard.schemas import (
    DashboardCandidateDetailResponse,
    DashboardCandidateListItem,
    DashboardStatsResponse,
    RawCandidateContent,
    ReviewerActionItem,
    ReviewerCandidateIdentity,
)
from app.modules.m9_storage import Candidate, CandidateExplanation, CandidateScore, StorageRepository


logger = logging.getLogger(__name__)

STATUS_KEYS = (
    "STRONG_RECOMMEND",
    "RECOMMEND",
    "WAITLIST",
    "DECLINED",
)


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = StorageRepository(session)

    async def get_stats(self) -> DashboardStatsResponse:
        candidates = await self.repository.list_candidates()
        ranked_scores = await self.repository.list_ranked_scores()

        by_status = {
            "STRONG_RECOMMEND": 0,
            "RECOMMEND": 0,
            "WAITLIST": 0,
            "DECLINED": 0,
        }
        confidence_values: list[float] = []
        pending_review = 0
        shortlisted = 0

        for score in ranked_scores:
            if score.confidence is not None:
                confidence_values.append(score.confidence)

            if bool(score.shortlist_eligible):
                shortlisted += 1

            if bool(score.manual_review_required) or (
                score.review_recommendation == "REQUIRES_MANUAL_REVIEW"
            ):
                pending_review += 1

            if score.recommendation_status in by_status:
                by_status[score.recommendation_status] += 1

        avg_confidence = (
            round(sum(confidence_values) / len(confidence_values), 2)
            if confidence_values
            else 0.0
        )

        return DashboardStatsResponse(
            total_candidates=len(candidates),
            processed=len(ranked_scores),
            shortlisted=shortlisted,
            pending_review=pending_review,
            avg_confidence=avg_confidence,
            by_status=by_status,
        )

    async def list_candidates(self) -> list[DashboardCandidateListItem]:
        ranked_scores = await self.repository.list_ranked_scores()
        return [self._project_candidate_list_item(score) for score in ranked_scores]

    async def get_candidate_detail(
        self,
        candidate_id: UUID,
    ) -> DashboardCandidateDetailResponse:
        candidate = await self.repository.get_candidate_with_related(candidate_id)
        if candidate is None:
            raise ValueError(f"Candidate {candidate_id} not found")

        if candidate.score_record is None:
            raise ValueError(f"Candidate {candidate_id} has no score record")

        if candidate.explanation_record is None:
            raise ValueError(f"Candidate {candidate_id} has no explanation record")

        return self._project_candidate_detail(candidate)

    async def list_shortlist(self) -> list[DashboardCandidateListItem]:
        shortlisted = [
            item
            for item in await self.list_candidates()
            if item.shortlist_eligible
        ]
        shortlisted.sort(
            key=lambda item: (
                item.ranking_position is None,
                item.ranking_position or 0,
                -item.review_priority_index,
            )
        )
        return shortlisted

    def _build_candidate_display_name(self, candidate: Candidate | None) -> str:
        if candidate is None or candidate.pii_record is None:
            return "Unknown Candidate"

        try:
            snapshot = decrypt_json(candidate.pii_record.encrypted_data)
        except Exception:  # pragma: no cover - defensive path for corrupted payloads
            logger.warning("Failed to decrypt candidate PII snapshot", exc_info=True)
            return "Unknown Candidate"

        personal = snapshot.get("personal")
        if not isinstance(personal, dict):
            return "Unknown Candidate"

        first_name = self._clean_text(personal.get("first_name"))
        last_name = self._clean_text(personal.get("last_name"))
        display_name = " ".join(part for part in (first_name, last_name) if part)
        return display_name or "Unknown Candidate"

    def _load_candidate_identity(self, candidate: Candidate) -> ReviewerCandidateIdentity:
        return ReviewerCandidateIdentity(
            candidate_id=candidate.id,
            name=self._build_candidate_display_name(candidate),
        )

    def _project_candidate_list_item(
        self,
        score: CandidateScore,
    ) -> DashboardCandidateListItem:
        candidate = score.candidate
        identity = self._load_candidate_identity(candidate)
        return DashboardCandidateListItem(
            candidate_id=identity.candidate_id,
            name=identity.name,
            selected_program=self._selected_program(candidate, score),
            review_priority_index=float(score.review_priority_index or 0.0),
            recommendation_status=self._recommendation_status(score.recommendation_status),
            confidence=float(score.confidence or 0.0),
            shortlist_eligible=bool(score.shortlist_eligible),
            ranking_position=score.ranking_position,
            top_strengths=self._coerce_string_list(score.top_strengths),
            caution_flags=self._coerce_string_list(score.caution_flags),
            created_at=self._candidate_created_at(candidate, score),
        )

    def _project_candidate_detail(
        self,
        candidate: Candidate,
    ) -> DashboardCandidateDetailResponse:
        if candidate.score_record is None:
            raise ValueError(f"Candidate {candidate.id} has no score record")

        if candidate.explanation_record is None:
            raise ValueError(f"Candidate {candidate.id} has no explanation record")

        identity = self._load_candidate_identity(candidate)
        score = CandidateScorePayload.model_validate(
            self._build_score_payload(candidate, candidate.score_record)
        )
        explanation = ExplainabilityReport.model_validate(
            self._build_explanation_payload(
                candidate,
                candidate.explanation_record,
                score.model_dump(mode="python"),
            )
        )
        raw_content = self._extract_raw_content(candidate)
        audit_logs = [
            ReviewerActionItem(
                id=a.id,
                candidate_id=a.candidate_id,
                reviewer_id=a.reviewer_id,
                action_type=a.action_type,
                previous_status=a.previous_status,
                new_status=a.new_status,
                comment=a.comment,
                created_at=a.created_at,
            )
            for a in (candidate.reviewer_actions or [])
        ]
        return DashboardCandidateDetailResponse(
            candidate_id=identity.candidate_id,
            name=identity.name,
            score=score,
            explanation=explanation,
            raw_content=raw_content,
            audit_logs=audit_logs,
        )

    def _extract_raw_content(self, candidate: Candidate) -> RawCandidateContent | None:
        mi = candidate.model_input_record
        if mi is None:
            return None
        project_list = mi.project_descriptions if isinstance(mi.project_descriptions, list) else []
        return RawCandidateContent(
            essay_text=mi.essay_text or None,
            video_transcript=mi.video_transcript or None,
            project_descriptions=[str(p) for p in project_list if p],
            experience_summary=mi.experience_summary or None,
        )

    def _build_score_payload(
        self,
        candidate: Candidate,
        score_record: CandidateScore,
    ) -> dict[str, Any]:
        payload = score_record.score_payload if isinstance(score_record.score_payload, dict) else {}

        return {
            "candidate_id": payload.get("candidate_id") or score_record.candidate_id,
            "selected_program": self._clean_text(payload.get("selected_program"))
            or self._selected_program(candidate, score_record),
            "program_id": self._clean_text(payload.get("program_id"))
            or self._clean_text(score_record.program_id)
            or "",
            "sub_scores": self._coerce_dict(payload.get("sub_scores"), score_record.sub_scores),
            "program_weight_profile": self._coerce_dict(
                payload.get("program_weight_profile"),
                score_record.program_weight_profile,
            ),
            "review_priority_index": self._coerce_float(
                payload.get("review_priority_index"),
                score_record.review_priority_index,
            ),
            "score_status": self._clean_text(payload.get("score_status")) or "",
            "recommendation_status": self._recommendation_status(
                payload.get("recommendation_status") or score_record.recommendation_status
            ),
            "decision_summary": self._clean_text(payload.get("decision_summary"))
            or self._clean_text(score_record.decision_summary)
            or "",
            "confidence": self._coerce_float(payload.get("confidence"), score_record.confidence),
            "confidence_band": self._clean_text(payload.get("confidence_band"))
            or self._clean_text(score_record.confidence_band)
            or "MEDIUM",
            "manual_review_required": self._coerce_bool(
                payload.get("manual_review_required"),
                score_record.manual_review_required,
            ),
            "human_in_loop_required": self._coerce_bool(
                payload.get("human_in_loop_required"),
                score_record.human_in_loop_required,
            ),
            "uncertainty_flag": self._coerce_bool(
                payload.get("uncertainty_flag"),
                score_record.uncertainty_flag,
            ),
            "shortlist_eligible": self._coerce_bool(
                payload.get("shortlist_eligible"),
                score_record.shortlist_eligible,
            ),
            "review_recommendation": self._clean_text(payload.get("review_recommendation"))
            or self._clean_text(score_record.review_recommendation)
            or "STANDARD_REVIEW",
            "review_reasons": self._coerce_string_list(
                payload.get("review_reasons"),
                score_record.review_reasons,
            ),
            "top_strengths": self._coerce_string_list(
                payload.get("top_strengths"),
                score_record.top_strengths,
            ),
            "top_risks": self._coerce_string_list(
                payload.get("top_risks"),
                score_record.top_risks,
            ),
            "score_delta_vs_baseline": self._coerce_float(
                payload.get("score_delta_vs_baseline"),
                score_record.score_delta_vs_baseline,
            ),
            "ranking_position": payload.get("ranking_position") or score_record.ranking_position,
            "caution_flags": self._coerce_string_list(
                payload.get("caution_flags"),
                score_record.caution_flags,
            ),
            "score_breakdown": self._coerce_dict(
                payload.get("score_breakdown"),
                score_record.score_breakdown,
            ),
            "model_family": self._clean_text(payload.get("model_family"))
            or self._clean_text(score_record.model_family)
            or "",
            "scoring_version": self._clean_text(payload.get("scoring_version"))
            or self._clean_text(score_record.scoring_version)
            or "",
        }

    def _build_explanation_payload(
        self,
        candidate: Candidate,
        explanation_record: CandidateExplanation,
        score_payload: dict[str, Any],
    ) -> dict[str, Any]:
        payload = (
            explanation_record.report_payload
            if isinstance(explanation_record.report_payload, dict)
            else {}
        )

        return {
            "candidate_id": payload.get("candidate_id") or explanation_record.candidate_id,
            "scoring_version": self._clean_text(payload.get("scoring_version"))
            or self._clean_text(explanation_record.scoring_version)
            or self._clean_text(score_payload.get("scoring_version"))
            or "",
            "selected_program": self._clean_text(payload.get("selected_program"))
            or self._selected_program(candidate, candidate.score_record),
            "program_id": self._clean_text(payload.get("program_id"))
            or self._clean_text(explanation_record.program_id)
            or self._clean_text(score_payload.get("program_id"))
            or "",
            "recommendation_status": self._recommendation_status(
                payload.get("recommendation_status")
                or explanation_record.recommendation_status
                or score_payload.get("recommendation_status")
            ),
            "review_priority_index": self._coerce_float(
                payload.get("review_priority_index"),
                explanation_record.review_priority_index,
                score_payload.get("review_priority_index"),
            ),
            "confidence": self._coerce_float(
                payload.get("confidence"),
                explanation_record.confidence,
                score_payload.get("confidence"),
            ),
            "manual_review_required": self._coerce_bool(
                payload.get("manual_review_required"),
                explanation_record.manual_review_required,
                score_payload.get("manual_review_required"),
            ),
            "human_in_loop_required": self._coerce_bool(
                payload.get("human_in_loop_required"),
                explanation_record.human_in_loop_required,
                score_payload.get("human_in_loop_required"),
            ),
            "review_recommendation": self._clean_text(payload.get("review_recommendation"))
            or self._clean_text(explanation_record.review_recommendation)
            or self._clean_text(score_payload.get("review_recommendation"))
            or "STANDARD_REVIEW",
            "summary": self._clean_text(payload.get("summary"))
            or self._clean_text(explanation_record.summary)
            or self._clean_text(score_payload.get("decision_summary"))
            or "",
            "positive_factors": self._coerce_object_list(
                payload.get("positive_factors"),
                explanation_record.positive_factors,
            ),
            "caution_blocks": self._coerce_object_list(
                payload.get("caution_blocks"),
                explanation_record.caution_flags,
            ),
            "reviewer_guidance": self._clean_text(payload.get("reviewer_guidance"))
            or self._clean_text(explanation_record.reviewer_guidance)
            or "",
            "data_quality_notes": self._coerce_string_list(
                payload.get("data_quality_notes"),
                explanation_record.data_quality_notes,
            ),
        }

    def _selected_program(
        self,
        candidate: Candidate | None,
        score: CandidateScore | None,
    ) -> str:
        if candidate is not None:
            selected_program = self._clean_text(candidate.selected_program)
            if selected_program:
                return selected_program

        if score is not None and isinstance(score.score_payload, dict):
            selected_program = self._clean_text(score.score_payload.get("selected_program"))
            if selected_program:
                return selected_program

        return ""

    def _candidate_created_at(
        self,
        candidate: Candidate | None,
        score: CandidateScore,
    ):
        return candidate.created_at if candidate is not None else score.created_at

    def _recommendation_status(self, value: Any) -> str:
        cleaned = self._clean_text(value)
        if cleaned in STATUS_KEYS:
            return cleaned
        return "WAITLIST"

    def _clean_text(self, value: Any) -> str:
        if not isinstance(value, str):
            return ""
        return value.strip()

    def _coerce_bool(self, *values: Any) -> bool:
        for value in values:
            if isinstance(value, bool):
                return value
        return False

    def _coerce_float(self, *values: Any) -> float:
        for value in values:
            if value is None:
                continue
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
        return 0.0

    def _coerce_dict(self, *values: Any) -> dict[str, Any]:
        for value in values:
            if isinstance(value, dict):
                return value
        return {}

    def _coerce_object_list(self, *values: Any) -> list[dict[str, Any]]:
        for value in values:
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return []

    def _coerce_string_list(self, *values: Any) -> list[str]:
        for value in values:
            if not isinstance(value, list):
                continue
            result = [
                item.strip()
                for item in value
                if isinstance(item, str) and item.strip()
            ]
            if result:
                return result
            if value == []:
                return []
        return []
