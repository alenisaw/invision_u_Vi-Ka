"""
File: test_m6_m7_handoff.py
Purpose: Tests for the prepared M6 -> M7 explainability handoff.

Notes:
- This validates the contract before M7 exists.
"""

from __future__ import annotations

import unittest

from app.modules.m6_scoring.service import ScoringService
from app.modules.m6_scoring.synthetic_data import build_reference_fixtures


class ScoringExplainabilityHandoffTests(unittest.TestCase):
    """Validate the prepared explainability handoff payload."""

    def test_build_explainability_input_returns_expected_shape(self) -> None:
        """The handoff should contain score, factors, cautions, and signal context."""

        service = ScoringService()
        envelope = build_reference_fixtures()["balanced"]

        explainability_input = service.build_explainability_input(envelope)

        self.assertEqual(explainability_input.scoring_version, "m6-v1")
        self.assertTrue(explainability_input.program_id)
        self.assertEqual(len(explainability_input.sub_scores), 8)
        self.assertLessEqual(len(explainability_input.positive_factors), 3)
        self.assertGreater(len(explainability_input.signal_context), 0)
        self.assertEqual(explainability_input.candidate_id, envelope.candidate_id)


if __name__ == "__main__":
    unittest.main()


# File summary: test_m6_m7_handoff.py
# Covers the prepared handoff payload from M6 into the future M7.
