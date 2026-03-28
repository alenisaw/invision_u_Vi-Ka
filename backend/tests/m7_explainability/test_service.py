"""
File: test_service.py
Purpose: Content-level tests for the M7 explainability service.
"""

from __future__ import annotations

import unittest

from backend.app.modules.m6_scoring.service import ScoringService
from backend.app.modules.m6_scoring.synthetic_data import build_reference_fixtures
from backend.app.modules.m7_explainability.service import ExplainabilityService


class ExplainabilityServiceTests(unittest.TestCase):
    """Validate that M7 returns actual reviewer-facing content, not just shape."""

    def test_build_report_returns_summary_and_blocks(self) -> None:
        scoring = ScoringService()
        explainability = ExplainabilityService()
        envelope = build_reference_fixtures()["balanced"]

        handoff = scoring.build_explainability_input(envelope)
        report = explainability.build_report(handoff)

        self.assertEqual(report.candidate_id, envelope.candidate_id)
        self.assertTrue(report.summary)
        self.assertGreaterEqual(len(report.positive_factors), 1)
        self.assertIsInstance(report.reviewer_guidance, str)

    def test_low_quality_case_surfaces_guidance(self) -> None:
        scoring = ScoringService()
        explainability = ExplainabilityService()
        envelope = build_reference_fixtures()["incomplete"]

        handoff = scoring.build_explainability_input(envelope)
        report = explainability.build_report(handoff)

        self.assertTrue(report.caution_blocks or report.data_quality_notes)
        self.assertTrue(report.reviewer_guidance)


if __name__ == "__main__":
    unittest.main()


# File summary: test_service.py
# Covers summary, positive factors, and reviewer guidance generation for M7.
