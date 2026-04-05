"""
File: optimization.py
Purpose: Transparent grid search for scoring decision-layer tuning.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from itertools import product
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import mean_absolute_error, mean_squared_error, precision_recall_fscore_support, r2_score

from .calibration import ScoreCalibrator
from .decision_policy import DecisionContext, apply_decision_policy, classify_score
from .io_utils import ensure_trusted_report_dir
from .scoring_config import DecisionPolicyConfig, build_policy_config
from .service import ScoringService
from .synthetic_data import generate_synthetic_dataset
from .schemas import LabeledEnvelope


@dataclass(frozen=True)
class Snapshot:
    """One precomputed sample snapshot for routing optimization."""

    completeness: float
    data_flags: tuple[str, ...]
    target_rpi: float
    raw_score: float
    confidence: float
    confidence_components: dict[str, float]
    caution_flags: tuple[str, ...]
    profile_type: str


def _prepare_snapshots(service: ScoringService, labeled_samples: list[LabeledEnvelope]) -> list[Snapshot]:
    """Precompute raw scoring contexts so search avoids repeated model fitting."""

    snapshots: list[Snapshot] = []
    for labeled_sample in labeled_samples:
        raw_context = service._build_raw_score_context(labeled_sample.envelope)
        snapshots.append(
            Snapshot(
                completeness=labeled_sample.envelope.completeness,
                data_flags=tuple(labeled_sample.envelope.data_flags),
                target_rpi=labeled_sample.target_rpi,
                raw_score=float(raw_context["final_score"]),
                confidence=float(raw_context["confidence"]),
                confidence_components=dict(raw_context["confidence_components"]),
                caution_flags=tuple(raw_context["caution_flags"]),
                profile_type=labeled_sample.profile_type,
            )
        )
    return snapshots


def _fit_calibrator(mode: str, snapshots: list[Snapshot]) -> ScoreCalibrator:
    """Fit one calibration mode on the train snapshots."""

    calibrator = ScoreCalibrator(mode=mode)
    calibrator.fit([item.raw_score for item in snapshots], [item.target_rpi for item in snapshots])
    return calibrator


def _borderline_summary(frame: pd.DataFrame, policy: DecisionPolicyConfig) -> dict[str, float]:
    """Summarize borderline routing around WAITLIST / DECLINED boundaries."""

    lower = max(0.0, policy.thresholds.waitlist_min - 0.05)
    upper = min(1.0, policy.thresholds.recommend_min + 0.03)
    borderline = frame[(frame["calibrated_score"] >= lower) & (frame["calibrated_score"] <= upper)]
    if borderline.empty:
        return {
            "borderline_count": 0,
            "borderline_waitlist_rate": 0.0,
            "borderline_declined_rate": 0.0,
            "borderline_manual_review_rate": 0.0,
        }
    return {
        "borderline_count": int(len(borderline)),
        "borderline_waitlist_rate": round(float((borderline["score_status"] == "WAITLIST").mean()), 4),
        "borderline_declined_rate": round(float((borderline["score_status"] == "DECLINED").mean()), 4),
        "borderline_manual_review_rate": round(float(borderline["manual_review_required"].mean()), 4),
    }


def _evaluate_snapshots(
    snapshots: list[Snapshot],
    policy: DecisionPolicyConfig,
    calibrator: ScoreCalibrator,
    split_name: str,
) -> dict:
    """Evaluate one policy config on a prepared snapshot split."""

    rows = []
    for snapshot in snapshots:
        outcome = apply_decision_policy(
            raw_score=snapshot.raw_score,
            confidence=snapshot.confidence,
            confidence_components=snapshot.confidence_components,
            caution_flags=snapshot.caution_flags,
            data_flags=snapshot.data_flags,
            completeness=snapshot.completeness,
            policy=policy,
            calibrator=calibrator,
        )
        rows.append(
            {
                "target_rpi": snapshot.target_rpi,
                "calibrated_score": outcome.calibrated_score,
                "target_status": classify_score(
                    DecisionContext(
                        calibrated_score=snapshot.target_rpi,
                        completeness=snapshot.completeness,
                        confidence=1.0,
                        mean_signal_confidence=1.0,
                        signal_coverage=1.0,
                        model_disagreement=0.0,
                        soft_caution_count=0,
                        caution_flags=(),
                        data_flags=(),
                    ),
                    policy,
                ),
                "score_status": outcome.score_status,
                "manual_review_required": outcome.manual_review_required,
                "profile_type": snapshot.profile_type,
                "confidence": snapshot.confidence,
            }
        )

    frame = pd.DataFrame(rows)
    precision, recall, f1, _ = precision_recall_fscore_support(
        frame["target_status"],
        frame["score_status"],
        average="macro",
        zero_division=0,
    )
    accept_rate = float(frame["score_status"].isin(["STRONG_RECOMMEND", "RECOMMEND"]).mean())
    rmse = math.sqrt(mean_squared_error(frame["target_rpi"], frame["calibrated_score"]))
    borderline = _borderline_summary(frame, policy)
    metrics = {
        "split": split_name,
        "mae": round(float(mean_absolute_error(frame["target_rpi"], frame["calibrated_score"])), 4),
        "rmse": round(float(rmse), 4),
        "r2": round(float(r2_score(frame["target_rpi"], frame["calibrated_score"])), 4),
        "macro_precision": round(float(precision), 4),
        "macro_recall": round(float(recall), 4),
        "macro_f1": round(float(f1), 4),
        "spearman_rank_correlation": round(
            float(spearmanr(frame["target_rpi"], frame["calibrated_score"]).correlation or 0.0),
            4,
        ),
        "acceptance_rate": round(accept_rate, 4),
        "strong_rate": round(float((frame["score_status"] == "STRONG_RECOMMEND").mean()), 4),
        "recommend_rate": round(float((frame["score_status"] == "RECOMMEND").mean()), 4),
        "waitlist_rate": round(float((frame["score_status"] == "WAITLIST").mean()), 4),
        "declined_rate": round(float((frame["score_status"] == "DECLINED").mean()), 4),
        "manual_review_rate": round(float(frame["manual_review_required"].mean()), 4),
        **borderline,
    }
    return {"metrics": metrics, "frame": frame}


def _distance_to_band(value: float, low: float, high: float) -> float:
    """Return zero inside the target band and distance outside it."""

    if low <= value <= high:
        return 0.0
    if value < low:
        return low - value
    return value - high


def _objective_score(balanced_metrics: dict, stress_metrics: dict) -> float:
    """Compute a weighted multi-objective score for ranking candidates."""

    accept_penalty = _distance_to_band(balanced_metrics["acceptance_rate"], 0.30, 0.35)
    manual_penalty = _distance_to_band(balanced_metrics["manual_review_rate"], 0.10, 0.20)
    stress_manual_penalty = max(0.0, stress_metrics["manual_review_rate"] - 0.22)
    borderline_penalty = max(0.0, balanced_metrics["borderline_declined_rate"] - 0.55)
    borderline_reward = balanced_metrics["borderline_waitlist_rate"]
    robustness_penalty = abs(balanced_metrics["acceptance_rate"] - stress_metrics["acceptance_rate"])

    score = (
        100.0
        - accept_penalty * 320.0
        - manual_penalty * 260.0
        - stress_manual_penalty * 90.0
        - robustness_penalty * 55.0
        - borderline_penalty * 35.0
        + borderline_reward * 24.0
        + balanced_metrics["macro_f1"] * 10.0
        + stress_metrics["macro_f1"] * 10.0
        + balanced_metrics["r2"] * 3.0
        + stress_metrics["r2"] * 3.0
    )
    return round(score, 4)


def _build_candidate_policies() -> list[DecisionPolicyConfig]:
    """Build a transparent grid of candidate decision-layer configs."""

    policies: list[DecisionPolicyConfig] = []
    grid = product(
        (0.76, 0.78, 0.80),
        (0.62, 0.64, 0.645, 0.65, 0.66),
        (0.44, 0.46, 0.48),
        (0.42, 0.46),
        (0.01, 0.015),
        (3, 4),
        ("none", "isotonic"),
        (0.30, 0.32, 0.34),
    )
    for (
        strong_min,
        recommend_min,
        waitlist_min,
        low_confidence_max,
        narrow_margin_max,
        trigger_count,
        calibration_mode,
        declined_manual_review_score_min,
    ) in grid:
        if not (strong_min > recommend_min > waitlist_min):
            continue
        overrides = {
            "default_calibration_mode": calibration_mode,
            "status_thresholds": {
                "strong_recommend_min": strong_min,
                "recommend_min": recommend_min,
                "waitlist_min": waitlist_min,
            },
            "uncertainty_policy": {
                "declined_manual_review_score_min": declined_manual_review_score_min,
                "low_confidence_max": low_confidence_max,
                "narrow_margin_max": narrow_margin_max,
                "manual_review_trigger_count": trigger_count,
                "low_coverage_max": 0.40,
                "disagreement_max": 0.28,
                "soft_caution_min": 4,
            },
        }
        policies.append(build_policy_config(overrides=overrides))
    return policies


def search_decision_configs(
    train_sample_count: int = 300,
    test_sample_count: int = 120,
    seed: int = 42,
) -> tuple[pd.DataFrame, list[dict]]:
    """Run grid search over decision thresholds and uncertainty policy."""

    train_samples = generate_synthetic_dataset(sample_count=train_sample_count, seed=seed, profile_mix="balanced")
    balanced_samples = generate_synthetic_dataset(sample_count=test_sample_count, seed=seed + 1, profile_mix="balanced")
    stress_samples = generate_synthetic_dataset(sample_count=test_sample_count, seed=seed + 2, profile_mix="stress")

    training_service = ScoringService(calibration_mode="none")
    training_service.fit(train_samples)

    train_snapshots = _prepare_snapshots(training_service, train_samples)
    balanced_snapshots = _prepare_snapshots(training_service, balanced_samples)
    stress_snapshots = _prepare_snapshots(training_service, stress_samples)
    calibrators = {
        mode: _fit_calibrator(mode, train_snapshots)
        for mode in ("none", "isotonic")
    }

    rows: list[dict] = []
    details: list[dict] = []

    for index, policy in enumerate(_build_candidate_policies(), start=1):
        calibrator = calibrators[policy.calibration_mode]
        balanced_eval = _evaluate_snapshots(balanced_snapshots, policy, calibrator, "balanced")
        stress_eval = _evaluate_snapshots(stress_snapshots, policy, calibrator, "stress")
        objective = _objective_score(balanced_eval["metrics"], stress_eval["metrics"])

        row = {
            "candidate_id": index,
            "calibration_mode": policy.calibration_mode,
            "strong_min": policy.thresholds.strong_recommend_min,
            "recommend_min": policy.thresholds.recommend_min,
            "waitlist_min": policy.thresholds.waitlist_min,
            "low_confidence_max": policy.uncertainty_policy.low_confidence_max,
            "narrow_margin_max": policy.uncertainty_policy.narrow_margin_max,
            "manual_review_trigger_count": policy.uncertainty_policy.manual_review_trigger_count,
            "declined_manual_review_score_min": policy.uncertainty_policy.declined_manual_review_score_min,
            "objective_score": objective,
            "balanced_acceptance_rate": balanced_eval["metrics"]["acceptance_rate"],
            "balanced_manual_review_rate": balanced_eval["metrics"]["manual_review_rate"],
            "balanced_waitlist_rate": balanced_eval["metrics"]["waitlist_rate"],
            "balanced_declined_rate": balanced_eval["metrics"]["declined_rate"],
            "balanced_macro_f1": balanced_eval["metrics"]["macro_f1"],
            "stress_acceptance_rate": stress_eval["metrics"]["acceptance_rate"],
            "stress_manual_review_rate": stress_eval["metrics"]["manual_review_rate"],
            "stress_waitlist_rate": stress_eval["metrics"]["waitlist_rate"],
            "stress_declined_rate": stress_eval["metrics"]["declined_rate"],
            "stress_macro_f1": stress_eval["metrics"]["macro_f1"],
            "borderline_waitlist_rate": balanced_eval["metrics"]["borderline_waitlist_rate"],
            "borderline_declined_rate": balanced_eval["metrics"]["borderline_declined_rate"],
            "borderline_manual_review_rate": balanced_eval["metrics"]["borderline_manual_review_rate"],
        }
        rows.append(row)
        details.append(
            {
                "candidate_id": index,
                "policy": {
                    "calibration_mode": policy.calibration_mode,
                    "thresholds": asdict(policy.thresholds),
                    "uncertainty_policy": asdict(policy.uncertainty_policy),
                },
                "balanced_metrics": balanced_eval["metrics"],
                "stress_metrics": stress_eval["metrics"],
                "objective_score": objective,
            }
        )

    frame = pd.DataFrame(rows).sort_values("objective_score", ascending=False).reset_index(drop=True)
    return frame, details


def select_recommendations(search_frame: pd.DataFrame, details: list[dict]) -> dict[str, dict]:
    """Select the three recommended operating points from the ranked search table."""

    detail_map = {item["candidate_id"]: item for item in details}
    balanced_frame = search_frame[
        (search_frame["balanced_acceptance_rate"] >= 0.30)
        & (search_frame["balanced_acceptance_rate"] <= 0.35)
        & (search_frame["balanced_manual_review_rate"] <= 0.22)
    ]
    balanced = (balanced_frame.iloc[0] if not balanced_frame.empty else search_frame.iloc[0]).to_dict()

    conservative_frame = search_frame[
        (search_frame["balanced_acceptance_rate"] <= 0.31)
        & (search_frame["balanced_manual_review_rate"] <= 0.22)
    ]
    conservative = (conservative_frame.iloc[0] if not conservative_frame.empty else search_frame.iloc[0]).to_dict()

    softer_frame = search_frame[
        (search_frame["balanced_acceptance_rate"] <= 0.36)
        & (search_frame["balanced_manual_review_rate"] <= 0.22)
    ].sort_values(
        ["borderline_waitlist_rate", "balanced_acceptance_rate", "objective_score"],
        ascending=[False, False, False],
    )
    softer = (softer_frame.iloc[0] if not softer_frame.empty else search_frame.iloc[0]).to_dict()

    return {
        "conservative": detail_map[int(conservative["candidate_id"])],
        "balanced": detail_map[int(balanced["candidate_id"])],
        "softer_borderline": detail_map[int(softer["candidate_id"])],
    }


def export_search_report(out_dir: str | Path, train_sample_count: int = 300, test_sample_count: int = 120, seed: int = 42) -> dict[str, Path]:
    """Run the search and export ranked candidates plus top recommendations."""

    output_dir = ensure_trusted_report_dir(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    frame, details = search_decision_configs(
        train_sample_count=train_sample_count,
        test_sample_count=test_sample_count,
        seed=seed,
    )
    recommendations = select_recommendations(frame, details)

    ranked_path = output_dir / "decision_search_ranked.csv"
    details_path = output_dir / "decision_search_details.json"
    recommendations_path = output_dir / "decision_search_recommendations.json"

    frame.to_csv(ranked_path, index=False)
    details_path.write_text(json.dumps(details, indent=2), encoding="utf-8")
    recommendations_path.write_text(json.dumps(recommendations, indent=2), encoding="utf-8")

    return {
        "decision_search_ranked": ranked_path,
        "decision_search_details": details_path,
        "decision_search_recommendations": recommendations_path,
    }


def main() -> None:
    """CLI entry point for decision-layer grid search."""

    parser = argparse.ArgumentParser(description="Run decision-layer optimization for the scoring stage.")
    parser.add_argument("--train-samples", type=int, default=300)
    parser.add_argument("--test-samples", type=int, default=120)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out-dir", type=str, default="")
    args = parser.parse_args()

    frame, details = search_decision_configs(
        train_sample_count=args.train_samples,
        test_sample_count=args.test_samples,
        seed=args.seed,
    )
    recommendations = select_recommendations(frame, details)

    print("\n[Scoring] Decision Search Top 10")
    print(frame.head(10).to_string(index=False))
    print("\n[Scoring] Recommended Configurations")
    print(json.dumps(recommendations, indent=2))

    if args.out_dir:
        exported = export_search_report(
            out_dir=args.out_dir,
            train_sample_count=args.train_samples,
            test_sample_count=args.test_samples,
            seed=args.seed,
        )
    print("\n[Scoring] Exported optimization artifacts")
        print(json.dumps({key: str(value) for key, value in exported.items()}, indent=2))


if __name__ == "__main__":
    main()

