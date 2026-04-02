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
    "initiative_agency": "Инициативность и ответственность",
    "learning_agility": "Обучаемость",
    "communication_clarity": "Ясность коммуникации",
    "ethical_reasoning": "Этическое мышление",
    "program_fit": "Соответствие программе",
}

SOURCE_LABELS = {
    "essay": "эссе",
    "video_transcript": "транскрипция видео",
    "project_descriptions": "описания проектов",
    "experience_summary": "описание опыта",
    "internal_test_answers": "ответы внутреннего теста",
}

CAUTION_POLICY: dict[str, tuple[ExplainabilitySeverity, str, str]] = {
    "possible_ai_use": (
        "warning",
        "Риск недостоверности или использования ИИ",
        "Сверьте эссе, транскрипцию, проекты и внутренние ответы перед финальным решением.",
    ),
    "authenticity_or_ai_risk": (
        "warning",
        "Риск недостоверности или использования ИИ",
        "Сверьте эссе, транскрипцию, проекты и внутренние ответы перед финальным решением.",
    ),
    "low_cross_source_consistency": (
        "warning",
        "Несогласованность источников",
        "Проверьте, совпадают ли ключевые факты между эссе, видео и проектами.",
    ),
    "weak_claim_support": (
        "warning",
        "Слабая доказательная база",
        "Проверьте, подкреплены ли важные заявления конкретными примерами.",
    ),
    "voice_inconsistency": (
        "warning",
        "Расхождение письменной и устной версии",
        "Сравните письменный и устный нарратив кандидата перед итоговым решением.",
    ),
    "generic_evidence": (
        "advisory",
        "Слишком общие формулировки",
        "На финальном рассмотрении запросите больше конкретных примеров и результатов.",
    ),
    "low_completeness": (
        "critical",
        "Недостаточно данных",
        "Не трактуйте отсутствие материалов как слабый потенциал. Кейс нужно разбирать вручную.",
    ),
    "no_structured_signals": (
        "critical",
        "Недостаточно структурированных сигналов",
        "Считайте кейс недообоснованным и отправьте его на ручную проверку.",
    ),
    "requires_human_review": (
        "critical",
        "Требуется ручная проверка",
        "Комиссия должна отдельно проверить кейс перед маршрутизацией.",
    ),
    "missing_essay": (
        "warning",
        "Нет текстового эссе",
        "Учтите, что письменная мотивация кандидата отсутствует и часть сигналов строится по другим источникам.",
    ),
    "essay_replaced_by_video_transcript": (
        "advisory",
        "Эссе заменено транскрипцией",
        "Учтите, что письменное поле не заполнено, и мотивационный нарратив собран из видеотранскрипции.",
    ),
    "missing_video": (
        "warning",
        "Нет видеоинтервью",
        "Учтите, что устная часть профиля отсутствует, поэтому голосовые сигналы ограничены.",
    ),
    "missing_video_transcript": (
        "warning",
        "Нет транскрипции видео",
        "Если видео было загружено, проверьте ASR и при необходимости повторите обработку вручную.",
    ),
    "missing_project_descriptions": (
        "advisory",
        "Нет описаний проектов",
        "Попросите у кандидата или комиссии дополнительные примеры практической работы.",
    ),
    "low_profile_completeness": (
        "warning",
        "Профиль заполнен неполно",
        "Финальное решение принимайте только после проверки недостающих материалов.",
    ),
    "asr_processing_failed": (
        "warning",
        "Ошибка обработки видео",
        "Проверьте источник видео и при необходимости запустите транскрибацию повторно.",
    ),
    "low_asr_confidence": (
        "warning",
        "Низкая уверенность ASR",
        "Относитесь к транскрипции как к вспомогательному источнику и перепроверьте спорные места.",
    ),
}


def factor_title(factor_name: str) -> str:
    return FACTOR_TITLES.get(factor_name, factor_name.replace("_", " ").title())


def factor_summary(factor: ExplainabilityFactor) -> str:
    return (
        f"{factor_title(factor.factor)} входит в число ключевых положительных драйверов "
        f"(оценка {factor.score:.2f}, вклад {factor.score_contribution:.2f}), "
        "поэтому этот фактор заметно влияет на итоговую рекомендацию, а не служит фоновым контекстом."
    )


def source_label(source_name: str) -> str:
    return SOURCE_LABELS.get(source_name, source_name.replace("_", " "))


def caution_block(flag: ExplainabilityCautionFlag) -> CautionBlock:
    severity, title, suggested_action = CAUTION_POLICY.get(
        flag.flag,
        (
            flag.severity,
            flag.flag.replace("_", " ").title(),
            "Проверьте этот предупреждающий сигнал на финальном рассмотрении комиссии.",
        ),
    )
    return CautionBlock(
        flag=flag.flag,
        severity=severity,
        title=title,
        summary=flag.reason,
        suggested_action=suggested_action,
    )
