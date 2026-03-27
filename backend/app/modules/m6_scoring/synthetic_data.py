"""
File: synthetic_data.py
Purpose: Generate compact synthetic samples for M6 training and sanity checks.

Notes:
- Synthetic labels are for development and validation only.
- Keep generation logic aligned with the rule baseline so the model refines, not replaces.
"""

from __future__ import annotations

import random
from uuid import uuid4

from .rules import apply_missing_data_penalty, compute_baseline_rpi, compute_sub_scores, get_signal_value
from .schemas import LabeledEnvelope, SignalEnvelope, SignalPayload

PROFILE_PRESETS = {
    "strong": {
        "core_range": (0.72, 0.94),
        "confidence_range": (0.75, 0.95),
        "modifier_range": (0.10, 0.30),
        "completeness_range": (0.85, 1.00),
        "missing_probability": 0.03,
    },
    "balanced": {
        "core_range": (0.52, 0.78),
        "confidence_range": (0.60, 0.85),
        "modifier_range": (0.25, 0.55),
        "completeness_range": (0.70, 0.90),
        "missing_probability": 0.08,
    },
    "weak": {
        "core_range": (0.18, 0.48),
        "confidence_range": (0.45, 0.72),
        "modifier_range": (0.45, 0.85),
        "completeness_range": (0.50, 0.80),
        "missing_probability": 0.10,
    },
    "incomplete": {
        "core_range": (0.30, 0.72),
        "confidence_range": (0.35, 0.75),
        "modifier_range": (0.35, 0.80),
        "completeness_range": (0.25, 0.60),
        "missing_probability": 0.35,
    },
    "risky": {
        "core_range": (0.45, 0.82),
        "confidence_range": (0.40, 0.75),
        "modifier_range": (0.55, 0.95),
        "completeness_range": (0.60, 0.88),
        "missing_probability": 0.12,
    },
}

PROFILE_MIXES = {
    "balanced": {
        "strong": 0.22,
        "balanced": 0.34,
        "weak": 0.18,
        "incomplete": 0.13,
        "risky": 0.13,
    },
    "stress": {
        "strong": 0.08,
        "balanced": 0.20,
        "weak": 0.24,
        "incomplete": 0.24,
        "risky": 0.24,
    },
}

SCORING_SIGNALS = [
    "leadership_indicators",
    "team_leadership",
    "growth_trajectory",
    "challenges_overcome",
    "motivation_clarity",
    "goal_specificity",
    "agency_signals",
    "self_started_projects",
    "proactivity_examples",
    "learning_agility",
    "clarity_score",
    "structure_score",
    "idea_articulation",
    "ethical_reasoning",
    "civic_orientation",
    "program_alignment",
]

MODIFIER_SIGNALS = [
    "essay_transcript_consistency",
    "claims_evidence_match",
    "ai_writing_risk",
    "voice_consistency",
    "specificity_score",
]


def _clip(value: float) -> float:
    return max(0.0, min(1.0, round(value, 4)))


def _sample_signal_payload(value: float, confidence: float, signal_name: str) -> SignalPayload:
    """Create one compact signal payload."""

    return SignalPayload(
        value=_clip(value),
        confidence=_clip(confidence),
        source=["synthetic_profile"],
        evidence=[f"synthetic:{signal_name}"],
        reasoning="synthetic fixture",
    )


def _generate_envelope(profile_type: str, randomizer: random.Random) -> SignalEnvelope:
    """Generate one synthetic envelope using the chosen profile preset."""

    preset = PROFILE_PRESETS[profile_type]
    signals: dict[str, SignalPayload] = {}

    for signal_name in SCORING_SIGNALS:
        if randomizer.random() < preset["missing_probability"]:
            continue

        signal_value = randomizer.uniform(*preset["core_range"])
        signal_confidence = randomizer.uniform(*preset["confidence_range"])
        signals[signal_name] = _sample_signal_payload(signal_value, signal_confidence, signal_name)

    for signal_name in MODIFIER_SIGNALS:
        signal_value = randomizer.uniform(*preset["modifier_range"])
        signal_confidence = randomizer.uniform(*preset["confidence_range"])

        if signal_name != "ai_writing_risk":
            signal_value = 1.0 - signal_value if profile_type in {"strong", "balanced"} else signal_value
        signals[signal_name] = _sample_signal_payload(signal_value, signal_confidence, signal_name)

    data_flags: list[str] = []
    if profile_type == "incomplete":
        data_flags.append("requires_human_review")
    if profile_type == "risky":
        data_flags.append("low_asr_confidence")

    return SignalEnvelope(
        candidate_id=uuid4(),
        signal_schema_version="v1",
        m5_model_version=f"synthetic-{profile_type}",
        completeness=_clip(randomizer.uniform(*preset["completeness_range"])),
        data_flags=data_flags,
        signals=signals,
    )


def _label_envelope(envelope: SignalEnvelope, randomizer: random.Random) -> float:
    """Create a target label that stays close to the baseline with a few refinements."""

    sub_scores = compute_sub_scores(envelope)
    baseline_rpi = compute_baseline_rpi(sub_scores)

    leadership_boost = 0.04 if sub_scores.get("leadership_potential", 0.0) >= 0.80 else 0.0
    growth_boost = 0.03 if sub_scores.get("growth_trajectory", 0.0) >= 0.75 else 0.0
    learning_boost = 0.02 if sub_scores.get("learning_agility", 0.0) >= 0.78 else 0.0
    ai_penalty = -0.08 if (get_signal_value(envelope, "ai_writing_risk", 0.0) or 0.0) >= 0.70 else 0.0
    consistency_penalty = -0.04 if (get_signal_value(envelope, "essay_transcript_consistency", 1.0) or 1.0) <= 0.35 else 0.0
    completeness_penalty = -0.05 if envelope.completeness < 0.45 else 0.0
    noise = randomizer.uniform(-0.03, 0.03)

    adjusted_rpi = (
        baseline_rpi
        + leadership_boost
        + growth_boost
        + learning_boost
        + ai_penalty
        + consistency_penalty
        + completeness_penalty
        + noise
    )
    return apply_missing_data_penalty(_clip(adjusted_rpi), envelope.completeness)


def generate_synthetic_dataset(
    sample_count: int = 300,
    seed: int = 42,
    profile_mix: str = "balanced",
) -> list[LabeledEnvelope]:
    """Generate synthetic labeled envelopes for model training or sanity checks."""

    if sample_count <= 0:
        raise ValueError("sample_count must be positive")
    if profile_mix not in PROFILE_MIXES:
        raise ValueError(f"unsupported profile_mix: {profile_mix}")

    randomizer = random.Random(seed)
    profile_types = list(PROFILE_MIXES[profile_mix].keys())
    profile_weights = list(PROFILE_MIXES[profile_mix].values())
    labeled_samples: list[LabeledEnvelope] = []

    for _ in range(sample_count):
        profile_type = randomizer.choices(profile_types, weights=profile_weights, k=1)[0]
        envelope = _generate_envelope(profile_type, randomizer)
        labeled_samples.append(
            LabeledEnvelope(
                envelope=envelope,
                profile_type=profile_type,
                target_rpi=_label_envelope(envelope, randomizer),
            )
        )

    return labeled_samples


def build_reference_fixtures() -> dict[str, SignalEnvelope]:
    """Create a small deterministic set of envelopes for tests and demos."""

    randomizer = random.Random(7)
    return {
        "strong": _generate_envelope("strong", randomizer),
        "balanced": _generate_envelope("balanced", randomizer),
        "weak": _generate_envelope("weak", randomizer),
        "incomplete": _generate_envelope("incomplete", randomizer),
        "risky": _generate_envelope("risky", randomizer),
    }


# File summary: synthetic_data.py
# Generates compact synthetic fixtures and labeled samples for M6 work.
