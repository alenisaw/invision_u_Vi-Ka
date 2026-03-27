"""
File: service.py
Purpose: Main orchestration entry point for the M6 scoring module.

Notes:
- The service keeps the public API small and explicit.
- The module should work before the ML layer is trained.
"""

from __future__ import annotations

import math

import numpy as np

try:
    from scipy.stats import spearmanr
    from sklearn.metrics import mean_absolute_error, mean_squared_error, precision_recall_fscore_support, r2_score
except ImportError:  # pragma: no cover
    spearmanr = None
    mean_absolute_error = None
    mean_squared_error = None
    precision_recall_fscore_support = None
    r2_score = None

from .confidence import assess_score_confidence
from .ml_model import HybridScoringModel
from ..m7_explainability.schemas import (
    ExplainabilityCautionFlag,
    ExplainabilityFactor,
    ExplainabilityInput,
    ExplainabilitySignalContext,
)
from .ranker import rank_scores
from .rules import (
    SCORING_VERSION,
    SCORING_WEIGHTS,
    SOFT_CAUTION_FLAGS,
    apply_missing_data_penalty,
    clamp_score,
    compute_baseline_rpi,
    compute_sub_scores,
    derive_caution_flags,
    map_recommendation_status,
)
from .schemas import CandidateScore, LabeledEnvelope, SignalEnvelope
from .synthetic_data import generate_synthetic_dataset


def _feature_builder(envelope: SignalEnvelope) -> tuple[dict[str, float], float]:
    """Build the shared feature primitives used by both rules and ML."""

    sub_scores = compute_sub_scores(envelope)
    baseline_rpi = compute_baseline_rpi(sub_scores)
    return sub_scores, baseline_rpi


class ScoringService:
    """Primary entry point for M6 scoring operations."""

    def __init__(
        self,
        scoring_version: str = SCORING_VERSION,
        blend_weight_ml: float = 0.20,
        model_family: str = "gbr",
    ) -> None:
        self.scoring_version = scoring_version
        self.blend_weight_ml = blend_weight_ml
        self.blend_weight_baseline = clamp_score(1.0 - blend_weight_ml)
        self.model_family = model_family
        self.ml_model = HybridScoringModel(model_family=model_family)

    def fit(self, labeled_samples: list[LabeledEnvelope]) -> None:
        """Train the optional ML refinement layer."""

        self.ml_model.fit(labeled_samples, _feature_builder)

    def train_on_synthetic(self, sample_count: int = 300, seed: int = 42) -> list[LabeledEnvelope]:
        """Train the ML layer on generated development data."""

        labeled_samples = generate_synthetic_dataset(sample_count=sample_count, seed=seed, profile_mix="balanced")
        self.fit(labeled_samples)
        return labeled_samples

    def evaluate_on_synthetic(
        self,
        train_sample_count: int = 300,
        test_sample_count: int = 120,
        seed: int = 42,
        test_profile_mix: str = "balanced",
    ) -> dict[str, float | int]:
        """Train on synthetic data and evaluate on a holdout synthetic split."""

        if mean_absolute_error is None or precision_recall_fscore_support is None or spearmanr is None:
            raise RuntimeError("evaluation dependencies are not available in the current environment")

        train_samples = generate_synthetic_dataset(sample_count=train_sample_count, seed=seed, profile_mix="balanced")
        test_samples = generate_synthetic_dataset(
            sample_count=test_sample_count,
            seed=seed + 1,
            profile_mix=test_profile_mix,
        )
        self.fit(train_samples)

        true_scores: list[float] = []
        predicted_scores: list[float] = []
        true_statuses: list[str] = []
        predicted_statuses: list[str] = []
        confidence_bands: list[str] = []
        review_recommendations: list[str] = []
        uncertainty_flags: list[bool] = []

        for labeled_sample in test_samples:
            score = self.score_candidate(labeled_sample.envelope)
            true_scores.append(labeled_sample.target_rpi)
            predicted_scores.append(score.review_priority_index)
            confidence_bands.append(score.confidence_band)
            review_recommendations.append(score.review_recommendation)
            uncertainty_flags.append(score.uncertainty_flag)
            true_statuses.append(
                map_recommendation_status(
                    score=labeled_sample.target_rpi,
                    completeness=labeled_sample.envelope.completeness,
                    uncertainty_flag=False,
                )
            )
            predicted_statuses.append(score.recommendation_status)

        precision, recall, f1_score, _ = precision_recall_fscore_support(
            true_statuses,
            predicted_statuses,
            average="macro",
            zero_division=0,
        )
        correlation = spearmanr(np.asarray(true_scores), np.asarray(predicted_scores)).correlation
        top_k = min(10, len(test_samples))
        true_top = set(np.argsort(true_scores)[-top_k:].tolist())
        predicted_top = set(np.argsort(predicted_scores)[-top_k:].tolist())

        rmse = math.sqrt(mean_squared_error(true_scores, predicted_scores))
        return {
            "train_sample_count": train_sample_count,
            "test_sample_count": test_sample_count,
            "test_profile_mix": test_profile_mix,
            "mae": round(float(mean_absolute_error(true_scores, predicted_scores)), 4),
            "rmse": round(float(rmse), 4),
            "r2": round(float(r2_score(true_scores, predicted_scores)), 4),
            "macro_precision": round(float(precision), 4),
            "macro_recall": round(float(recall), 4),
            "macro_f1": round(float(f1_score), 4),
            "spearman_rank_correlation": round(float(correlation if correlation == correlation else 0.0), 4),
            "top_k_overlap": round(len(true_top & predicted_top) / top_k, 4),
            "manual_review_rate": round(float(np.mean(uncertainty_flags)), 4),
            "high_confidence_rate": round(float(np.mean([band == "HIGH" for band in confidence_bands])), 4),
            "fast_track_rate": round(
                float(np.mean([review == "FAST_TRACK_REVIEW" for review in review_recommendations])),
                4,
            ),
        }

    def build_explainability_input(self, envelope: SignalEnvelope) -> ExplainabilityInput:
        """Prepare the future M6 -> M7 handoff payload."""

        score = self.score_candidate(envelope)
        positive_factors = self._build_positive_factors(score)
        caution_flags = self._build_caution_items(score.caution_flags)
        signal_context = {
            signal_name: ExplainabilitySignalContext(**signal.model_dump())
            for signal_name, signal in envelope.signals.items()
        }
        data_quality_notes = [
            f"completeness={score.score_breakdown.get('completeness', 0.0):.2f}",
            f"signal_coverage={score.score_breakdown.get('signal_coverage', 0.0):.2f}",
            f"mean_signal_confidence={score.score_breakdown.get('mean_signal_confidence', 0.0):.2f}",
        ]

        return ExplainabilityInput(
            candidate_id=score.candidate_id,
            scoring_version=score.scoring_version,
            recommendation_status=score.recommendation_status,
            review_priority_index=score.review_priority_index,
            confidence=score.confidence,
            uncertainty_flag=score.uncertainty_flag,
            sub_scores=score.sub_scores,
            score_breakdown=score.score_breakdown,
            positive_factors=positive_factors,
            caution_flags=caution_flags,
            signal_context=signal_context,
            data_quality_notes=data_quality_notes,
        )

    def score_candidate(self, envelope: SignalEnvelope) -> CandidateScore:
        """Score one candidate from the canonical signal envelope."""

        sub_scores, baseline_rpi = _feature_builder(envelope)
        caution_flags = derive_caution_flags(envelope)
        ml_rpi = self.ml_model.predict(envelope, sub_scores, baseline_rpi)

        blended_rpi = clamp_score(
            baseline_rpi * self.blend_weight_baseline + ml_rpi * self.blend_weight_ml
        )
        final_rpi = apply_missing_data_penalty(blended_rpi, envelope.completeness)

        confidence, uncertainty_flag, confidence_components = assess_score_confidence(
            envelope=envelope,
            baseline_rpi=baseline_rpi,
            ml_rpi=ml_rpi,
            caution_flags=caution_flags,
        )
        recommendation_status = self._calibrate_recommendation_status(
            score=final_rpi,
            confidence=confidence,
            completeness=envelope.completeness,
            uncertainty_flag=uncertainty_flag,
            caution_flags=caution_flags,
        )

        shortlist_eligible = recommendation_status in {"STRONG_RECOMMEND", "RECOMMEND"}
        confidence_band = self._build_confidence_band(confidence)
        review_recommendation, review_reasons = self._build_review_recommendation(
            recommendation_status=recommendation_status,
            confidence_band=confidence_band,
            uncertainty_flag=uncertainty_flag,
            caution_flags=caution_flags,
            confidence_components=confidence_components,
        )
        return CandidateScore(
            candidate_id=envelope.candidate_id,
            sub_scores=sub_scores,
            review_priority_index=final_rpi,
            recommendation_status=recommendation_status,
            confidence=confidence,
            confidence_band=confidence_band,
            uncertainty_flag=uncertainty_flag,
            shortlist_eligible=shortlist_eligible,
            review_recommendation=review_recommendation,
            review_reasons=review_reasons,
            caution_flags=caution_flags,
            score_breakdown={
                "baseline_rpi": baseline_rpi,
                "ml_rpi": ml_rpi,
                "blended_rpi": blended_rpi,
                **confidence_components,
            },
            model_family=self.model_family,
            scoring_version=self.scoring_version,
        )

    def score_batch(self, envelopes: list[SignalEnvelope]) -> list[CandidateScore]:
        """Score and rank a batch of candidates."""

        scored_candidates = [self.score_candidate(envelope) for envelope in envelopes]
        return rank_scores(scored_candidates)

    def _build_positive_factors(self, score: CandidateScore) -> list[ExplainabilityFactor]:
        """Prepare the top score contributors for the future explainability layer."""

        factors = []
        for sub_score_name, sub_score_value in score.sub_scores.items():
            contribution = clamp_score(sub_score_value * SCORING_WEIGHTS.get(sub_score_name, 0.0))
            factors.append(
                ExplainabilityFactor(
                    factor=sub_score_name,
                    sub_score=sub_score_name,
                    score=sub_score_value,
                    score_contribution=contribution,
                )
            )

        factors.sort(key=lambda factor: factor.score_contribution, reverse=True)
        return factors[:3]

    def _build_caution_items(self, caution_flags: list[str]) -> list[ExplainabilityCautionFlag]:
        """Normalize caution flags for the future explainability layer."""

        return [
            ExplainabilityCautionFlag(
                flag=flag,
                severity="advisory",
                reason="derived from modifier signals or data flags",
            )
            for flag in caution_flags
        ]

    def _build_confidence_band(self, confidence: float) -> str:
        """Map the confidence score into a compact UI-friendly band."""

        if confidence >= 0.80:
            return "HIGH"
        if confidence >= 0.62:
            return "MEDIUM"
        return "LOW"

    def _calibrate_recommendation_status(
        self,
        score: float,
        confidence: float,
        completeness: float,
        uncertainty_flag: bool,
        caution_flags: list[str],
    ) -> str:
        """Calibrate the recommendation status after score blending."""

        if uncertainty_flag:
            return "MANUAL_REVIEW"

        base_status = map_recommendation_status(score=score, completeness=completeness, uncertainty_flag=False)
        soft_cautions = sum(1 for flag in caution_flags if flag in SOFT_CAUTION_FLAGS)

        if base_status == "LOW_SIGNAL":
            return "LOW_SIGNAL"
        if base_status == "STRONG_RECOMMEND" and confidence < 0.62:
            return "RECOMMEND"
        if base_status == "RECOMMEND" and score >= 0.72 and confidence >= 0.82 and soft_cautions <= 1:
            return "STRONG_RECOMMEND"
        if base_status == "RECOMMEND" and confidence < 0.52:
            return "REVIEW_NEEDED"
        if base_status == "REVIEW_NEEDED" and score >= 0.57 and confidence >= 0.78 and soft_cautions <= 1 and completeness >= 0.75:
            return "RECOMMEND"
        return base_status

    def _build_review_recommendation(
        self,
        recommendation_status: str,
        confidence_band: str,
        uncertainty_flag: bool,
        caution_flags: list[str],
        confidence_components: dict[str, float],
    ) -> tuple[str, list[str]]:
        """Build compact UI-facing review guidance."""

        review_reasons: list[str] = []
        if uncertainty_flag:
            review_reasons.append("uncertainty threshold triggered")
        if confidence_components.get("signal_coverage", 1.0) < 0.60:
            review_reasons.append("low signal coverage")
        if confidence_components.get("mean_signal_confidence", 1.0) < 0.60:
            review_reasons.append("low signal confidence")
        if caution_flags:
            review_reasons.append(", ".join(caution_flags[:2]))
        if not review_reasons and confidence_band == "HIGH":
            review_reasons.append("high model confidence")

        if uncertainty_flag:
            return "REQUIRES_MANUAL_REVIEW", review_reasons
        if recommendation_status in {"STRONG_RECOMMEND", "RECOMMEND"} and confidence_band == "HIGH":
            return "FAST_TRACK_REVIEW", review_reasons
        return "STANDARD_REVIEW", review_reasons


# File summary: service.py
# Exposes the main scoring entry points and keeps M6 orchestration compact.
