"""
File: test_evaluation_bundle.py
Purpose: Local smoke tests for the M6 evaluation bundle.

Notes:
- Keep these focused on evaluation outputs used by notebooks and exports.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from backend.app.modules.m6_scoring.evaluation import (
    build_fixture_report,
    compare_models,
    export_evaluation_bundle,
)


class M6EvaluationBundleTests(unittest.TestCase):
    """Exercise local evaluation helpers that support the notebook bundle."""

    def test_compare_models_returns_supported_rows(self) -> None:
        """The comparison helper should return baseline plus available ML models."""

        frame = compare_models(train_sample_count=30, test_sample_count=15, seed=4)

        self.assertIn("baseline_only", set(frame["mode"]))
        self.assertIn("gbr", set(frame["mode"]))
        self.assertIn("mode", frame.columns)
        self.assertIn("mae", frame.columns)
        self.assertIn("high_confidence_rate", frame.columns)
        self.assertGreaterEqual(len(frame), 2)

    def test_build_fixture_report_returns_known_fixtures(self) -> None:
        """The fixed fixture report should remain available for notebook inspection."""

        frame = build_fixture_report()

        self.assertGreaterEqual(len(frame), 5)
        self.assertIn("fixture", frame.columns)
        self.assertIn("status", frame.columns)

    def test_export_bundle_writes_expected_files(self) -> None:
        """Export should materialize csv/json artifacts inside the workspace."""

        output_dir = Path("backend/tests/m6_scoring/results/test_export_bundle")
        try:
            exported = export_evaluation_bundle(output_dir, train_sample_count=20, test_sample_count=10, seed=6)
            for path in exported.values():
                self.assertTrue(Path(path).exists())
            self.assertIn("balanced_model_comparison", exported)
            self.assertIn("stress_model_comparison", exported)
            self.assertIn("gbr_predictions", exported)
        finally:
            if output_dir.exists():
                for child in output_dir.iterdir():
                    child.unlink()
                output_dir.rmdir()


if __name__ == "__main__":
    unittest.main()


# File summary: test_evaluation_bundle.py
# Covers comparison, fixture reporting, and artifact export for the M6 bundle.
