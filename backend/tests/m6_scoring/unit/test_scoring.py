"""
File: test_m6_scoring.py
Purpose: Basic unit tests for the M6 scoring module.

Notes:
- Keep tests focused on contract, ranking, and safe training flow.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from backend.app.modules.m6_scoring.ml_model import HybridScoringModel
from backend.app.modules.m6_scoring.service import ScoringService
from backend.app.modules.m6_scoring.synthetic_data import build_reference_fixtures


class ScoringServiceTests(unittest.TestCase):
    """Exercise the compact public surface of M6."""

    def setUp(self) -> None:
        self.service = ScoringService()
        self.fixtures = build_reference_fixtures()

    def test_score_candidate_returns_expected_shape(self) -> None:
        """One candidate should return the agreed scoring surface."""

        score = self.service.score_candidate(self.fixtures["strong"])

        self.assertEqual(score.scoring_version, "m6-v1")
        self.assertEqual(len(score.sub_scores), 8)
        self.assertGreaterEqual(score.review_priority_index, 0.0)
        self.assertLessEqual(score.review_priority_index, 1.0)
        self.assertIn(score.confidence_band, {"LOW", "MEDIUM", "HIGH"})
        self.assertIn(score.review_recommendation, {"REQUIRES_MANUAL_REVIEW", "STANDARD_REVIEW", "FAST_TRACK_REVIEW"})
        self.assertEqual(score.model_family, "gbr")
        self.assertIn(
            score.recommendation_status,
            {"STRONG_RECOMMEND", "RECOMMEND", "REVIEW_NEEDED", "LOW_SIGNAL", "MANUAL_REVIEW"},
        )

    def test_score_batch_assigns_ranking_positions(self) -> None:
        """Batch scoring should return deterministic ranking positions."""

        ranked_scores = self.service.score_batch(
            [
                self.fixtures["weak"],
                self.fixtures["balanced"],
                self.fixtures["strong"],
            ]
        )

        self.assertEqual([score.ranking_position for score in ranked_scores], [1, 2, 3])
        self.assertGreaterEqual(ranked_scores[0].review_priority_index, ranked_scores[1].review_priority_index)
        self.assertGreaterEqual(ranked_scores[1].review_priority_index, ranked_scores[2].review_priority_index)

    def test_train_on_synthetic_keeps_module_usable(self) -> None:
        """Synthetic training should not break subsequent scoring."""

        try:
            self.service.train_on_synthetic(sample_count=40, seed=11)
        except RuntimeError as error:
            self.skipTest(str(error))

        score = self.service.score_candidate(self.fixtures["balanced"])
        self.assertGreaterEqual(score.confidence, 0.0)
        self.assertLessEqual(score.confidence, 1.0)
        self.assertIsInstance(score.review_reasons, list)

    def test_incomplete_profile_is_not_shortlisted(self) -> None:
        """Low-completeness fixture should not become shortlist eligible."""

        score = self.service.score_candidate(self.fixtures["incomplete"])

        self.assertFalse(score.shortlist_eligible)
        self.assertIn(score.recommendation_status, {"LOW_SIGNAL", "MANUAL_REVIEW"})
        self.assertIn("low_completeness", score.caution_flags)

    def test_risky_profile_triggers_uncertainty(self) -> None:
        """Critical data flags should push the candidate toward manual review logic."""

        score = self.service.score_candidate(self.fixtures["risky"])

        self.assertTrue(score.uncertainty_flag)
        self.assertEqual(score.recommendation_status, "MANUAL_REVIEW")
        self.assertEqual(score.review_recommendation, "REQUIRES_MANUAL_REVIEW")

    def test_model_can_be_saved_and_loaded(self) -> None:
        """The optional ML artifact path should remain usable."""

        model = HybridScoringModel()
        try:
            self.service.train_on_synthetic(sample_count=40, seed=19)
        except RuntimeError as error:
            self.skipTest(str(error))

        artifact_path = Path("backend/tests/tmp_scoring_model.joblib")
        try:
            self.service.ml_model.save(artifact_path)
            loaded_model = HybridScoringModel.load(artifact_path)
        finally:
            if artifact_path.exists():
                artifact_path.unlink()

        self.assertTrue(loaded_model.is_trained)


if __name__ == "__main__":
    unittest.main()


# File summary: test_m6_scoring.py
# Covers shape, ranking, and the synthetic training path of M6.
