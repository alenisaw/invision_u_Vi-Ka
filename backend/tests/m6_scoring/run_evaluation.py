"""
File: run_evaluation.py
Purpose: Export a fresh M6 synthetic evaluation bundle into the local test results folder.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.modules.m6_scoring.evaluation import export_evaluation_bundle
from app.modules.m6_scoring.optimization import export_search_report


def _load_summary(path: Path) -> dict:
    """Read a summary json file if it exists."""

    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _build_reference_delta(reference_summary: dict, current_summary: dict) -> pd.DataFrame:
    """Create a compact before/after comparison against the frozen reference run."""

    reference_metrics = {
        "baseline_only": reference_summary.get("baseline_metrics", {}),
        "gbr": reference_summary.get("gbr_metrics") or reference_summary.get("hybrid_metrics", {}),
    }
    current_metrics = {
        "baseline_only": current_summary.get("baseline_metrics", {}),
        "gbr": current_summary.get("gbr_metrics", {}),
    }

    tracked_metrics = [
        "mae",
        "rmse",
        "r2",
        "macro_recall",
        "macro_f1",
        "spearman_rank_correlation",
        "top_k_overlap",
        "manual_review_rate",
        "uncertainty_rate",
        "high_confidence_rate",
        "fast_track_rate",
        "acceptance_rate",
        "strong_recommend_rate",
        "recommend_rate",
        "waitlist_rate",
        "declined_rate",
    ]

    rows: list[dict[str, float | str | None]] = []
    for model_name in ("baseline_only", "gbr"):
        for metric_name in tracked_metrics:
            before = reference_metrics.get(model_name, {}).get(metric_name)
            after = current_metrics.get(model_name, {}).get(metric_name)
            rows.append(
                {
                    "model": model_name,
                    "metric": metric_name,
                    "before": before,
                    "after": after,
                    "delta": round(after - before, 4) if before is not None and after is not None else None,
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    """Generate the latest synthetic evaluation artifacts for local inspection."""

    output_dir = REPO_ROOT / "backend/tests/m6_scoring/results/latest"
    output_dir.mkdir(parents=True, exist_ok=True)

    for child in output_dir.iterdir():
        if child.is_file():
            child.unlink()

    exported = export_evaluation_bundle(
        out_dir=output_dir,
        train_sample_count=300,
        test_sample_count=120,
        seed=42,
    )
    exported.update(
        export_search_report(
            out_dir=output_dir,
            train_sample_count=300,
            test_sample_count=120,
            seed=42,
        )
    )

    reference_dir = REPO_ROOT / "backend/tests/m6_scoring/results/pre_tuning_reference"
    current_summary = _load_summary(output_dir / "summary.json")
    reference_summary = _load_summary(reference_dir / "summary.json")
    delta_frame = _build_reference_delta(reference_summary, current_summary)
    delta_csv_path = output_dir / "vs_pre_tuning.csv"
    delta_json_path = output_dir / "vs_pre_tuning.json"
    delta_frame.to_csv(delta_csv_path, index=False)
    delta_json_path.write_text(delta_frame.to_json(orient="records", indent=2), encoding="utf-8")

    exported["vs_pre_tuning_csv"] = delta_csv_path
    exported["vs_pre_tuning_json"] = delta_json_path
    print(json.dumps({key: str(value) for key, value in exported.items()}, indent=2))


if __name__ == "__main__":
    main()


