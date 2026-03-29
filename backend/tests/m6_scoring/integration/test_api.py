"""
File: test_m1_m6_api.py
Purpose: API tests for the M6 gateway routes.
"""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.modules.m6_scoring.synthetic_data import build_reference_fixtures


class GatewayApiTests(unittest.TestCase):
    """Validate the initial API surface that exposes M6."""

    def setUp(self) -> None:
        self.client = TestClient(app)
        self.fixtures = build_reference_fixtures()

    def test_health_returns_ok(self) -> None:
        """Health endpoint should expose basic status information."""

        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertIn("version", body)

    def test_score_signals_route_scores_one_candidate(self) -> None:
        """Direct scoring endpoint should accept the canonical signal envelope."""

        payload = self.fixtures["balanced"].model_dump(mode="json")
        response = self.client.post("/api/v1/pipeline/score-signals", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["candidate_id"], payload["candidate_id"])
        self.assertIn("review_priority_index", body["data"])

    def test_score_signals_batch_returns_ranked_results(self) -> None:
        """Batch scoring endpoint should assign ranking positions."""

        payload = [
            self.fixtures["weak"].model_dump(mode="json"),
            self.fixtures["strong"].model_dump(mode="json"),
            self.fixtures["balanced"].model_dump(mode="json"),
        ]
        response = self.client.post("/api/v1/pipeline/score-signals/batch", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual([item["ranking_position"] for item in body["data"]], [1, 2, 3])

    def test_evaluate_synthetic_route_returns_metrics(self) -> None:
        """Synthetic evaluation endpoint should expose compact metrics."""

        response = self.client.post(
            "/api/v1/pipeline/score-signals/evaluate-synthetic?train_sample_count=40&test_sample_count=20&seed=9"
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertIn("mae", body["data"])
        self.assertIn("macro_f1", body["data"])
        self.assertIn("spearman_rank_correlation", body["data"])


if __name__ == "__main__":
    unittest.main()


# File summary: test_m1_m6_api.py
# Covers the health route and direct gateway access to M6 scoring.
