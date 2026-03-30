"""
File: rules.py
Purpose: Deterministic baseline scoring logic for the M6 module.
"""

from __future__ import annotations

from typing import Iterable

from .m6_scoring_config import (
    CRITICAL_DATA_FLAGS,
    MODIFIER_SIGNAL_NAMES,
    SCORING_VERSION,
    SOFT_CAUTION_FLAGS,
    STATUS_THRESHOLDS,
    SUBSCORE_SIGNAL_WEIGHTS,
)
from .program_policy import get_program_weight_profile
from .schemas import SignalEnvelope


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
    """Compute sub-scores from available structured signals.

    Sub-scores with zero present signals are omitted from the result
    so that ``compute_baseline_rpi`` can renormalize weights and avoid
    treating absent data as 0.0 (the completeness penalty already
    handles missing-data downgrading).
    """

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

        if present_weight:
            sub_scores[sub_score_name] = clamp_score(weighted_total / present_weight)

    return sub_scores


def compute_baseline_rpi(sub_scores: dict[str, float], program_id: str | None = None) -> float:
    """Compute the deterministic review priority index.

    Only sub-scores actually present in *sub_scores* contribute.  Their
    weights are renormalized so that the RPI reflects the quality of the
    data we *do* have rather than being dragged towards zero by absent
    dimensions.  The completeness penalty applied later already accounts
    for missing data.
    """

    scoring_weights = get_program_weight_profile(program_id)
    weighted_total = 0.0
    present_weight_sum = 0.0
    for sub_score_name, weight in scoring_weights.items():
        if sub_score_name in sub_scores:
            weighted_total += sub_scores[sub_score_name] * weight
            present_weight_sum += weight

    if not present_weight_sum:
        return 0.0
    return clamp_score(weighted_total / present_weight_sum)


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


def map_recommendation_status(score: float, completeness: float) -> str:
    """Map the score into one of the four primary score categories."""

    if completeness < STATUS_THRESHOLDS["declined_completeness_max"]:
        return "DECLINED"
    if score >= STATUS_THRESHOLDS["strong_recommend_min"]:
        return "STRONG_RECOMMEND"
    if score >= STATUS_THRESHOLDS["recommend_min"]:
        return "RECOMMEND"
    if score >= STATUS_THRESHOLDS["waitlist_min"]:
        return "WAITLIST"
    return "DECLINED"


