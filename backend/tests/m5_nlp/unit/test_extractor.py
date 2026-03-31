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

    def test_behavioral_cues_capture_indirect_leadership_and_growth(self) -> None:
        extractor = HeuristicSignalExtractor()
        request = M5ExtractionRequest(
            candidate_id=uuid4(),
            selected_program="Creative Engineering",
            essay_text=(
                "When our prototype failed, I rebuilt the plan with the team, redistributed tasks, and kept weekly meetings going "
                "until we delivered a better version."
            ),
            video_transcript=(
                "At first the group was stuck, so I coordinated the work, listened to each teammate, and helped us recover after mistakes."
            ),
        )

        signals = extractor.extract(request)

        self.assertIn("leadership_indicators", signals)
        self.assertIn("growth_trajectory", signals)
        self.assertGreater(signals["leadership_indicators"].value, 0.40)
        self.assertGreater(signals["growth_trajectory"].value, 0.40)

    def test_behavioral_cues_work_for_mixed_language_initiative(self) -> None:
        extractor = HeuristicSignalExtractor()
        request = M5ExtractionRequest(
            candidate_id=uuid4(),
            selected_program="Digital Media and Marketing",
            video_transcript=(
                "Я сама opened a school media club, found a teacher adviser, and ran weekly sessions where we recorded short interviews."
            ),
        )

        signals = extractor.extract(request)

        self.assertIn("agency_signals", signals)
        self.assertIn("self_started_projects", signals)
        self.assertGreater(signals["agency_signals"].value, 0.35)

    def test_self_labels_without_examples_do_not_overinflate_scores(self) -> None:
        extractor = HeuristicSignalExtractor()
        request = M5ExtractionRequest(
            candidate_id=uuid4(),
            selected_program="Foundation Year",
            essay_text=(
                "I am a leader, very proactive, highly motivated, responsible, and initiative-driven."
            ),
        )

        signals = extractor.extract(request)

        self.assertLess(signals["agency_signals"].value, 0.60)
        self.assertLess(signals["leadership_indicators"].value, 0.60)


if __name__ == "__main__":
    unittest.main()
