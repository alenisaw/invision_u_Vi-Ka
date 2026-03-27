"""
File: evaluation.py
Purpose: Reproducible synthetic evaluation utilities for the M6 module.

Notes:
- Keep evaluation logic outside notebooks so results stay reproducible.
- Use synthetic data for sanity checks, not for real-world quality claims.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import mean_absolute_error, mean_squared_error, precision_recall_fscore_support, r2_score

from .rules import map_recommendation_status
from .service import ScoringService
from .synthetic_data import build_reference_fixtures, generate_synthetic_dataset


def _evaluate_samples(service: ScoringService, test_samples) -> tuple[dict[str, float | int | str], pd.DataFrame]:
    """Evaluate one scoring service against a synthetic holdout split."""

    rows: list[dict[str, float | str | bool]] = []
    for labeled_sample in test_samples:
        score = service.score_candidate(labeled_sample.envelope)
        rows.append(
            {
                "candidate_id": str(labeled_sample.envelope.candidate_id),
                "target_rpi": labeled_sample.target_rpi,
                "predicted_rpi": score.review_priority_index,
                "target_status": map_recommendation_status(
                    score=labeled_sample.target_rpi,
                    completeness=labeled_sample.envelope.completeness,
                    uncertainty_flag=False,
                ),
                "predicted_status": score.recommendation_status,
                "confidence": score.confidence,
                "confidence_band": score.confidence_band,
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
        results["predicted_status"],
        average="macro",
        zero_division=0,
    )
    correlation = spearmanr(results["target_rpi"], results["predicted_rpi"]).correlation
    top_k = min(10, len(results))
    true_top = set(results.nlargest(top_k, "target_rpi").index.tolist())
    predicted_top = set(results.nlargest(top_k, "predicted_rpi").index.tolist())

    metrics = {
        "sample_count": int(len(results)),
        "mae": round(float(mean_absolute_error(results["target_rpi"], results["predicted_rpi"])), 4),
        "rmse": round(float(math.sqrt(mean_squared_error(results["target_rpi"], results["predicted_rpi"]))), 4),
        "r2": round(float(r2_score(results["target_rpi"], results["predicted_rpi"])), 4),
        "macro_precision": round(float(precision), 4),
        "macro_recall": round(float(recall), 4),
        "macro_f1": round(float(f1_score), 4),
        "spearman_rank_correlation": round(float(correlation if correlation == correlation else 0.0), 4),
        "top_k_overlap": round(len(true_top & predicted_top) / top_k, 4),
        "manual_review_rate": round(float(results["uncertainty_flag"].mean()), 4),
        "high_confidence_rate": round(float((results["confidence_band"] == "HIGH").mean()), 4),
        "fast_track_rate": round(float((results["review_recommendation"] == "FAST_TRACK_REVIEW").mean()), 4),
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
        except RuntimeError:
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
                "uncertainty_flag": score.uncertainty_flag,
                "shortlist_eligible": score.shortlist_eligible,
                "caution_flags": ", ".join(score.caution_flags),
            }
        )
    return pd.DataFrame(rows).sort_values(["rpi", "confidence"], ascending=[False, False]).reset_index(drop=True)


def export_evaluation_bundle(out_dir: str | Path, train_sample_count: int = 300, test_sample_count: int = 120, seed: int = 42) -> dict[str, Path]:
    """Export comparison metrics and prediction tables for notebook or review use."""

    output_dir = Path(out_dir)
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

    balanced_metrics_path = output_dir / "balanced_model_comparison.csv"
    stress_metrics_path = output_dir / "stress_model_comparison.csv"
    baseline_path = output_dir / "baseline_predictions.csv"
    gbr_path = output_dir / "gbr_predictions.csv"
    fixture_path = output_dir / "fixture_report.csv"
    summary_path = output_dir / "summary.json"

    balanced_comparison.to_csv(balanced_metrics_path, index=False)
    stress_comparison.to_csv(stress_metrics_path, index=False)
    baseline["predictions"].to_csv(baseline_path, index=False)
    gbr["predictions"].to_csv(gbr_path, index=False)
    fixtures.to_csv(fixture_path, index=False)

    summary = {
        "baseline_metrics": baseline["metrics"],
        "gbr_metrics": gbr["metrics"],
        "balanced_comparison": balanced_comparison.to_dict(orient="records"),
        "stress_comparison": stress_comparison.to_dict(orient="records"),
        "train_sample_count": train_sample_count,
        "test_sample_count": test_sample_count,
        "seed": seed,
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return {
        "balanced_model_comparison": balanced_metrics_path,
        "stress_model_comparison": stress_metrics_path,
        "baseline_predictions": baseline_path,
        "gbr_predictions": gbr_path,
        "fixture_report": fixture_path,
        "summary": summary_path,
    }


def main() -> None:
    """CLI entry point for quick synthetic evaluation runs."""

    parser = argparse.ArgumentParser(description="Run synthetic evaluation for the M6 scoring module.")
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

    print("\n[M6] Balanced Split Model Comparison")
    print(comparison.to_string(index=False))
    print("\n[M6] Stress Split Model Comparison")
    print(stress_comparison.to_string(index=False))
    print("\n[M6] Fixture Report")
    print(fixture_report.to_string(index=False))

    if args.out_dir:
        exported = export_evaluation_bundle(
            out_dir=args.out_dir,
            train_sample_count=args.train_samples,
            test_sample_count=args.test_samples,
            seed=args.seed,
        )
        print("\n[M6] Exported artifacts")
        print(json.dumps({key: str(value) for key, value in exported.items()}, indent=2))


if __name__ == "__main__":
    main()


# File summary: evaluation.py
# Centralizes synthetic evaluation, comparison, export, and CLI entry for M6.
