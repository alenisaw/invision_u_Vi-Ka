"""
File: run_evaluation.py
Purpose: Export a fresh scoring evaluation bundle into the local test results folder.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.modules.scoring.evaluation import export_evaluation_bundle
from app.modules.scoring.optimization import export_search_report


def main() -> None:
    """Generate the latest synthetic evaluation artifacts for local inspection."""

    output_dir = REPO_ROOT / "backend/tests/scoring/results/current"
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

    for key, value in exported.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
