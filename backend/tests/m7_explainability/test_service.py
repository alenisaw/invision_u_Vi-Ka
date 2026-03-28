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
        self.assertTrue(any(block.evidence for block in report.positive_factors))

    def test_low_quality_case_surfaces_guidance(self) -> None:
        scoring = ScoringService()
        explainability = ExplainabilityService()
        envelope = build_reference_fixtures()["incomplete"]

        handoff = scoring.build_explainability_input(envelope)
        report = explainability.build_report(handoff)

        self.assertTrue(report.caution_blocks or report.data_quality_notes)
        self.assertTrue(report.reviewer_guidance)
        self.assertTrue(any(block.severity in {"warning", "critical"} for block in report.caution_blocks))

    def test_generate_uses_passed_score_contract(self) -> None:
        scoring = ScoringService()
        explainability = ExplainabilityService()
        envelope = build_reference_fixtures()["strong"]
        score = scoring.score_candidate(envelope)

        report = self.async_run(explainability.generate(envelope.candidate_id, envelope, score))

        self.assertEqual(report.recommendation_status, score.recommendation_status)
        self.assertEqual(report.review_recommendation, score.review_recommendation)

    def async_run(self, coroutine):
        import asyncio

        return asyncio.run(coroutine)


if __name__ == "__main__":
    unittest.main()


# File summary: test_service.py
# Covers summary, positive factors, and reviewer guidance generation for M7.
