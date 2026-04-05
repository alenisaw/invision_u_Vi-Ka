"""
File: test_notebook_bundle.py
Purpose: Bundle-level tests for scoring export helpers.
"""

from __future__ import annotations

import unittest

from app.modules.scoring.evaluation import compare_models


class ScoringBundleTests(unittest.TestCase):
    """Validate the synthetic evaluation bundle used by export tooling."""

    def test_comparison_contains_baseline_and_model_rows(self) -> None:
        """Comparison output should expose baseline and the configured models."""

        frame = compare_models(train_sample_count=24, test_sample_count=12, seed=8)

        self.assertIn("baseline_only", set(frame["mode"]))
        self.assertIn("gbr", set(frame["mode"]))
        self.assertIn("manual_review_rate", frame.columns)
        self.assertIn("fast_track_rate", frame.columns)


if __name__ == "__main__":
    unittest.main()
