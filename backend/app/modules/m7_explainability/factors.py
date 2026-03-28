"""
File: factors.py
Purpose: Human-readable factor and caution formatting helpers for M7.
"""

from __future__ import annotations

from .schemas import CautionBlock, ExplainabilityCautionFlag, ExplainabilityFactor, ExplainabilitySeverity

FACTOR_TITLES = {
    "leadership_potential": "Лидерский потенциал",
    "growth_trajectory": "Траектория роста",
    "motivation_clarity": "Ясность мотивации",
    "initiative_agency": "Инициативность и ownership",
    "learning_agility": "Learning agility",
    "communication_clarity": "Ясность коммуникации",
    "ethical_reasoning": "Этичность и зрелость решений",
    "program_fit": "Совпадение с программой",
}

CAUTION_POLICY: dict[str, tuple[ExplainabilitySeverity, str, str]] = {
    "possible_ai_use": ("warning", "Признаки неаутентичности текста", "Сверить эссе с видеотранскриптом и внутренним тестом."),
    "low_cross_source_consistency": ("warning", "Несостыковки между источниками", "Проверить ключевые тезисы по всем доступным источникам."),
    "weak_claim_support": ("warning", "Слабая доказательная база", "Попросить комиссию отдельно проверить конкретику примеров."),
    "voice_inconsistency": ("warning", "Стиль письма и речи расходится", "Сравнить письменные и устные ответы на предмет аутентичности."),
    "generic_evidence": ("advisory", "Слишком общие формулировки", "Проверить, есть ли у кандидата реальные конкретные кейсы."),
    "low_completeness": ("critical", "Недостаточно данных", "Решение лучше принимать только после ручной проверки."),
    "no_structured_signals": ("critical", "Нет структурированных сигналов", "M5 вернул слишком мало сигнальной информации для надежного решения."),
}


def factor_title(factor_name: str) -> str:
    """Return a human-readable title for one factor."""

    return FACTOR_TITLES.get(factor_name, factor_name.replace("_", " ").title())


def factor_summary(factor: ExplainabilityFactor) -> str:
    """Build a short factor summary for reviewer UI."""

    return (
        f"{factor_title(factor.factor)}: score {factor.score:.2f}, "
        f"contribution {factor.score_contribution:.2f}."
    )


def caution_block(flag: ExplainabilityCautionFlag) -> CautionBlock:
    """Normalize one caution flag into a reviewer-facing block."""

    severity, title, suggested_action = CAUTION_POLICY.get(
        flag.flag,
        (flag.severity, flag.flag.replace("_", " ").title(), "Проверить кейс вручную при финальном решении."),
    )
    return CautionBlock(
        flag=flag.flag,
        severity=severity,
        title=title,
        summary=flag.reason,
        suggested_action=suggested_action,
    )


# File summary: factors.py
# Maps M6 factor names and caution flags into reviewer-facing titles, severities, and actions.
