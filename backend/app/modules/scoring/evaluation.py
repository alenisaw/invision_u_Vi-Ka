"""
File: evaluation.py
Purpose: Reproducible synthetic evaluation utilities for the scoring stage.
"""

from __future__ import annotations

import argparse
import json
import math
import logging
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import mean_absolute_error, mean_squared_error, precision_recall_fscore_support, r2_score

from .io_utils import ensure_trusted_report_dir
from .scoring_config import STATUS_ORDER
from .rules import map_recommendation_status
from .service import ScoringService
from .synthetic_data import build_reference_fixtures, generate_synthetic_dataset

logger = logging.getLogger(__name__)


def _build_status_distribution(results: pd.DataFrame, mode: str) -> pd.DataFrame:
    """Return status percentages for one evaluation mode."""

    rows = []
    sample_count = max(len(results), 1)
    for status_name in STATUS_ORDER:
        count = int((results["predicted_status"] == status_name).sum())
        rows.append(
            {
                "mode": mode,
                "status": status_name,
                "count": count,
                "rate": round(count / sample_count, 4),
            }
        )
    return pd.DataFrame(rows)


def _build_profile_type_summary(results: pd.DataFrame, mode: str) -> pd.DataFrame:
    """Return a compact per-profile-type summary for one evaluation mode."""

    rows = []
    for profile_type, frame in results.groupby("profile_type"):
        rows.append(
            {
                "mode": mode,
                "profile_type": profile_type,
                "sample_count": int(len(frame)),
                "mean_predicted_rpi": round(float(frame["predicted_rpi"].mean()), 4),
                "mean_confidence": round(float(frame["confidence"].mean()), 4),
                "manual_review_rate": round(float(frame["manual_review_required"].mean()), 4),
                "uncertainty_rate": round(float(frame["uncertainty_flag"].mean()), 4),
                "strong_recommend_rate": round(float((frame["predicted_status"] == "STRONG_RECOMMEND").mean()), 4),
                "recommend_rate": round(float((frame["predicted_status"] == "RECOMMEND").mean()), 4),
                "waitlist_rate": round(float((frame["predicted_status"] == "WAITLIST").mean()), 4),
                "declined_rate": round(float((frame["predicted_status"] == "DECLINED").mean()), 4),
            }
        )
    return pd.DataFrame(rows).sort_values(["mode", "profile_type"]).reset_index(drop=True)


def _evaluate_samples(service: ScoringService, test_samples) -> tuple[dict[str, float | int | str], pd.DataFrame]:
    """Evaluate one scoring service against a synthetic holdout split."""

    rows: list[dict[str, float | str | bool]] = []
    latencies_ms: list[float] = []
    for labeled_sample in test_samples:
        started_at = perf_counter()
        score = service.score_candidate(labeled_sample.envelope)
        latencies_ms.append((perf_counter() - started_at) * 1000.0)
        rows.append(
            {
                "candidate_id": str(labeled_sample.envelope.candidate_id),
                "target_rpi": labeled_sample.target_rpi,
                "predicted_rpi": score.review_priority_index,
                "target_status": map_recommendation_status(
                    score=labeled_sample.target_rpi,
                    completeness=labeled_sample.envelope.completeness,
                ),
                "predicted_score_status": score.score_status,
                "predicted_status": score.recommendation_status,
                "confidence": score.confidence,
                "confidence_band": score.confidence_band,
                "manual_review_required": score.manual_review_required,
                "uncertainty_flag": score.uncertainty_flag,
                "review_recommendation": score.review_recommendation,
                "completeness": labeled_sample.envelope.completeness,
                "signal_count": len(labeled_sample.envelope.signals),
                "profile_type": labeled_sample.profile_type,
            }
        )

    results = pd.DataFrame(rows)
    precision, recall, f1_score, _ = precision_recall_fscore_support(
        results["target_status"],
        results["predicted_score_status"],
        average="macro",
        zero_division=0,
    )
    correlation = spearmanr(results["target_rpi"], results["predicted_rpi"]).correlation
    top_k = min(10, len(results))
    true_top = set(results.nlargest(top_k, "target_rpi").index.tolist())
    predicted_top = set(results.nlargest(top_k, "predicted_rpi").index.tolist())
    safe_correlation = float(correlation) if correlation is not None and not math.isnan(float(correlation)) else 0.0

    metrics = {
        "sample_count": int(len(results)),
        "mae": round(float(mean_absolute_error(results["target_rpi"], results["predicted_rpi"])), 4),
        "rmse": round(float(math.sqrt(mean_squared_error(results["target_rpi"], results["predicted_rpi"]))), 4),
        "r2": round(float(r2_score(results["target_rpi"], results["predicted_rpi"])), 4),
        "macro_precision": round(float(precision), 4),
        "macro_recall": round(float(recall), 4),
        "macro_f1": round(float(f1_score), 4),
        "spearman_rank_correlation": round(safe_correlation, 4),
        "top_k_overlap": round(len(true_top & predicted_top) / max(top_k, 1), 4),
        "manual_review_rate": round(float(results["manual_review_required"].mean()), 4),
        "uncertainty_rate": round(float(results["uncertainty_flag"].mean()), 4),
        "high_confidence_rate": round(float((results["confidence_band"] == "HIGH").mean()), 4),
        "fast_track_rate": round(float((results["review_recommendation"] == "FAST_TRACK_REVIEW").mean()), 4),
        "avg_latency_ms": round(float(np.mean(latencies_ms)) if latencies_ms else 0.0, 4),
        "p95_latency_ms": round(float(np.percentile(latencies_ms, 95)) if latencies_ms else 0.0, 4),
        "throughput_candidates_per_sec": round(float(1000.0 / np.mean(latencies_ms)) if latencies_ms and np.mean(latencies_ms) > 0 else 0.0, 4),
        "acceptance_rate": round(
            float(results["predicted_status"].isin(["STRONG_RECOMMEND", "RECOMMEND"]).mean()),
            4,
        ),
        "strong_recommend_rate": round(float((results["predicted_status"] == "STRONG_RECOMMEND").mean()), 4),
        "recommend_rate": round(float((results["predicted_status"] == "RECOMMEND").mean()), 4),
        "waitlist_rate": round(float((results["predicted_status"] == "WAITLIST").mean()), 4),
        "declined_rate": round(float((results["predicted_status"] == "DECLINED").mean()), 4),
    }
    return metrics, results


def evaluate_baseline_only(
    train_sample_count: int = 300,
    test_sample_count: int = 120,
    seed: int = 42,
    test_profile_mix: str = "balanced",
) -> dict:
    """Evaluate the rule-based baseline without ML refinement."""

    _ = generate_synthetic_dataset(sample_count=train_sample_count, seed=seed, profile_mix="balanced")
    test_samples = generate_synthetic_dataset(sample_count=test_sample_count, seed=seed + 1, profile_mix=test_profile_mix)
    service = ScoringService()
    metrics, predictions = _evaluate_samples(service, test_samples)
    return {
        "mode": "baseline_only",
        "train_sample_count": train_sample_count,
        "test_sample_count": test_sample_count,
        "test_profile_mix": test_profile_mix,
        "metrics": metrics,
        "predictions": predictions,
    }


def evaluate_hybrid_model(
    train_sample_count: int = 300,
    test_sample_count: int = 120,
    seed: int = 42,
    model_family: str = "gbr",
    test_profile_mix: str = "balanced",
) -> dict:
    """Evaluate a hybrid scoring path for the requested model family."""

    train_samples = generate_synthetic_dataset(sample_count=train_sample_count, seed=seed, profile_mix="balanced")
    test_samples = generate_synthetic_dataset(sample_count=test_sample_count, seed=seed + 1, profile_mix=test_profile_mix)
    service = ScoringService(model_family=model_family)
    service.fit(train_samples)
    metrics, predictions = _evaluate_samples(service, test_samples)
    return {
        "mode": model_family,
        "train_sample_count": train_sample_count,
        "test_sample_count": test_sample_count,
        "test_profile_mix": test_profile_mix,
        "metrics": metrics,
        "predictions": predictions,
    }


def compare_models(
    train_sample_count: int = 300,
    test_sample_count: int = 120,
    seed: int = 42,
    test_profile_mix: str = "balanced",
) -> pd.DataFrame:
    """Return a compact comparison table across supported scoring modes."""

    comparisons = [
        evaluate_baseline_only(
            train_sample_count=train_sample_count,
            test_sample_count=test_sample_count,
            seed=seed,
            test_profile_mix=test_profile_mix,
        )
    ]

    for model_family in ("gbr",):
        try:
            comparisons.append(
                evaluate_hybrid_model(
                    train_sample_count=train_sample_count,
                    test_sample_count=test_sample_count,
                    seed=seed,
                    model_family=model_family,
                    test_profile_mix=test_profile_mix,
                )
            )
        except RuntimeError as exc:
            logger.warning("Scoring comparison skipped %s due to runtime error: %s", model_family, exc)
            continue

    return pd.DataFrame([{"mode": item["mode"], **item["metrics"]} for item in comparisons])


def build_fixture_report() -> pd.DataFrame:
    """Return a compact table for the fixed synthetic fixture set."""

    service = ScoringService(model_family="gbr")
    rows = []
    for fixture_name, envelope in build_reference_fixtures().items():
        score = service.score_candidate(envelope)
        rows.append(
            {
                "fixture": fixture_name,
                "status": score.recommendation_status,
                "rpi": score.review_priority_index,
                "confidence": score.confidence,
                "confidence_band": score.confidence_band,
                "manual_review_required": score.manual_review_required,
                "uncertainty_flag": score.uncertainty_flag,
                "shortlist_eligible": score.shortlist_eligible,
                "decision_summary": score.decision_summary,
                "caution_flags": ", ".join(score.caution_flags),
            }
        )
    return pd.DataFrame(rows).sort_values(["rpi", "confidence"], ascending=[False, False]).reset_index(drop=True)


def export_evaluation_bundle(out_dir: str | Path, train_sample_count: int = 300, test_sample_count: int = 120, seed: int = 42) -> dict[str, Path]:
    """Export comparison metrics and prediction tables for notebook or review use."""

    output_dir = ensure_trusted_report_dir(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    baseline = evaluate_baseline_only(
        train_sample_count=train_sample_count,
        test_sample_count=test_sample_count,
        seed=seed,
        test_profile_mix="balanced",
    )
    gbr = evaluate_hybrid_model(
        train_sample_count=train_sample_count,
        test_sample_count=test_sample_count,
        seed=seed,
        model_family="gbr",
        test_profile_mix="balanced",
    )
    balanced_comparison = compare_models(
        train_sample_count=train_sample_count,
        test_sample_count=test_sample_count,
        seed=seed,
        test_profile_mix="balanced",
    )
    stress_comparison = compare_models(
        train_sample_count=train_sample_count,
        test_sample_count=test_sample_count,
        seed=seed,
        test_profile_mix="stress",
    )
    fixtures = build_fixture_report()
    balanced_status_distribution = pd.concat(
        [
            _build_status_distribution(baseline["predictions"], "baseline_only"),
            _build_status_distribution(gbr["predictions"], "gbr"),
        ],
        ignore_index=True,
    )
    stress_baseline = evaluate_baseline_only(
        train_sample_count=train_sample_count,
        test_sample_count=test_sample_count,
        seed=seed,
        test_profile_mix="stress",
    )
    stress_gbr = evaluate_hybrid_model(
        train_sample_count=train_sample_count,
        test_sample_count=test_sample_count,
        seed=seed,
        model_family="gbr",
        test_profile_mix="stress",
    )
    stress_status_distribution = pd.concat(
        [
            _build_status_distribution(stress_baseline["predictions"], "baseline_only"),
            _build_status_distribution(stress_gbr["predictions"], "gbr"),
        ],
        ignore_index=True,
    )
    balanced_profile_summary = pd.concat(
        [
            _build_profile_type_summary(baseline["predictions"], "baseline_only"),
            _build_profile_type_summary(gbr["predictions"], "gbr"),
        ],
        ignore_index=True,
    )
    stress_profile_summary = pd.concat(
        [
            _build_profile_type_summary(stress_baseline["predictions"], "baseline_only"),
            _build_profile_type_summary(stress_gbr["predictions"], "gbr"),
        ],
        ignore_index=True,
    )

    balanced_metrics_path = output_dir / "balanced_model_comparison.csv"
    stress_metrics_path = output_dir / "stress_model_comparison.csv"
    balanced_status_path = output_dir / "balanced_status_distribution.csv"
    stress_status_path = output_dir / "stress_status_distribution.csv"
    balanced_profile_path = output_dir / "balanced_profile_type_summary.csv"
    stress_profile_path = output_dir / "stress_profile_type_summary.csv"
    baseline_path = output_dir / "baseline_predictions.csv"
    gbr_path = output_dir / "gbr_predictions.csv"
    fixture_path = output_dir / "fixture_report.csv"
    summary_path = output_dir / "summary.json"

    balanced_comparison.to_csv(balanced_metrics_path, index=False)
    stress_comparison.to_csv(stress_metrics_path, index=False)
    balanced_status_distribution.to_csv(balanced_status_path, index=False)
    stress_status_distribution.to_csv(stress_status_path, index=False)
    balanced_profile_summary.to_csv(balanced_profile_path, index=False)
    stress_profile_summary.to_csv(stress_profile_path, index=False)
    baseline["predictions"].to_csv(baseline_path, index=False)
    gbr["predictions"].to_csv(gbr_path, index=False)
    fixtures.to_csv(fixture_path, index=False)

    summary = {
        "baseline_metrics": baseline["metrics"],
        "gbr_metrics": gbr["metrics"],
        "balanced_comparison": balanced_comparison.to_dict(orient="records"),
        "stress_comparison": stress_comparison.to_dict(orient="records"),
        "balanced_status_distribution": balanced_status_distribution.to_dict(orient="records"),
        "stress_status_distribution": stress_status_distribution.to_dict(orient="records"),
        "train_sample_count": train_sample_count,
        "test_sample_count": test_sample_count,
        "seed": seed,
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return {
        "balanced_model_comparison": balanced_metrics_path,
        "stress_model_comparison": stress_metrics_path,
        "balanced_status_distribution": balanced_status_path,
        "stress_status_distribution": stress_status_path,
        "balanced_profile_type_summary": balanced_profile_path,
        "stress_profile_type_summary": stress_profile_path,
        "baseline_predictions": baseline_path,
        "gbr_predictions": gbr_path,
        "fixture_report": fixture_path,
        "summary": summary_path,
    }


def main() -> None:
    """CLI entry point for quick synthetic evaluation runs."""

    parser = argparse.ArgumentParser(description="Run synthetic evaluation for the scoring stage.")
    parser.add_argument("--train-samples", type=int, default=300)
    parser.add_argument("--test-samples", type=int, default=120)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out-dir", type=str, default="")
    args = parser.parse_args()

    comparison = compare_models(
        train_sample_count=args.train_samples,
        test_sample_count=args.test_samples,
        seed=args.seed,
        test_profile_mix="balanced",
    )
    stress_comparison = compare_models(
        train_sample_count=args.train_samples,
        test_sample_count=args.test_samples,
        seed=args.seed,
        test_profile_mix="stress",
    )
    fixture_report = build_fixture_report()

    print("\n[Scoring] Balanced Split Model Comparison")
    print(comparison.to_string(index=False))
    print("\n[Scoring] Stress Split Model Comparison")
    print(stress_comparison.to_string(index=False))
    print("\n[Scoring] Fixture Report")
    print(fixture_report.to_string(index=False))

    if args.out_dir:
        exported = export_evaluation_bundle(
            out_dir=args.out_dir,
            train_sample_count=args.train_samples,
            test_sample_count=args.test_samples,
            seed=args.seed,
        )
        print("\n[Scoring] Exported artifacts")
        print(json.dumps({key: str(value) for key, value in exported.items()}, indent=2))


if __name__ == "__main__":
    main()
