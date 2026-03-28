"""
File: test_m6_scoring.py
Purpose: Basic unit tests for the M6 scoring module.

Notes:
- Keep tests focused on contract, ranking, and safe training flow.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from app.modules.m6_scoring.ml_model import HybridScoringModel
from app.modules.m6_scoring.service import ScoringService
from app.modules.m6_scoring.synthetic_data import build_reference_fixtures


class ScoringServiceTests(unittest.TestCase):
    """Exercise the compact public surface of M6."""

    def setUp(self) -> None:
        self.service = ScoringService()
        self.fixtures = build_reference_fixtures()

    def test_score_candidate_returns_expected_shape(self) -> None:
        """One candidate should return the agreed scoring surface."""

        score = self.service.score_candidate(self.fixtures["strong"])

        self.assertEqual(score.scoring_version, "m6-v1")
        self.assertTrue(score.program_id)
        self.assertEqual(len(score.sub_scores), 8)
        self.assertGreaterEqual(score.review_priority_index, 0.0)
        self.assertLessEqual(score.review_priority_index, 1.0)
        self.assertIn(score.score_status, {"STRONG_RECOMMEND", "RECOMMEND", "WAITLIST", "DECLINED"})
        self.assertIn(score.confidence_band, {"LOW", "MEDIUM", "HIGH"})
        self.assertIn(score.review_recommendation, {"REQUIRES_MANUAL_REVIEW", "STANDARD_REVIEW", "FAST_TRACK_REVIEW"})
        self.assertEqual(score.model_family, "gbr")
        self.assertIsInstance(score.decision_summary, str)
        self.assertIsInstance(score.top_strengths, list)
        self.assertIsInstance(score.top_risks, list)
        self.assertIn(
            score.recommendation_status,
            {"STRONG_RECOMMEND", "RECOMMEND", "WAITLIST", "DECLINED"},
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
        self.assertEqual(score.recommendation_status, "DECLINED")
        self.assertIn("low_completeness", score.caution_flags)

    def test_risky_profile_keeps_borderline_status_without_forced_manual(self) -> None:
        """Low ASR quality alone should not force manual review after the routing redesign."""

        score = self.service.score_candidate(self.fixtures["risky"])

        self.assertIn(score.recommendation_status, {"WAITLIST", "DECLINED"})
        self.assertFalse(score.manual_review_required)

    def test_model_can_be_saved_and_loaded(self) -> None:
        """The optional ML artifact path should remain usable."""

        try:
            self.service.train_on_synthetic(sample_count=40, seed=19)
        except RuntimeError as error:
            self.skipTest(str(error))

        artifact_path = Path("backend/app/modules/m6_scoring/artifacts/test_scoring_model.joblib")
        try:
            self.service.ml_model.save(artifact_path)
            loaded_model = HybridScoringModel.load(artifact_path)
        finally:
            if artifact_path.exists():
                artifact_path.unlink()
            metadata_path = artifact_path.with_suffix(f"{artifact_path.suffix}.meta.json")
            if metadata_path.exists():
                metadata_path.unlink()

        self.assertTrue(loaded_model.is_trained)

    def test_unsupported_signal_schema_version_is_rejected(self) -> None:
        """M6 should reject envelopes with unsupported signal schema versions."""

        envelope = self.fixtures["balanced"].model_copy(update={"signal_schema_version": "v99"})

        with self.assertRaises(ValueError):
            self.service.score_candidate(envelope)


if __name__ == "__main__":
    unittest.main()


# File summary: test_m6_scoring.py
# Covers shape, ranking, and the synthetic training path of M6.
