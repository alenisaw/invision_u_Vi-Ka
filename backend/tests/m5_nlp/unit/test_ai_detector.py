from __future__ import annotations

import unittest

from backend.app.modules.m5_nlp.ai_detector import (
    ai_writing_risk_score,
    authenticity_confidence,
    authenticity_risk_score,
    specificity_score,
    transcript_authenticity_risk_score,
    voice_consistency_score,
)


class AIDetectorTests(unittest.TestCase):
    def test_specificity_score_prefers_concrete_text(self) -> None:
        generic = "I am highly motivated and want to make a positive impact."
        concrete = "I led a team of 6 students and shipped a registration app used in our club."
        self.assertGreater(specificity_score(concrete), specificity_score(generic))

    def test_voice_consistency_score_returns_normalized_value(self) -> None:
        score = voice_consistency_score("I built a project for students", "I built a project for students and tested it")
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_ai_risk_is_advisory_and_normalized(self) -> None:
        risk = ai_writing_risk_score(
            "I am highly motivated and want to make a positive impact.",
            "I built a project and can explain how it worked.",
            "Student community app with real users.",
        )
        confidence = authenticity_confidence("essay", "transcript")
        self.assertGreaterEqual(risk, 0.0)
        self.assertLessEqual(risk, 1.0)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)

    def test_transcript_authenticity_risk_supports_transcript_only_cases(self) -> None:
        risk = transcript_authenticity_risk_score(
            transcript_text="I am passionate and highly motivated to make an impact.",
            project_text="Built a school scheduling bot with two classmates.",
        )
        generic_risk = authenticity_risk_score(
            primary_text="I am passionate and highly motivated to make an impact.",
            project_text="",
        )
        self.assertGreaterEqual(risk, 0.0)
        self.assertLessEqual(risk, 1.0)
        self.assertLess(risk, generic_risk)


if __name__ == "__main__":
    unittest.main()
