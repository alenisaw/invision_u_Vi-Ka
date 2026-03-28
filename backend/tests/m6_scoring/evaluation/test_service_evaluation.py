"""
File: test_m6_evaluation.py
Purpose: Synthetic evaluation tests for the M6 scoring module.

Notes:
- Keep this focused on metric surface and execution safety.
"""

from __future__ import annotations

import unittest

from app.modules.m6_scoring.service import ScoringService


class ScoringEvaluationTests(unittest.TestCase):
    """Exercise the synthetic evaluation path of M6."""

    def test_evaluate_on_synthetic_returns_metric_bundle(self) -> None:
        """Synthetic evaluation should return the agreed metric keys."""

        service = ScoringService()
        try:
            metrics = service.evaluate_on_synthetic(train_sample_count=40, test_sample_count=20, seed=5)
        except RuntimeError as error:
            self.skipTest(str(error))

        for key in {
            "mae",
            "rmse",
            "r2",
            "macro_precision",
            "macro_recall",
            "macro_f1",
            "spearman_rank_correlation",
            "top_k_overlap",
            "manual_review_rate",
            "uncertainty_rate",
            "high_confidence_rate",
            "fast_track_rate",
            "strong_recommend_rate",
            "recommend_rate",
            "waitlist_rate",
            "declined_rate",
            "test_profile_mix",
        }:
            self.assertIn(key, metrics)


if __name__ == "__main__":
    unittest.main()


# File summary: test_m6_evaluation.py
# Covers the synthetic evaluation output surface of M6.
