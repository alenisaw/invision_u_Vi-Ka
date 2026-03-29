"""
File: test_m6_notebook_bundle.py
Purpose: Bundle-level tests for notebook and export helpers.
"""

from __future__ import annotations

import unittest

from app.modules.m6_scoring.evaluation import compare_models


class NotebookBundleTests(unittest.TestCase):
    """Validate the synthetic evaluation bundle used by the notebook."""

    def test_comparison_contains_baseline_and_model_rows(self) -> None:
        """Comparison output should expose baseline and the configured models."""

        frame = compare_models(train_sample_count=24, test_sample_count=12, seed=8)

        self.assertIn("baseline_only", set(frame["mode"]))
        self.assertIn("gbr", set(frame["mode"]))
        self.assertIn("manual_review_rate", frame.columns)
        self.assertIn("fast_track_rate", frame.columns)


if __name__ == "__main__":
    unittest.main()


# File summary: test_m6_notebook_bundle.py
# Covers the comparison output used by the M6 notebook flow.
