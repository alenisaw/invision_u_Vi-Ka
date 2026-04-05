"""
File: test_service.py
Purpose: Content-level tests for the explanation stage service.
"""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, MagicMock

from app.modules.scoring.service import ScoringService
from app.modules.scoring.synthetic_data import build_reference_fixtures
from app.modules.explanation.service import ExplanationService


class ExplanationServiceTests(unittest.TestCase):
    """Validate that the explanation stage returns reviewer-facing content, not just shape."""

    def test_build_report_returns_summary_and_blocks(self) -> None:
        scoring = ScoringService()
        explainability = ExplanationService()
        envelope = build_reference_fixtures()["balanced"]

        handoff = scoring.build_explanation_input(envelope)
        report = explainability.build_report(handoff)

        self.assertEqual(report.candidate_id, envelope.candidate_id)
        self.assertTrue(report.summary)
        self.assertGreaterEqual(len(report.positive_factors), 1)
        self.assertIsInstance(report.reviewer_guidance, str)
        self.assertTrue(any(block.evidence for block in report.positive_factors))
        self.assertTrue(any("подтверж" in block.summary.lower() for block in report.positive_factors))
        self.assertIn("кандидат", report.summary.lower())

    def test_low_quality_case_surfaces_guidance(self) -> None:
        scoring = ScoringService()
        explainability = ExplanationService()
        envelope = build_reference_fixtures()["incomplete"]

        handoff = scoring.build_explanation_input(envelope)
        report = explainability.build_report(handoff)

        self.assertTrue(report.caution_blocks or report.data_quality_notes)
        self.assertTrue(report.reviewer_guidance)
        self.assertTrue(any(block.severity in {"warning", "critical"} for block in report.caution_blocks))
        self.assertTrue(any(ord(char) > 127 for char in report.reviewer_guidance))

    def test_generate_uses_passed_score_contract(self) -> None:
        scoring = ScoringService()
        explainability = ExplanationService()
        envelope = build_reference_fixtures()["strong"]
        score = scoring.score_candidate(envelope)

        report = self.async_run(explainability.generate(envelope.candidate_id, envelope, score))

        self.assertEqual(report.recommendation_status, score.recommendation_status)
        self.assertEqual(report.review_recommendation, score.review_recommendation)

    def async_run(self, coroutine):
        import asyncio

        return asyncio.run(coroutine)


class ExplanationServiceGenerateTests(unittest.IsolatedAsyncioTestCase):
    """Validate the async generation path used by the pipeline."""

    async def test_generate_reuses_provided_score_and_persists_report(self) -> None:
        scoring = ScoringService()
        envelope = build_reference_fixtures()["balanced"]
        score = scoring.score_candidate(envelope)
        explainability = ExplanationService(session=MagicMock())
        explainability.repository = AsyncMock()
        explainability.scoring_service.build_explanation_input = MagicMock(
            wraps=scoring.build_explanation_input
        )

        report = await explainability.generate(envelope.candidate_id, envelope, score)

        self.assertEqual(report.candidate_id, envelope.candidate_id)
        self.assertEqual(report.review_priority_index, score.review_priority_index)
        self.assertEqual(report.recommendation_status, score.recommendation_status)
        explainability.scoring_service.build_explanation_input.assert_called_once()

        explainability.repository.upsert_candidate_explanation.assert_awaited_once()
        persisted = explainability.repository.upsert_candidate_explanation.await_args.kwargs
        persisted_report = report.model_dump(mode="json")
        self.assertEqual(persisted["candidate_id"], envelope.candidate_id)
        self.assertEqual(persisted["summary"], report.summary)
        self.assertEqual(persisted["positive_factors"], persisted_report["positive_factors"])
        self.assertEqual(persisted["caution_flags"], persisted_report["caution_blocks"])
        self.assertEqual(persisted["data_quality_notes"], report.data_quality_notes)
        self.assertEqual(persisted["reviewer_guidance"], report.reviewer_guidance)
        explainability.repository.create_audit_log.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
