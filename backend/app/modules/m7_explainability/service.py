"""
File: service.py
Purpose: Reviewer-facing explainability formatting for M7.
"""

from __future__ import annotations

from typing import Any

try:  # pragma: no cover
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError:  # pragma: no cover
    AsyncSession = Any  # type: ignore[misc,assignment]

from ..m6_scoring.service import ScoringService
from ..m6_scoring.schemas import CandidateScore, SignalEnvelope
from .evidence import collect_factor_evidence
from .factors import caution_block, factor_summary, factor_title
from .schemas import ExplainabilityInput, ExplainabilityReport, FactorBlock


class ExplainabilityService:
    """Formats M6 outputs into an auditable explanation bundle."""

    def __init__(self, session: AsyncSession | None = None) -> None:
        self.session = session
        self.scoring_service = ScoringService()

    def build_report(self, handoff: ExplainabilityInput) -> ExplainabilityReport:
        """Convert the M6 handoff payload into reviewer-facing explanation output."""

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
        summary = self._build_summary(handoff, factor_blocks, caution_blocks)
        reviewer_guidance = self._build_reviewer_guidance(handoff, caution_blocks)

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
            summary=summary,
            positive_factors=factor_blocks,
            caution_blocks=caution_blocks,
            reviewer_guidance=reviewer_guidance,
            data_quality_notes=handoff.data_quality_notes,
        )

    async def generate(self, candidate_id, envelope: SignalEnvelope, score: CandidateScore) -> ExplainabilityReport:
        """Build explainability output from M6 data without altering numeric decisions."""

        handoff = self.scoring_service.build_explainability_input(envelope)
        return self.build_report(handoff)

    def _build_summary(self, handoff: ExplainabilityInput, factor_blocks, caution_blocks) -> str:
        """Create one compact summary sentence for dashboard use."""

        strengths = ", ".join(block.title for block in factor_blocks[:2]) or "умеренные сигналы"
        if handoff.manual_review_required:
            return f"Кандидат показывает {strengths}, но требует ручной проверки из-за качества или конфликтности сигналов."
        if caution_blocks:
            return f"Кандидат показывает {strengths}; решение можно принимать с учетом отмеченных caution-флагов."
        return f"Кандидат показывает {strengths}; сигналы выглядят достаточно стабильными для текущего решения."

    def _build_reviewer_guidance(self, handoff: ExplainabilityInput, caution_blocks) -> str:
        """Create one short reviewer instruction based on routing and caution policy."""

        if handoff.manual_review_required:
            return "Провести ручную проверку доказательств, качества источников и согласованности между ответами."
        if caution_blocks:
            return "Проверить caution-блоки, но основной score можно использовать как рабочий ориентир комиссии."
        if handoff.review_recommendation == "FAST_TRACK_REVIEW":
            return "Кейс можно рассматривать в ускоренном порядке без снижения внимания к evidence."
        return "Использовать explanation как support-слой, не заменяя финальное решение комиссии."


# File summary: service.py
# Builds summary, evidence-backed strengths, caution blocks, and reviewer guidance from M6 handoff.
