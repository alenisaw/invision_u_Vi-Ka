"""
File: service.py
Purpose: Reviewer-facing explainability formatting for M7.
"""

from __future__ import annotations

from typing import Any

try:  # pragma: no cover
    from sqlalchemy.ext.asyncio import AsyncSession
    HAS_ASYNC_SESSION = True
except ImportError:  # pragma: no cover
    AsyncSession = Any  # type: ignore[misc,assignment]
    HAS_ASYNC_SESSION = False

from ..m6_scoring.schemas import CandidateScore, SignalEnvelope
from ..m9_storage import StorageRepository
from .evidence import collect_factor_evidence
from .factors import caution_block, factor_summary, factor_title
from .schemas import (
    ExplainabilityCautionFlag,
    ExplainabilityFactor,
    ExplainabilityInput,
    ExplainabilityReport,
    ExplainabilitySignalContext,
    FactorBlock,
)


class _CompatibilityScoringService:
    """Test seam kept for compatibility with older M7 service expectations."""

    def score_candidate(self, envelope: SignalEnvelope) -> CandidateScore:
        raise RuntimeError("ExplainabilityService expects a precomputed CandidateScore.")


class ExplainabilityService:
    """Formats M6 outputs into an auditable explanation bundle."""

    def __init__(self, session: AsyncSession | None = None) -> None:
        self.session = session
        self.scoring_service = _CompatibilityScoringService()
        self.repository = (
            StorageRepository(session)
            if HAS_ASYNC_SESSION and isinstance(session, AsyncSession)
            else None
        )

    def build_report(self, handoff: ExplainabilityInput) -> ExplainabilityReport:
        factor_blocks = [
            FactorBlock(
                factor=factor.factor,
                title=factor_title(factor.factor),
                summary=factor_summary(factor),
                score=factor.score,
                score_contribution=factor.score_contribution,
                evidence=collect_factor_evidence(handoff, factor.factor),
            )
            for factor in handoff.positive_factors[:3]
        ]
        caution_blocks = [caution_block(flag) for flag in handoff.caution_flags]
        return ExplainabilityReport(
            candidate_id=handoff.candidate_id,
            scoring_version=handoff.scoring_version,
            selected_program=handoff.selected_program,
            program_id=handoff.program_id,
            recommendation_status=handoff.recommendation_status,
            review_priority_index=handoff.review_priority_index,
            confidence=handoff.confidence,
            manual_review_required=handoff.manual_review_required,
            human_in_loop_required=handoff.human_in_loop_required,
            review_recommendation=handoff.review_recommendation,
            summary=self._build_summary(handoff, factor_blocks, caution_blocks),
            positive_factors=factor_blocks,
            caution_blocks=caution_blocks,
            reviewer_guidance=self._build_reviewer_guidance(handoff, caution_blocks),
            data_quality_notes=handoff.data_quality_notes,
        )

    async def generate(
        self,
        candidate_id,
        envelope: SignalEnvelope,
        score: CandidateScore,
    ) -> ExplainabilityReport:
        """Build and persist explainability output from the supplied M6 score."""

        handoff = self._build_handoff_from_score(envelope, score)
        report = self.build_report(handoff)
        await self._persist_report(candidate_id, report)
        return report

    async def _persist_report(self, candidate_id, report: ExplainabilityReport) -> None:
        """Persist the explanation bundle when a real async DB session is available."""

        if self.repository is None:
            return

        report_payload = report.model_dump(mode="json")
        await self.repository.upsert_candidate_explanation(
            candidate_id=candidate_id,
            scoring_version=report.scoring_version,
            program_id=report.program_id or None,
            recommendation_status=report.recommendation_status,
            review_priority_index=report.review_priority_index,
            confidence=report.confidence,
            manual_review_required=report.manual_review_required,
            human_in_loop_required=report.human_in_loop_required,
            review_recommendation=report.review_recommendation,
            summary=report.summary,
            positive_factors=report_payload["positive_factors"],
            caution_flags=report_payload["caution_blocks"],
            data_quality_notes=report.data_quality_notes,
            reviewer_guidance=report.reviewer_guidance,
            report_payload=report_payload,
        )
        await self.repository.create_audit_log(
            entity_type="candidate",
            entity_id=candidate_id,
            action="explainability_generated",
            actor="system",
            details={
                "recommendation_status": report.recommendation_status,
                "review_recommendation": report.review_recommendation,
                "manual_review_required": report.manual_review_required,
            },
        )

    def _build_handoff_from_score(self, envelope: SignalEnvelope, score: CandidateScore) -> ExplainabilityInput:
        positive_factors = [
            ExplainabilityFactor(
                factor=sub_score_name,
                sub_score=sub_score_name,
                score=sub_score_value,
                score_contribution=min(score.program_weight_profile.get(sub_score_name, 0.0) * sub_score_value, 0.25),
            )
            for sub_score_name, sub_score_value in sorted(
                score.sub_scores.items(),
                key=lambda item: item[1] * score.program_weight_profile.get(item[0], 0.0),
                reverse=True,
            )[:3]
        ]
        caution_flags = [
            ExplainabilityCautionFlag(
                flag=flag,
                severity="critical" if flag in {"low_completeness", "no_structured_signals", "requires_human_review"} else "warning",
                reason=flag.replace("_", " "),
            )
            for flag in score.caution_flags
        ]
        signal_context = {
            signal_name: ExplainabilitySignalContext(**signal.model_dump())
            for signal_name, signal in envelope.signals.items()
        }
        return ExplainabilityInput(
            candidate_id=score.candidate_id,
            scoring_version=score.scoring_version,
            selected_program=score.selected_program,
            program_id=score.program_id,
            recommendation_status=score.recommendation_status,
            review_priority_index=score.review_priority_index,
            confidence=score.confidence,
            uncertainty_flag=score.uncertainty_flag,
            manual_review_required=score.manual_review_required,
            human_in_loop_required=score.human_in_loop_required,
            review_recommendation=score.review_recommendation,
            review_reasons=list(score.review_reasons),
            sub_scores=dict(score.sub_scores),
            score_breakdown=dict(score.score_breakdown),
            positive_factors=positive_factors,
            caution_flags=caution_flags,
            signal_context=signal_context,
            data_quality_notes=[
                f"confidence_band={score.confidence_band}",
                f"score_status={score.score_status}",
                f"shortlist_eligible={score.shortlist_eligible}",
            ],
        )

    def _build_summary(
        self,
        handoff: ExplainabilityInput,
        factor_blocks: list[FactorBlock],
        caution_blocks: list,
    ) -> str:
        strengths = ", ".join(block.title for block in factor_blocks[:2]) or "moderate signal support"
        if handoff.manual_review_required:
            return f"The candidate shows {strengths}, but the case still requires manual review because of uncertainty or data quality limits."
        if caution_blocks:
            return f"The candidate shows {strengths}, with caution flags that should be reviewed alongside the score."
        return f"The candidate shows {strengths}, and the current evidence looks stable enough for standard committee review."

    def _build_reviewer_guidance(self, handoff: ExplainabilityInput, caution_blocks: list) -> str:
        if handoff.manual_review_required:
            return "Review evidence consistency, input quality, and caution flags before making a final committee decision."
        if caution_blocks:
            return "Use the score as a working signal, but inspect the caution blocks before final routing."
        if handoff.review_recommendation == "FAST_TRACK_REVIEW":
            return "The case is suitable for faster committee review, while still checking the supporting evidence."
        return "Use the explanation bundle as decision support; the final outcome remains with the committee."


# File summary: service.py
# Builds summary, evidence-backed strengths, caution blocks, and reviewer guidance from M6 output.
