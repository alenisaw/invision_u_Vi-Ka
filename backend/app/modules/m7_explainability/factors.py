"""
File: factors.py
Purpose: Human-readable factor and caution formatting helpers for M7.
"""

from __future__ import annotations

from .schemas import CautionBlock, ExplainabilityCautionFlag, ExplainabilityFactor, ExplainabilitySeverity


FACTOR_TITLES = {
    "leadership_potential": "Leadership Potential",
    "growth_trajectory": "Growth Trajectory",
    "motivation_clarity": "Motivation Clarity",
    "initiative_agency": "Initiative and Ownership",
    "learning_agility": "Learning Agility",
    "communication_clarity": "Communication Clarity",
    "ethical_reasoning": "Ethical Reasoning",
    "program_fit": "Program Fit",
}

CAUTION_POLICY: dict[str, tuple[ExplainabilitySeverity, str, str]] = {
    "possible_ai_use": ("warning", "Possible authenticity mismatch", "Compare essay claims against transcript and internal test answers."),
    "low_cross_source_consistency": ("warning", "Cross-source inconsistency", "Check whether core claims remain stable across essay, transcript, and projects."),
    "weak_claim_support": ("warning", "Weak evidence support", "Review whether major claims are backed by concrete examples."),
    "voice_inconsistency": ("warning", "Written-spoken style mismatch", "Compare the written and spoken narrative before making a final decision."),
    "generic_evidence": ("advisory", "Generic narrative evidence", "Ask for more concrete examples during committee review."),
    "low_completeness": ("critical", "Insufficient information", "Do not rely on the score without manual review of missing inputs."),
    "no_structured_signals": ("critical", "No structured signal coverage", "Treat the case as under-evidenced and review manually."),
    "requires_human_review": ("critical", "Manual review required", "A reviewer should inspect the case before final routing."),
}


def factor_title(factor_name: str) -> str:
    return FACTOR_TITLES.get(factor_name, factor_name.replace("_", " ").title())


def factor_summary(factor: ExplainabilityFactor) -> str:
    return f"{factor_title(factor.factor)} is one of the main positive drivers (score {factor.score:.2f}, contribution {factor.score_contribution:.2f})."


def caution_block(flag: ExplainabilityCautionFlag) -> CautionBlock:
    severity, title, suggested_action = CAUTION_POLICY.get(
        flag.flag,
        (flag.severity, flag.flag.replace("_", " ").title(), "Review the caution flag during final committee assessment."),
    )
    return CautionBlock(
        flag=flag.flag,
        severity=severity,
        title=title,
        summary=flag.reason,
        suggested_action=suggested_action,
    )


