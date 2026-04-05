"""
File: test_explanation_handoff.py
Purpose: Tests for the prepared scoring-to-explanation handoff.
"""

from __future__ import annotations

import unittest

from app.modules.scoring.service import ScoringService
from app.modules.scoring.synthetic_data import build_reference_fixtures


class ScoringExplanationHandoffTests(unittest.TestCase):
    """Validate the prepared explanation handoff payload."""

    def test_build_explanation_input_returns_expected_shape(self) -> None:
        """The handoff should contain score, factors, cautions, and signal context."""

        service = ScoringService()
        envelope = build_reference_fixtures()["balanced"]

        explanation_input = service.build_explanation_input(envelope)

        self.assertEqual(explanation_input.scoring_version, "scoring-v1")
        self.assertTrue(explanation_input.program_id)
        self.assertEqual(len(explanation_input.sub_scores), 8)
        self.assertLessEqual(len(explanation_input.positive_factors), 3)
        self.assertGreater(len(explanation_input.signal_context), 0)
        self.assertEqual(explanation_input.candidate_id, envelope.candidate_id)


if __name__ == "__main__":
    unittest.main()
