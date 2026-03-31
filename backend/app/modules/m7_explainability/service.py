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
from ..m6_scoring.service import ScoringService
from .evidence import collect_factor_evidence, collect_factor_signal_contexts
from .factors import caution_block, factor_summary, factor_title
from .schemas import ExplainabilityInput, ExplainabilityReport, FactorBlock


class ExplainabilityService:
    """Formats M6 outputs into an auditable explanation bundle."""

    def __init__(self, session: AsyncSession | None = None) -> None:
        self.session = session
        self.scoring_service = ScoringService()
        self.repository = None
        if HAS_ASYNC_SESSION and isinstance(session, AsyncSession):
            from ..m9_storage import StorageRepository

            self.repository = StorageRepository(session)

    def build_report(self, handoff: ExplainabilityInput) -> ExplainabilityReport:
        factor_blocks = [
            FactorBlock(
                factor=factor.factor,
                title=factor_title(factor.factor),
                summary=self._build_factor_summary(handoff, factor),
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

        handoff = self.scoring_service.build_explainability_input(envelope, score)
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

    def _build_summary(
        self,
        handoff: ExplainabilityInput,
        factor_blocks: list[FactorBlock],
        caution_blocks: list,
    ) -> str:
        strengths = ", ".join(block.title for block in factor_blocks[:2]) or "moderate signal support"
        evidence_sources = sorted(
            {
                item.source
                for block in factor_blocks[:2]
                for item in block.evidence
                if item.source
            }
        )
        source_clause = (
            f" Supporting evidence comes primarily from {', '.join(evidence_sources[:2])}."
            if evidence_sources
            else ""
        )
        if handoff.manual_review_required:
            return (
                f"The candidate shows {strengths}, but the case still requires manual review because the current evidence is incomplete or unstable."
                f"{source_clause}"
            )
        if caution_blocks:
            caution_titles = ", ".join(block.title for block in caution_blocks[:2])
            return (
                f"The candidate shows {strengths}, but reviewers should weigh caution signals such as {caution_titles} before making a final decision."
                f"{source_clause}"
            )
        return f"The candidate shows {strengths}, and the current evidence looks stable enough for standard committee review.{source_clause}"

    def _build_reviewer_guidance(self, handoff: ExplainabilityInput, caution_blocks: list) -> str:
        if handoff.manual_review_required:
            return "Review evidence consistency, input quality, and caution flags before making a final committee decision. Incomplete evidence should be treated as insufficient data, not as proof of low potential."
        if caution_blocks:
            return "Use the score as a working signal, but inspect the caution blocks before final routing."
        if handoff.review_recommendation == "FAST_TRACK_REVIEW":
            return "The case is suitable for faster committee review, while still checking the supporting evidence."
        return "Use the explanation bundle as decision support; the final outcome remains with the committee."

    def _build_factor_summary(self, handoff: ExplainabilityInput, factor) -> str:
        contexts = collect_factor_signal_contexts(handoff, factor.factor)
        if not contexts:
            return factor_summary(factor)

        direct_support = 0
        indirect_support = 0
        sources: list[str] = []
        reason_fragments: list[str] = []

        for _, signal in contexts:
            if "direct behavioral evidence" in signal.reasoning.lower():
                direct_support += 1
            elif "indirect behavioral evidence" in signal.reasoning.lower():
                indirect_support += 1
            for source_name in signal.source:
                if source_name not in sources:
                    sources.append(source_name)
            if signal.reasoning and signal.reasoning not in reason_fragments:
                reason_fragments.append(signal.reasoning)

        support_label = "direct evidence" if direct_support else "indirect evidence"
        if direct_support and indirect_support:
            support_label = "direct and indirect evidence"
        source_label = ", ".join(sources[:3]) if sources else "available narrative sources"
        rationale = reason_fragments[0] if reason_fragments else factor_summary(factor)
        return (
            f"{factor_title(factor.factor)} materially influenced the recommendation "
            f"(score {factor.score:.2f}, contribution {factor.score_contribution:.2f}). "
            f"It is supported by {support_label} from {source_label}. {rationale}"
        )


