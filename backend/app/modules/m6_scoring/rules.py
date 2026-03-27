"""
File: rules.py
Purpose: Deterministic baseline scoring logic for the M6 module.

Notes:
- Core scores come from structured values, not raw text.
- Confidence and caution handling are delegated to dedicated helpers.
"""

from __future__ import annotations

from typing import Iterable

from .schemas import SignalEnvelope

SCORING_VERSION = "m6-v1"

SUBSCORE_SIGNAL_WEIGHTS: dict[str, dict[str, float]] = {
    "leadership_potential": {
        "leadership_indicators": 0.6,
        "team_leadership": 0.4,
    },
    "growth_trajectory": {
        "growth_trajectory": 0.6,
        "challenges_overcome": 0.4,
    },
    "motivation_clarity": {
        "motivation_clarity": 0.6,
        "goal_specificity": 0.4,
    },
    "initiative_agency": {
        "agency_signals": 0.4,
        "self_started_projects": 0.3,
        "proactivity_examples": 0.3,
    },
    "learning_agility": {
        "learning_agility": 1.0,
    },
    "communication_clarity": {
        "clarity_score": 0.4,
        "structure_score": 0.3,
        "idea_articulation": 0.3,
    },
    "ethical_reasoning": {
        "ethical_reasoning": 0.7,
        "civic_orientation": 0.3,
    },
    "program_fit": {
        "program_alignment": 1.0,
    },
}

SCORING_WEIGHTS: dict[str, float] = {
    "leadership_potential": 0.20,
    "growth_trajectory": 0.18,
    "motivation_clarity": 0.15,
    "initiative_agency": 0.15,
    "learning_agility": 0.12,
    "communication_clarity": 0.10,
    "ethical_reasoning": 0.05,
    "program_fit": 0.05,
}

MODIFIER_SIGNAL_NAMES = {
    "essay_transcript_consistency",
    "claims_evidence_match",
    "ai_writing_risk",
    "voice_consistency",
    "specificity_score",
}

CRITICAL_DATA_FLAGS = {
    "requires_human_review",
    "low_asr_confidence",
    "unclear_segments_high",
    "no_speech_detected",
}

SOFT_CAUTION_FLAGS = {
    "possible_ai_use",
    "low_cross_source_consistency",
    "weak_claim_support",
    "voice_inconsistency",
    "generic_evidence",
}


def clamp_score(value: float) -> float:
    """Clamp any numeric score into the supported score range."""

    return max(0.0, min(1.0, round(value, 4)))


def get_signal_value(envelope: SignalEnvelope, signal_name: str, default: float | None = None) -> float | None:
    """Return a signal value if present."""

    signal = envelope.signals.get(signal_name)
    return default if signal is None else signal.value


def get_signal_confidence(envelope: SignalEnvelope, signal_name: str, default: float | None = None) -> float | None:
    """Return a signal confidence if present."""

    signal = envelope.signals.get(signal_name)
    return default if signal is None else signal.confidence


def get_scoring_signal_names() -> set[str]:
    """Expose the full set of positive scoring signals."""

    signal_names: set[str] = set()
    for signal_map in SUBSCORE_SIGNAL_WEIGHTS.values():
        signal_names.update(signal_map.keys())
    return signal_names


def compute_sub_scores(envelope: SignalEnvelope) -> dict[str, float]:
    """Compute the eight main sub-scores from available structured signals."""

    sub_scores: dict[str, float] = {}
    for sub_score_name, signal_map in SUBSCORE_SIGNAL_WEIGHTS.items():
        weighted_total = 0.0
        present_weight = 0.0

        for signal_name, weight in signal_map.items():
            signal_value = get_signal_value(envelope, signal_name)
            if signal_value is None:
                continue

            weighted_total += signal_value * weight
            present_weight += weight

        sub_scores[sub_score_name] = clamp_score(weighted_total / present_weight) if present_weight else 0.0

    return sub_scores


def compute_baseline_rpi(sub_scores: dict[str, float]) -> float:
    """Compute the deterministic review priority index."""

    review_priority_index = 0.0
    for sub_score_name, weight in SCORING_WEIGHTS.items():
        review_priority_index += sub_scores.get(sub_score_name, 0.0) * weight
    return clamp_score(review_priority_index)


def apply_missing_data_penalty(score: float, completeness: float) -> float:
    """Apply the agreed completeness penalty after score blending."""

    if completeness < 0.50:
        return clamp_score(score * 0.70)
    if completeness < 0.75:
        return clamp_score(score * 0.85)
    return clamp_score(score)


def derive_caution_flags(envelope: SignalEnvelope) -> list[str]:
    """Derive scoring-side caution flags from modifier signals and data flags."""

    caution_flags = list(dict.fromkeys(envelope.data_flags))

    if (get_signal_value(envelope, "ai_writing_risk", 0.0) or 0.0) >= 0.70:
        caution_flags.append("possible_ai_use")
    if (get_signal_value(envelope, "essay_transcript_consistency", 1.0) or 1.0) <= 0.40:
        caution_flags.append("low_cross_source_consistency")
    if (get_signal_value(envelope, "claims_evidence_match", 1.0) or 1.0) <= 0.40:
        caution_flags.append("weak_claim_support")
    if (get_signal_value(envelope, "voice_consistency", 1.0) or 1.0) <= 0.40:
        caution_flags.append("voice_inconsistency")
    if (get_signal_value(envelope, "specificity_score", 1.0) or 1.0) <= 0.35:
        caution_flags.append("generic_evidence")
    if envelope.completeness < 0.50:
        caution_flags.append("low_completeness")

    return list(dict.fromkeys(caution_flags))


def has_critical_data_flags(data_flags: Iterable[str]) -> bool:
    """Check whether data quality already requires a human in the loop."""

    return any(flag in CRITICAL_DATA_FLAGS for flag in data_flags)


def map_recommendation_status(score: float, completeness: float, uncertainty_flag: bool = False) -> str:
    """Map the score into a base recommendation bucket before calibration."""

    if uncertainty_flag:
        return "MANUAL_REVIEW"
    if completeness < 0.50 or score < 0.45:
        return "LOW_SIGNAL"
    if score >= 0.75:
        return "STRONG_RECOMMEND"
    if score >= 0.60:
        return "RECOMMEND"
    return "REVIEW_NEEDED"


# File summary: rules.py
# Holds score mapping, penalties, and status logic for the M6 baseline.
