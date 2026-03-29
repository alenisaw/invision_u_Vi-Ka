"""
File: decision_policy.py
Purpose: Explicit score routing and manual-review logic for M6.
"""

from __future__ import annotations

from dataclasses import dataclass

from .calibration import ScoreCalibrator

from .m6_scoring_config import DecisionPolicyConfig


@dataclass(frozen=True)
class DecisionContext:
    """Inputs needed to make the final decision-layer routing."""

    calibrated_score: float
    completeness: float
    confidence: float
    mean_signal_confidence: float
    signal_coverage: float
    model_disagreement: float
    soft_caution_count: int
    caution_flags: tuple[str, ...]
    data_flags: tuple[str, ...]


@dataclass(frozen=True)
class DecisionOutcome:
    """Final routing result of the decision layer."""

    calibrated_score: float
    score_status: str
    confidence_band: str
    manual_review_required: bool
    uncertainty_categories: list[str]
    shortlist_eligible: bool
    review_recommendation: str
    review_reasons: list[str]
    decision_summary: str


def classify_score(context: DecisionContext, policy: DecisionPolicyConfig) -> str:
    """Map the calibrated score into one of the four primary categories."""

    if context.completeness < policy.thresholds.declined_completeness_max:
        return "DECLINED"
    if context.calibrated_score >= policy.thresholds.strong_recommend_min:
        return "STRONG_RECOMMEND"
    if context.calibrated_score >= policy.thresholds.recommend_min:
        return "RECOMMEND"
    if context.calibrated_score >= policy.thresholds.waitlist_min:
        return "WAITLIST"
    return "DECLINED"


def nearest_threshold_margin(score: float, policy: DecisionPolicyConfig) -> float:
    """Measure the distance to the closest class boundary."""

    boundaries = [
        policy.thresholds.strong_recommend_min,
        policy.thresholds.recommend_min,
        policy.thresholds.waitlist_min,
    ]
    return min(abs(score - boundary) for boundary in boundaries)


def instability_radius(context: DecisionContext, policy: DecisionPolicyConfig) -> float:
    """Estimate how much the final score could shift under mild perturbation."""

    low_quality_gap = max(
        0.0,
        policy.uncertainty_policy.low_quality_completeness_max - context.completeness,
    )
    radius = (
        policy.uncertainty_policy.instability_radius_base
        + (1.0 - context.confidence) * policy.uncertainty_policy.instability_confidence_weight
        + context.model_disagreement * policy.uncertainty_policy.instability_disagreement_weight
        + low_quality_gap * policy.uncertainty_policy.instability_low_quality_weight
    )
    return max(0.0, round(radius, 4))


def derive_uncertainty_categories(context: DecisionContext, policy: DecisionPolicyConfig) -> list[str]:
    """Return explicit uncertainty categories for audit and routing."""

    categories: list[str] = []
    if context.confidence < policy.uncertainty_policy.low_confidence_max:
        categories.append("low_confidence")
    if (
        context.mean_signal_confidence < policy.uncertainty_policy.low_signal_confidence_max
        or context.signal_coverage < policy.uncertainty_policy.low_coverage_max
        or context.completeness < policy.uncertainty_policy.low_quality_completeness_max
    ):
        categories.append("missing_or_low_quality_inputs")
    if (
        context.model_disagreement > policy.uncertainty_policy.disagreement_max
        or context.soft_caution_count >= policy.uncertainty_policy.soft_caution_min
    ):
        categories.append("conflicting_signals")
    if nearest_threshold_margin(context.calibrated_score, policy) < policy.uncertainty_policy.narrow_margin_max:
        categories.append("narrow_margin_between_classes")
    if instability_radius(context, policy) >= nearest_threshold_margin(context.calibrated_score, policy):
        categories.append("score_instability_under_perturbation")
    return categories


def should_require_manual_review(
    context: DecisionContext,
    score_status: str,
    uncertainty_categories: list[str],
    policy: DecisionPolicyConfig,
) -> bool:
    """Decide whether the candidate truly needs manual review."""

    if any(flag in policy.uncertainty_policy.hard_flags for flag in context.data_flags):
        if score_status == "DECLINED":
            return context.calibrated_score >= policy.uncertainty_policy.declined_manual_review_score_min
        return True
    if score_status == "DECLINED":
        return False
    if (
        score_status in {"STRONG_RECOMMEND", "RECOMMEND"}
        and "low_confidence" in uncertainty_categories
        and (
            "conflicting_signals" in uncertainty_categories
            or "score_instability_under_perturbation" in uncertainty_categories
        )
    ):
        return True
    if (
        score_status == "WAITLIST"
        and "conflicting_signals" in uncertainty_categories
        and "narrow_margin_between_classes" in uncertainty_categories
    ):
        return True
    if (
        score_status in {"STRONG_RECOMMEND", "RECOMMEND", "WAITLIST"}
        and "missing_or_low_quality_inputs" in uncertainty_categories
        and len(uncertainty_categories) >= policy.uncertainty_policy.manual_review_trigger_count
    ):
        return True
    return False


def build_confidence_band(confidence: float, policy: DecisionPolicyConfig) -> str:
    """Map the continuous confidence score into a compact band."""

    if confidence >= policy.confidence_bands.high_min:
        return "HIGH"
    if confidence >= policy.confidence_bands.medium_min:
        return "MEDIUM"
    return "LOW"


def build_review_recommendation(
    score_status: str,
    confidence_band: str,
    manual_review_required: bool,
    caution_flags: list[str],
    uncertainty_categories: list[str],
    context: DecisionContext,
) -> tuple[str, list[str]]:
    """Build the explicit reviewer routing and short reasons."""

    review_reasons: list[str] = []
    if manual_review_required:
        review_reasons.append("manual review required")
    if context.signal_coverage < 0.60:
        review_reasons.append("low signal coverage")
    if context.mean_signal_confidence < 0.60:
        review_reasons.append("low signal confidence")
    if caution_flags:
        review_reasons.append(", ".join(caution_flags[:2]))
    if uncertainty_categories:
        review_reasons.append(", ".join(uncertainty_categories[:2]))
    if not review_reasons and confidence_band == "HIGH":
        review_reasons.append("high model confidence")

    if manual_review_required:
        return "REQUIRES_MANUAL_REVIEW", review_reasons
    if score_status in {"STRONG_RECOMMEND", "RECOMMEND"} and confidence_band == "HIGH":
        return "FAST_TRACK_REVIEW", review_reasons
    return "STANDARD_REVIEW", review_reasons


def build_decision_summary(
    score_status: str,
    confidence_band: str,
    manual_review_required: bool,
    shortlist_eligible: bool,
    policy: DecisionPolicyConfig,
) -> str:
    """Build a compact UI-friendly decision summary."""

    base_summary = policy.status_summary_templates.get(score_status, "Candidate scored successfully.")
    if manual_review_required:
        return f"{base_summary} Manual review flag is active."
    if shortlist_eligible and confidence_band == "HIGH":
        return f"{base_summary} Fast-track review is reasonable."
    return f"{base_summary} Confidence band: {confidence_band.lower()}."


def apply_decision_policy(
    raw_score: float,
    confidence: float,
    confidence_components: dict[str, float],
    caution_flags: list[str],
    data_flags: list[str],
    completeness: float,
    policy: DecisionPolicyConfig,
    calibrator: ScoreCalibrator,
) -> DecisionOutcome:
    """Apply calibration, class routing, and manual-review policy in one place."""

    calibrated_score = calibrator.transform(raw_score)
    context = DecisionContext(
        calibrated_score=calibrated_score,
        completeness=completeness,
        confidence=confidence,
        mean_signal_confidence=confidence_components.get("mean_signal_confidence", 0.0),
        signal_coverage=confidence_components.get("signal_coverage", 0.0),
        model_disagreement=confidence_components.get("model_disagreement", 0.0),
        soft_caution_count=int(confidence_components.get("soft_caution_count", 0.0)),
        caution_flags=tuple(caution_flags),
        data_flags=tuple(data_flags),
    )
    score_status = classify_score(context, policy)
    uncertainty_categories = derive_uncertainty_categories(context, policy)
    manual_review_required = should_require_manual_review(
        context=context,
        score_status=score_status,
        uncertainty_categories=uncertainty_categories,
        policy=policy,
    )
    confidence_band = build_confidence_band(confidence, policy)
    shortlist_eligible = (not manual_review_required) and score_status in policy.shortlist_eligible_statuses
    review_recommendation, review_reasons = build_review_recommendation(
        score_status=score_status,
        confidence_band=confidence_band,
        manual_review_required=manual_review_required,
        caution_flags=caution_flags,
        uncertainty_categories=uncertainty_categories,
        context=context,
    )
    decision_summary = build_decision_summary(
        score_status=score_status,
        confidence_band=confidence_band,
        manual_review_required=manual_review_required,
        shortlist_eligible=shortlist_eligible,
        policy=policy,
    )
    return DecisionOutcome(
        calibrated_score=calibrated_score,
        score_status=score_status,
        confidence_band=confidence_band,
        manual_review_required=manual_review_required,
        uncertainty_categories=uncertainty_categories,
        shortlist_eligible=shortlist_eligible,
        review_recommendation=review_recommendation,
        review_reasons=review_reasons,
        decision_summary=decision_summary,
    )


# File summary: decision_policy.py
# Separates class assignment, uncertainty categories, and manual-review routing.
