"""
File: service.py
Purpose: Main orchestration entry point for the scoring stage.
"""

from __future__ import annotations

import math
import logging
from time import perf_counter

import numpy as np

from .calibration import ScoreCalibrator
from .decision_policy import (
    apply_decision_policy,
)
from .scoring_config import (
    DEFAULT_BLEND_WEIGHT_ML,
    DEFAULT_CALIBRATION_MODE,
    DEFAULT_MODEL_FAMILY,
    DecisionPolicyConfig,
    SUPPORTED_SIGNAL_SCHEMA_VERSIONS,
    STATUS_ORDER,
    build_policy_config,
)
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
from .program_policy import get_program_weight_profile, normalize_program_id
from ..explanation.schemas import (
    ExplanationCautionFlag,
    ExplanationFactor,
    ExplanationInput,
    ExplanationSignalContext,
)
from .ranker import rank_scores
from .rules import (
    SCORING_VERSION,
    apply_missing_data_penalty,
    clamp_score,
    compute_baseline_rpi,
    compute_sub_scores,
    derive_caution_flags,
    map_recommendation_status,
)
from .schemas import CandidateScore, LabeledEnvelope, SignalEnvelope
from .synthetic_data import generate_synthetic_dataset

logger = logging.getLogger(__name__)


def _feature_builder(envelope: SignalEnvelope) -> tuple[dict[str, float], float]:
    """Build the shared feature primitives used by both rules and ML."""

    sub_scores = compute_sub_scores(envelope)
    baseline_rpi = compute_baseline_rpi(sub_scores, program_id=envelope.program_id or envelope.selected_program)
    return sub_scores, baseline_rpi


class ScoringService:
    """Primary entry point for scoring operations."""

    def __init__(
        self,
        scoring_version: str = SCORING_VERSION,
        blend_weight_ml: float | None = None,
        model_family: str | None = None,
        calibration_mode: str | None = None,
        policy_config: DecisionPolicyConfig | None = None,
    ) -> None:
        self.policy_config = policy_config or build_policy_config()
        self.scoring_version = scoring_version
        self.blend_weight_ml = blend_weight_ml if blend_weight_ml is not None else self.policy_config.blend_weight_ml
        self.blend_weight_baseline = clamp_score(1.0 - self.blend_weight_ml)
        self.model_family = model_family or self.policy_config.model_family or DEFAULT_MODEL_FAMILY
        self.calibration_mode = calibration_mode or self.policy_config.calibration_mode or DEFAULT_CALIBRATION_MODE
        self.ml_model = HybridScoringModel(model_family=self.model_family)
        self.calibrator = ScoreCalibrator(mode=self.calibration_mode)

    def fit(self, labeled_samples: list[LabeledEnvelope]) -> None:
        """Train the optional ML refinement layer."""

        self.ml_model.fit(labeled_samples, _feature_builder)
        raw_scores: list[float] = []
        targets: list[float] = []
        for labeled_sample in labeled_samples:
            raw_context = self._build_raw_score_context(labeled_sample.envelope)
            raw_scores.append(raw_context["final_score"])
            targets.append(labeled_sample.target_rpi)
        self.calibrator.fit(raw_scores, targets)

    def _validate_envelope(self, envelope: SignalEnvelope) -> None:
        """Enforce supported schema versions and minimal envelope sanity."""

        if envelope.signal_schema_version not in SUPPORTED_SIGNAL_SCHEMA_VERSIONS:
            raise ValueError(
                f"unsupported signal_schema_version: {envelope.signal_schema_version}; "
                f"supported={SUPPORTED_SIGNAL_SCHEMA_VERSIONS}"
            )
        if not isinstance(envelope.signals, dict):
            raise ValueError("signals must be a mapping of signal_name -> SignalPayload")

    def train_on_synthetic(self, sample_count: int = 300, seed: int = 42) -> list[LabeledEnvelope]:
        """Train the ML layer on generated development data."""

        labeled_samples = generate_synthetic_dataset(sample_count=sample_count, seed=seed, profile_mix="balanced")
        self.fit(labeled_samples)
        return labeled_samples

    def _build_raw_score_context(self, envelope: SignalEnvelope) -> dict[str, float | dict | list]:
        """Compute the raw score components before decision policy routing."""

        self._validate_envelope(envelope)
        sub_scores, baseline_rpi = _feature_builder(envelope)
        caution_flags = derive_caution_flags(envelope)
        if not envelope.signals:
            caution_flags.append("no_structured_signals")
        ml_rpi = self.ml_model.predict(envelope, sub_scores, baseline_rpi)
        blended_rpi = clamp_score(
            baseline_rpi * self.blend_weight_baseline + ml_rpi * self.blend_weight_ml
        )
        final_score = apply_missing_data_penalty(blended_rpi, envelope.completeness)
        confidence, uncertainty_flag, confidence_components = assess_score_confidence(
            envelope=envelope,
            baseline_rpi=baseline_rpi,
            ml_rpi=ml_rpi,
            caution_flags=caution_flags,
        )
        return {
            "sub_scores": sub_scores,
            "baseline_rpi": baseline_rpi,
            "ml_rpi": ml_rpi,
            "blended_rpi": blended_rpi,
            "final_score": final_score,
            "confidence": confidence,
            "uncertainty_flag": uncertainty_flag,
            "confidence_components": confidence_components,
            "caution_flags": caution_flags,
        }

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
        manual_review_flags: list[bool] = []
        latencies_ms: list[float] = []

        for labeled_sample in test_samples:
            started_at = perf_counter()
            score = self.score_candidate(labeled_sample.envelope)
            latencies_ms.append((perf_counter() - started_at) * 1000.0)
            true_scores.append(labeled_sample.target_rpi)
            predicted_scores.append(score.review_priority_index)
            confidence_bands.append(score.confidence_band)
            review_recommendations.append(score.review_recommendation)
            uncertainty_flags.append(score.uncertainty_flag)
            manual_review_flags.append(score.manual_review_required)
            true_statuses.append(
                map_recommendation_status(
                    score=labeled_sample.target_rpi,
                    completeness=labeled_sample.envelope.completeness,
                )
            )
            predicted_statuses.append(score.score_status)

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
        safe_correlation = float(correlation) if correlation is not None and not math.isnan(float(correlation)) else 0.0

        rmse = math.sqrt(mean_squared_error(true_scores, predicted_scores))
        status_rates = {
            f"{status_name.lower()}_rate": round(float(np.mean([status == status_name for status in predicted_statuses])), 4)
            for status_name in STATUS_ORDER
        }
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
            "spearman_rank_correlation": round(safe_correlation, 4),
            "top_k_overlap": round(len(true_top & predicted_top) / max(top_k, 1), 4),
            "manual_review_rate": round(float(np.mean(manual_review_flags)), 4),
            "uncertainty_rate": round(float(np.mean(uncertainty_flags)), 4),
            "high_confidence_rate": round(float(np.mean([band == "HIGH" for band in confidence_bands])), 4),
            "fast_track_rate": round(
                float(np.mean([review == "FAST_TRACK_REVIEW" for review in review_recommendations])),
                4,
            ),
            "avg_latency_ms": round(float(np.mean(latencies_ms)) if latencies_ms else 0.0, 4),
            "p95_latency_ms": round(float(np.percentile(latencies_ms, 95)) if latencies_ms else 0.0, 4),
            "throughput_candidates_per_sec": round(
                float(1000.0 / np.mean(latencies_ms)) if latencies_ms and np.mean(latencies_ms) > 0 else 0.0,
                4,
            ),
            **status_rates,
        }

    def build_explanation_input(
        self,
        envelope: SignalEnvelope,
        score: CandidateScore | None = None,
    ) -> ExplanationInput:
        """Prepare the scoring-to-explanation handoff payload without forcing a re-score."""

        score = score or self.score_candidate(envelope)
        positive_factors = self._build_positive_factors(score)
        caution_flags = self._build_caution_items(score.caution_flags)
        signal_context = {
            signal_name: ExplanationSignalContext(**signal.model_dump())
            for signal_name, signal in envelope.signals.items()
        }
        data_quality_notes = self._build_data_quality_notes(score)

        return ExplanationInput(
            candidate_id=score.candidate_id,
            scoring_version=score.scoring_version,
            selected_program=score.selected_program,
            program_id=score.program_id,
            recommendation_status=score.recommendation_status,
            review_priority_index=score.review_priority_index,
            confidence=score.confidence,
            uncertainty_flag=score.uncertainty_flag,
            manual_review_required=score.manual_review_required,
            human_in_loop_required=score.human_in_loop_required,
            review_recommendation=score.review_recommendation,
            review_reasons=score.review_reasons,
            sub_scores=score.sub_scores,
            score_breakdown=score.score_breakdown,
            positive_factors=positive_factors,
            caution_flags=caution_flags,
            signal_context=signal_context,
            data_quality_notes=data_quality_notes,
        )

    def score_candidate(self, envelope: SignalEnvelope) -> CandidateScore:
        """Score one candidate from the canonical signal envelope."""

        raw_context = self._build_raw_score_context(envelope)
        resolved_program_id = normalize_program_id(envelope.program_id or envelope.selected_program)
        sub_scores = raw_context["sub_scores"]
        baseline_rpi = raw_context["baseline_rpi"]
        ml_rpi = raw_context["ml_rpi"]
        blended_rpi = raw_context["blended_rpi"]
        raw_final_score = raw_context["final_score"]
        confidence = raw_context["confidence"]
        uncertainty_flag = bool(raw_context["uncertainty_flag"])
        confidence_components = raw_context["confidence_components"]
        caution_flags = raw_context["caution_flags"]

        decision = apply_decision_policy(
            raw_score=raw_final_score,
            confidence=confidence,
            confidence_components=confidence_components,
            caution_flags=caution_flags,
            data_flags=envelope.data_flags,
            completeness=envelope.completeness,
            policy=self.policy_config,
            calibrator=self.calibrator,
        )
        top_strengths = self._build_top_strengths(sub_scores)
        top_risks = self._build_top_risks(
            caution_flags,
            confidence_components,
            envelope.completeness,
            decision.uncertainty_categories,
        )
        if not envelope.signals:
            logger.warning("Scoring stage received an empty signal envelope for candidate %s", envelope.candidate_id)
        final_uncertainty_flag = (
            uncertainty_flag
            or decision.manual_review_required
            or len(decision.uncertainty_categories) >= self.policy_config.uncertainty_policy.uncertainty_flag_trigger_count
        )
        return CandidateScore(
            candidate_id=envelope.candidate_id,
            selected_program=envelope.selected_program,
            program_id=resolved_program_id,
            sub_scores=sub_scores,
            program_weight_profile=get_program_weight_profile(resolved_program_id),
            review_priority_index=decision.calibrated_score,
            score_status=decision.score_status,
            recommendation_status=decision.score_status,
            decision_summary=decision.decision_summary,
            confidence=confidence,
            confidence_band=decision.confidence_band,
            manual_review_required=decision.manual_review_required,
            human_in_loop_required=decision.manual_review_required,
            uncertainty_flag=final_uncertainty_flag,
            shortlist_eligible=decision.shortlist_eligible,
            review_recommendation=decision.review_recommendation,
            review_reasons=decision.review_reasons + decision.uncertainty_categories,
            top_strengths=top_strengths,
            top_risks=top_risks,
            score_delta_vs_baseline=round(decision.calibrated_score - baseline_rpi, 4),
            caution_flags=caution_flags,
            score_breakdown={
                "baseline_rpi": baseline_rpi,
                "ml_rpi": ml_rpi,
                "blended_rpi": blended_rpi,
                "raw_final_score": raw_final_score,
                "calibrated_score": decision.calibrated_score,
                **confidence_components,
            },
            model_family=self.model_family,
            scoring_version=self.scoring_version,
        )

    def score_batch(self, envelopes: list[SignalEnvelope]) -> list[CandidateScore]:
        """Score and rank a batch of candidates."""

        scored_candidates = [self.score_candidate(envelope) for envelope in envelopes]
        return rank_scores(scored_candidates)

    def _build_positive_factors(self, score: CandidateScore) -> list[ExplanationFactor]:
        """Prepare the top score contributors for the explanation layer."""

        factors = []
        program_weights = get_program_weight_profile(score.program_id or score.selected_program)
        for sub_score_name, sub_score_value in score.sub_scores.items():
            contribution = clamp_score(sub_score_value * program_weights.get(sub_score_name, 0.0))
            factors.append(
                ExplanationFactor(
                    factor=sub_score_name,
                    sub_score=sub_score_name,
                    score=sub_score_value,
                    score_contribution=contribution,
                )
            )

        factors.sort(key=lambda factor: factor.score_contribution, reverse=True)
        return factors[:3]

    def _build_caution_items(self, caution_flags: list[str]) -> list[ExplanationCautionFlag]:
        """Normalize caution flags for the explanation layer."""

        severity_map = {
            "low_completeness": "critical",
            "no_structured_signals": "critical",
            "requires_human_review": "critical",
            "essay_replaced_by_video_transcript": "advisory",
            "missing_essay": "warning",
            "missing_video": "warning",
            "missing_video_transcript": "warning",
            "missing_project_descriptions": "advisory",
            "low_profile_completeness": "warning",
            "asr_processing_failed": "warning",
            "low_asr_confidence": "warning",
            "possible_ai_use": "warning",
            "authenticity_or_ai_risk": "warning",
            "low_cross_source_consistency": "warning",
            "weak_claim_support": "warning",
            "voice_inconsistency": "warning",
            "generic_evidence": "advisory",
        }
        reason_map = {
            "low_completeness": "Р”Р°РЅРЅС‹С… РїРѕ РєР°РЅРґРёРґР°С‚Сѓ РЅРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ, РїРѕСЌС‚РѕРјСѓ С‚РµРєСѓС‰СѓСЋ РѕС†РµРЅРєСѓ РЅСѓР¶РЅРѕ СЃС‡РёС‚Р°С‚СЊ РїСЂРµРґРІР°СЂРёС‚РµР»СЊРЅРѕР№, Р° РЅРµ Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРё СЃР»Р°Р±РѕР№.",
            "no_structured_signals": "РџР°Р№РїР»Р°Р№РЅ РЅРµ СЃРјРѕРі СЃРѕР±СЂР°С‚СЊ РґРѕСЃС‚Р°С‚РѕС‡РЅРѕ СЃС‚СЂСѓРєС‚СѓСЂРёСЂРѕРІР°РЅРЅС‹С… СЃРёРіРЅР°Р»РѕРІ РґР»СЏ РЅР°РґРµР¶РЅРѕР№ Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРѕР№ РёРЅС‚РµСЂРїСЂРµС‚Р°С†РёРё.",
            "requires_human_review": "РћРґРёРЅ РёР»Рё РЅРµСЃРєРѕР»СЊРєРѕ Р¶РµСЃС‚РєРёС… quality/policy-check СѓР¶Рµ С‚СЂРµР±СѓСЋС‚ СЂСѓС‡РЅРѕР№ РїСЂРѕРІРµСЂРєРё РєРѕРјРёСЃСЃРёРµР№.",
            "essay_replaced_by_video_transcript": "РўРµРєСЃС‚РѕРІРѕРµ СЌСЃСЃРµ РЅРµ РїСЂРёР»РѕР¶РµРЅРѕ, РїРѕСЌС‚РѕРјСѓ РЅР°СЂСЂР°С‚РёРІ РєР°РЅРґРёРґР°С‚Р° СЃРѕР±СЂР°РЅ РёР· С‚СЂР°РЅСЃРєСЂРёРїС†РёРё РІРёРґРµРѕ.",
            "missing_essay": "РўРµРєСЃС‚РѕРІРѕРіРѕ СЌСЃСЃРµ РЅРµС‚, РїРѕСЌС‚РѕРјСѓ С‡Р°СЃС‚СЊ РѕС†РµРЅРєРё СЃС‚СЂРѕРёС‚СЃСЏ Р±РµР· РїРёСЃСЊРјРµРЅРЅРѕРіРѕ РёСЃС‚РѕС‡РЅРёРєР° РєР°РЅРґРёРґР°С‚Р°.",
            "missing_video": "Р’РёРґРµРѕРёРЅС‚РµСЂРІСЊСЋ РЅРµ РїСЂРµРґРѕСЃС‚Р°РІР»РµРЅРѕ, РїРѕСЌС‚РѕРјСѓ РіРѕР»РѕСЃРѕРІС‹Рµ Рё РїРѕРІРµРґРµРЅС‡РµСЃРєРёРµ СЃРёРіРЅР°Р»С‹ РѕРіСЂР°РЅРёС‡РµРЅС‹.",
            "missing_video_transcript": "РўСЂР°РЅСЃРєСЂРёРїС†РёСЏ РІРёРґРµРѕ РѕС‚СЃСѓС‚СЃС‚РІСѓРµС‚, РїРѕСЌС‚РѕРјСѓ РїРёСЃСЊРјРµРЅРЅС‹Р№ Р°РЅР°Р»РёР· РЅРµ РјРѕР¶РµС‚ РѕРїРёСЂР°С‚СЊСЃСЏ РЅР° СѓСЃС‚РЅСѓСЋ СЂРµС‡СЊ РєР°РЅРґРёРґР°С‚Р°.",
            "missing_project_descriptions": "РќРµС‚ РѕРїРёСЃР°РЅРёР№ РїСЂРѕРµРєС‚РѕРІ, РїРѕСЌС‚РѕРјСѓ РїСЂР°РєС‚РёС‡РµСЃРєРёРµ РїСЂРёРјРµСЂС‹ Рё РїРѕРґС‚РІРµСЂР¶РґРµРЅРёРµ РґРѕСЃС‚РёР¶РµРЅРёР№ РѕРіСЂР°РЅРёС‡РµРЅС‹.",
            "low_profile_completeness": "РџСЂРѕС„РёР»СЊ Р·Р°РїРѕР»РЅРµРЅ РЅРµРїРѕР»РЅРѕ, РїРѕСЌС‚РѕРјСѓ С‡Р°СЃС‚СЊ РІС‹РІРѕРґРѕРІ СЃС‚СЂРѕРёС‚СЃСЏ РЅР° РѕРіСЂР°РЅРёС‡РµРЅРЅРѕРј РЅР°Р±РѕСЂРµ РґР°РЅРЅС‹С….",
            "asr_processing_failed": "ASR РЅРµ СЃРјРѕРі РєРѕСЂСЂРµРєС‚РЅРѕ РѕР±СЂР°Р±РѕС‚Р°С‚СЊ РІРёРґРµРѕ, РїРѕСЌС‚РѕРјСѓ СѓСЃС‚РЅС‹Р№ РёСЃС‚РѕС‡РЅРёРє РІСЂРµРјРµРЅРЅРѕ РёСЃРєР»СЋС‡РµРЅ РёР· Р°РЅР°Р»РёР·Р°.",
            "low_asr_confidence": "РЈРІРµСЂРµРЅРЅРѕСЃС‚СЊ ASR РЅРёР·РєР°СЏ, РїРѕСЌС‚РѕРјСѓ С‚СЂР°РЅСЃРєСЂРёРїС†РёСЋ РЅСѓР¶РЅРѕ С‚СЂР°РєС‚РѕРІР°С‚СЊ РѕСЃС‚РѕСЂРѕР¶РЅРѕ.",
            "possible_ai_use": "Р’ РЅР°СЂСЂР°С‚РёРІРµ РµСЃС‚СЊ РїСЂРёР·РЅР°РєРё РІРѕР·РјРѕР¶РЅРѕРіРѕ РёСЃРїРѕР»СЊР·РѕРІР°РЅРёСЏ РР РёР»Рё РґСЂСѓРіРѕР№ РЅРёР·РєРѕР№ Р°СѓС‚РµРЅС‚РёС‡РЅРѕСЃС‚Рё, РїРѕСЌС‚РѕРјСѓ РєРµР№СЃ СЃС‚РѕРёС‚ РїСЂРѕРІРµСЂРёС‚СЊ РІСЂСѓС‡РЅСѓСЋ.",
            "authenticity_or_ai_risk": "Р’ РЅР°СЂСЂР°С‚РёРІРµ РµСЃС‚СЊ РїСЂРёР·РЅР°РєРё РІРѕР·РјРѕР¶РЅРѕРіРѕ РёСЃРїРѕР»СЊР·РѕРІР°РЅРёСЏ РР РёР»Рё РґСЂСѓРіРѕР№ РЅРёР·РєРѕР№ Р°СѓС‚РµРЅС‚РёС‡РЅРѕСЃС‚Рё, РїРѕСЌС‚РѕРјСѓ РєРµР№СЃ СЃС‚РѕРёС‚ РїСЂРѕРІРµСЂРёС‚СЊ РІСЂСѓС‡РЅСѓСЋ.",
            "low_cross_source_consistency": "РљР»СЋС‡РµРІС‹Рµ СѓС‚РІРµСЂР¶РґРµРЅРёСЏ СЃР»Р°Р±Рѕ СЃРѕРІРїР°РґР°СЋС‚ РјРµР¶РґСѓ СЌСЃСЃРµ, С‚СЂР°РЅСЃРєСЂРёРїС†РёРµР№ Рё СЃРѕРїСЂРѕРІРѕРґРёС‚РµР»СЊРЅС‹РјРё РѕРїРёСЃР°РЅРёСЏРјРё.",
            "weak_claim_support": "Р§Р°СЃС‚СЊ Р·РЅР°С‡РёРјС‹С… Р·Р°СЏРІР»РµРЅРёР№ РЅРµ РїРѕРґС‚РІРµСЂР¶РґРµРЅР° РєРѕРЅРєСЂРµС‚РЅС‹РјРё РїСЂРёРјРµСЂР°РјРё, РїСЂРѕРµРєС‚Р°РјРё РёР»Рё РёР·РјРµСЂРёРјС‹РјРё СЂРµР·СѓР»СЊС‚Р°С‚Р°РјРё.",
            "voice_inconsistency": "РџРёСЃСЊРјРµРЅРЅР°СЏ Рё СѓСЃС‚РЅР°СЏ РІРµСЂСЃРёРё РёСЃС‚РѕСЂРёРё РєР°РЅРґРёРґР°С‚Р° СЂР°Р·Р»РёС‡Р°СЋС‚СЃСЏ СЃРёР»СЊРЅРµРµ РґРѕРїСѓСЃС‚РёРјРѕРіРѕ РґР»СЏ СѓРІРµСЂРµРЅРЅРѕРіРѕ СЂРµС€РµРЅРёСЏ Р±РµР· РїСЂРѕРІРµСЂРєРё.",
            "generic_evidence": "Р’ СЂР°СЃРїРѕСЂСЏР¶РµРЅРёРё СЃРёСЃС‚РµРјС‹ РІ РѕСЃРЅРѕРІРЅРѕРј РѕР±С‰РёРµ С„РѕСЂРјСѓР»РёСЂРѕРІРєРё, Р° РЅРµ РєРѕРЅРєСЂРµС‚РЅС‹Рµ С„Р°РєС‚С‹ Рё РїСЂРёРјРµСЂС‹.",
        }
        return [
            ExplanationCautionFlag(
                flag=flag,
                severity=severity_map.get(flag, "advisory"),
                reason=reason_map.get(flag, "Derived from modifier signals or data quality flags."),
            )
            for flag in caution_flags
        ]

    def _build_data_quality_notes(self, score: CandidateScore) -> list[str]:
        """Prepare reviewer-facing data quality notes for the explanation handoff."""

        notes = [
            f"confidence_band={score.confidence_band}",
            f"signal_coverage={score.score_breakdown.get('signal_coverage', 0.0):.2f}",
            f"mean_signal_confidence={score.score_breakdown.get('mean_signal_confidence', 0.0):.2f}",
            f"completeness={score.score_breakdown.get('completeness', 0.0):.2f}",
        ]
        if score.manual_review_required and score.score_breakdown.get("completeness", 1.0) < 0.50:
            notes.append("The case is routed to manual review because the available evidence is incomplete, not because the candidate was automatically judged as weak.")
        return notes

    def _build_top_strengths(self, sub_scores: dict[str, float]) -> list[str]:
        """Return the strongest sub-score labels for UI display."""

        ranked = sorted(sub_scores.items(), key=lambda item: item[1], reverse=True)
        return [name for name, value in ranked if value >= 0.60][:3]

    def _build_top_risks(
        self,
        caution_flags: list[str],
        confidence_components: dict[str, float],
        completeness: float,
        uncertainty_categories: list[str],
    ) -> list[str]:
        """Return the main reasons why the candidate may need extra scrutiny."""

        top_risks = list(uncertainty_categories[:3]) + list(caution_flags[:3])
        if confidence_components.get("signal_coverage", 1.0) < 0.60:
            top_risks.append("low_signal_coverage")
        if confidence_components.get("mean_signal_confidence", 1.0) < 0.60:
            top_risks.append("low_signal_confidence")
        if completeness < 0.50:
            top_risks.append("low_completeness")
        return list(dict.fromkeys(top_risks))[:3]
