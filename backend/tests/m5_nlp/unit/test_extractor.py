from __future__ import annotations

import unittest
from uuid import uuid4

from backend.app.modules.m5_nlp.extractor import HeuristicSignalExtractor
from backend.app.modules.m5_nlp.schemas import M5ExtractionRequest


class HeuristicSignalExtractorTests(unittest.TestCase):
    def build_request(self) -> M5ExtractionRequest:
        return M5ExtractionRequest(
            candidate_id=uuid4(),
            selected_program="Innovative IT Product Design and Development",
            essay_text="I built a student app, led a team sprint, and want to create useful digital products.",
            video_transcript="I learned from failure, improved the prototype, and coordinated my team during deadlines.",
            project_descriptions=["Built a student product MVP and tested it with users."],
            experience_summary="I mentor peers and keep improving through feedback.",
            internal_test_answers=[{"question_id": "q1", "answer_text": "I choose the fair option because responsibility matters."}],
        )

    def test_extract_returns_core_signal_bundle(self) -> None:
        extractor = HeuristicSignalExtractor()
        signals = extractor.extract(self.build_request())

        self.assertIn("leadership_indicators", signals)
        self.assertIn("motivation_clarity", signals)
        self.assertIn("program_alignment", signals)
        self.assertIn("ethical_reasoning", signals)
        self.assertGreater(signals["program_alignment"].value, 0.0)

    def test_extract_skips_empty_sources_cleanly(self) -> None:
        extractor = HeuristicSignalExtractor()
        signals = extractor.extract(M5ExtractionRequest(candidate_id=uuid4(), selected_program="Foundation Year"))
        self.assertEqual(signals, {})


if __name__ == "__main__":
    unittest.main()
