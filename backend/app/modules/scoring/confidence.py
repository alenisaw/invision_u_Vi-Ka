"""
File: confidence.py
Purpose: Confidence and uncertainty helpers for the scoring stage.
"""

from __future__ import annotations

from .scoring_config import CONFIDENCE_RULES, CONFIDENCE_WEIGHTS
from .rules import (
    MODIFIER_SIGNAL_NAMES,
    SOFT_CAUTION_FLAGS,
    clamp_score,
    get_scoring_signal_names,
    get_signal_confidence,
    has_critical_data_flags,
)
from .schemas import SignalEnvelope


def calculate_signal_coverage(envelope: SignalEnvelope) -> float:
    """Measure how much of the positive scoring surface is available."""

    scoring_signal_names = get_scoring_signal_names()
    present_signal_names = {signal_name for signal_name in scoring_signal_names if signal_name in envelope.signals}
    return clamp_score(len(present_signal_names) / len(scoring_signal_names))


def calculate_mean_signal_confidence(envelope: SignalEnvelope) -> float:
    """Average confidence across the signals that matter for scoring."""

    confidence_values: list[float] = []
    for signal_name in sorted(get_scoring_signal_names() | MODIFIER_SIGNAL_NAMES):
        signal_confidence = get_signal_confidence(envelope, signal_name)
        if signal_confidence is not None:
            confidence_values.append(signal_confidence)

    if not confidence_values:
        return 0.0
    return clamp_score(sum(confidence_values) / len(confidence_values))


def assess_score_confidence(
    envelope: SignalEnvelope,
    baseline_rpi: float,
    ml_rpi: float,
    caution_flags: list[str],
) -> tuple[float, bool, dict[str, float]]:
    """Compute a compact confidence score and uncertainty marker."""

    signal_coverage = calculate_signal_coverage(envelope)
    mean_signal_confidence = calculate_mean_signal_confidence(envelope)
    model_disagreement = clamp_score(abs(baseline_rpi - ml_rpi))
    score_strength = clamp_score((baseline_rpi + ml_rpi) / 2.0)
    soft_caution_count = sum(1 for flag in caution_flags if flag in SOFT_CAUTION_FLAGS)
    hard_uncertainty = (
        has_critical_data_flags(envelope.data_flags)
        or envelope.completeness < CONFIDENCE_RULES["hard_uncertainty_completeness_max"]
    )

    risk_score = 0
    if mean_signal_confidence < CONFIDENCE_RULES["mean_signal_confidence_risk_min"]:
        risk_score += 1
    if signal_coverage < CONFIDENCE_RULES["signal_coverage_risk_min"]:
        risk_score += 1
    if envelope.completeness < CONFIDENCE_RULES["completeness_risk_min"]:
        risk_score += 1
    if model_disagreement > CONFIDENCE_RULES["model_disagreement_risk_min"]:
        risk_score += 1
    if soft_caution_count >= CONFIDENCE_RULES["soft_caution_risk_min"]:
        risk_score += 1
    if (
        score_strength < CONFIDENCE_RULES["weak_score_strength_max"]
        and signal_coverage < CONFIDENCE_RULES["weak_score_coverage_max"]
    ):
        risk_score += 1

    confidence_score = (
        mean_signal_confidence * CONFIDENCE_WEIGHTS["mean_signal_confidence"]
        + signal_coverage * CONFIDENCE_WEIGHTS["signal_coverage"]
        + envelope.completeness * CONFIDENCE_WEIGHTS["completeness"]
        + (1.0 - model_disagreement) * CONFIDENCE_WEIGHTS["agreement"]
        + score_strength * CONFIDENCE_WEIGHTS["score_strength"]
    )
    if (
        signal_coverage >= CONFIDENCE_RULES["high_confidence_bonus_coverage_min"]
        and mean_signal_confidence >= CONFIDENCE_RULES["high_confidence_bonus_signal_confidence_min"]
    ):
        confidence_score += CONFIDENCE_RULES["high_confidence_bonus_value"]
    if soft_caution_count:
        confidence_score -= min(
            CONFIDENCE_RULES["soft_caution_penalty_max"],
            soft_caution_count * CONFIDENCE_RULES["soft_caution_penalty_step"],
        )

    components = {
        "mean_signal_confidence": mean_signal_confidence,
        "signal_coverage": signal_coverage,
        "completeness": clamp_score(envelope.completeness),
        "model_disagreement": model_disagreement,
        "score_strength": score_strength,
        "soft_caution_count": float(soft_caution_count),
        "risk_score": float(risk_score),
        "hard_uncertainty": 1.0 if hard_uncertainty else 0.0,
    }
    return (
        clamp_score(confidence_score),
        hard_uncertainty or risk_score >= CONFIDENCE_RULES["manual_review_risk_score_min"],
        components,
    )

