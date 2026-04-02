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
from .factors import caution_block, factor_summary, factor_title, source_label
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
        strengths = ", ".join(block.title for block in factor_blocks[:2]) or "умеренно подтвержденный потенциал"
        evidence_sources = sorted(
            {
                item.source
                for block in factor_blocks[:2]
                for item in block.evidence
                if item.source
            }
        )
        source_clause = (
            f" Основные подтверждения пришли из источников: {', '.join(self._format_sources(evidence_sources[:2]))}."
            if evidence_sources
            else ""
        )
        if handoff.manual_review_required:
            return (
                f"Кандидат показывает сильные стороны по направлениям {strengths}, "
                "но кейс все еще требует ручной проверки, потому что текущая доказательная база неполная или нестабильная."
                f"{source_clause}"
            )
        if caution_blocks:
            caution_titles = ", ".join(block.title for block in caution_blocks[:2])
            return (
                f"Кандидат демонстрирует сильные стороны по направлениям {strengths}, "
                f"однако перед финальным решением комиссии нужно отдельно взвесить сигналы риска: {caution_titles}."
                f"{source_clause}"
            )
        return (
            f"Кандидат демонстрирует сильные стороны по направлениям {strengths}, "
            "а текущая доказательная база выглядит достаточно устойчивой для стандартного рассмотрения комиссией."
            f"{source_clause}"
        )

    def _build_reviewer_guidance(self, handoff: ExplainabilityInput, caution_blocks: list) -> str:
        if handoff.manual_review_required:
            return (
                "Проверьте согласованность доказательств, качество входных материалов и предупреждающие флаги "
                "перед финальным решением комиссии. Неполные данные нужно трактовать как нехватку информации, "
                "а не как автоматическое подтверждение слабого потенциала."
            )
        if caution_blocks:
            return (
                "Используйте score как рабочий ориентир, но обязательно пройдитесь по блокам предупреждений "
                "до окончательной маршрутизации кандидата."
            )
        if handoff.review_recommendation == "FAST_TRACK_REVIEW":
            return (
                "Кейс подходит для ускоренного рассмотрения, но подтверждающие факты и примеры "
                "все равно стоит быстро перепроверить."
            )
        return (
            "Используйте explainability как опору для решения: итоговый вердикт остается за комиссией, "
            "но ключевые положительные факторы и предупреждения уже структурированы для обсуждения."
        )

    def _build_factor_summary(self, handoff: ExplainabilityInput, factor) -> str:
        contexts = collect_factor_signal_contexts(handoff, factor.factor)
        if not contexts:
            return factor_summary(factor)

        direct_support = 0
        indirect_support = 0
        sources: list[str] = []
        for _, signal in contexts:
            if "direct behavioral evidence" in signal.reasoning.lower():
                direct_support += 1
            elif "indirect behavioral evidence" in signal.reasoning.lower():
                indirect_support += 1
            for source_name in signal.source:
                if source_name not in sources:
                    sources.append(source_name)

        support_label = "прямыми наблюдаемыми примерами" if direct_support else "косвенными подтверждениями"
        if direct_support and indirect_support:
            support_label = "комбинацией прямых и косвенных подтверждений"
        source_names = ", ".join(self._format_sources(sources[:3])) if sources else "доступными материалами кандидата"
        return (
            f"{factor_title(factor.factor)} заметно повлиял на рекомендацию "
            f"(оценка {factor.score:.2f}, вклад {factor.score_contribution:.2f}). "
            f"Фактор подтверждается {support_label} из источников: {source_names}. {factor_summary(factor)}"
        )

    @staticmethod
    def _format_sources(source_names: list[str]) -> list[str]:
        formatted: list[str] = []
        for raw_name in source_names:
            if not raw_name:
                continue
            parts = [source_label(part.strip()) for part in raw_name.split(",") if part.strip()]
            if parts:
                formatted.append(", ".join(parts))
        return formatted
