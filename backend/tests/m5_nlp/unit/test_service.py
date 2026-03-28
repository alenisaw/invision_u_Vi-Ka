"""
File: test_service.py
Purpose: Unit tests for the M5 NLP signal extraction service.
"""

from __future__ import annotations

import sys
import unittest
from uuid import uuid4

from app.modules.m5_nlp.schemas import M5ExtractionRequest
from app.modules.m5_nlp.service import NLPSignalExtractionService
from app.modules.m6_scoring.service import ScoringService

REPORT_SIGNAL_ORDER = (
    "leadership_indicators",
    "growth_trajectory",
    "motivation_clarity",
    "agency_signals",
    "learning_agility",
    "clarity_score",
    "ethical_reasoning",
    "program_alignment",
    "goal_specificity",
    "future_goals_alignment",
    "challenges_overcome",
    "resilience_evidence",
    "leadership_reflection",
    "teamwork_problem_solving",
    "support_network",
    "english_growth",
)

REPORT_SUB_SCORE_ORDER = (
    "leadership_potential",
    "growth_trajectory",
    "motivation_clarity",
    "initiative_agency",
    "learning_agility",
    "communication_clarity",
    "ethical_reasoning",
    "program_fit",
)


def _ordered_signal_names(signal_names: list[str]) -> list[str]:
    """Keep the terminal report stable across runs."""

    prioritized = [signal_name for signal_name in REPORT_SIGNAL_ORDER if signal_name in signal_names]
    remaining = sorted(signal_name for signal_name in signal_names if signal_name not in REPORT_SIGNAL_ORDER)
    return prioritized + remaining


def _format_probability_line(name: str, value: float) -> str:
    """Render one score line in the requested terminal-friendly format."""

    return f"{name}: {value:.3f}"


def _build_terminal_report(envelope, score) -> str:
    """Build a compact synthetic payload report for stdout."""

    lines = [
        "",
        "[M5 synthetic payload]",
        f"signal_count: {len(envelope.signals)}",
        "signals:",
    ]

    for signal_name in _ordered_signal_names(list(envelope.signals)):
        lines.append(_format_probability_line(signal_name, envelope.signals[signal_name].value))

    lines.append(f"data_flags: {envelope.data_flags}")
    lines.append(f"m5_model_version: {envelope.m5_model_version}")
    lines.append("sub_scores:")
    lines.append(_format_probability_line("review_priority_index", score.review_priority_index))

    for sub_score_name in REPORT_SUB_SCORE_ORDER:
        lines.append(_format_probability_line(sub_score_name, score.sub_scores[sub_score_name]))

    return "\n".join(lines)


class FakeTranscriptionClient:
    """Simple test double for media transcription."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.called = False

    def transcribe_media(self, media_path: str, language: str = "auto") -> dict:
        self.called = True
        return {"text": self.text, "language": language, "media_path": media_path}


class M5SignalExtractionServiceTests(unittest.TestCase):
    """Validate the public M5 extraction surface."""

    def setUp(self) -> None:
        self.service = NLPSignalExtractionService(transcription_client=FakeTranscriptionClient(text=""))

    def build_request(self, transcript_text: str = "") -> M5ExtractionRequest:
        """Create a Foundation Year interview-style payload for extraction tests."""

        return M5ExtractionRequest(
            candidate_id=uuid4(),
            completeness=0.92,
            selected_program="Foundation Year",
            essay_text=(
                "I want to join the Foundation Year at inVision U because it will prepare me for bachelor study "
                "and strengthen my academic English. My long-term goal is to build digital products for students "
                "from small towns. When our first prototype failed, feedback from my teacher and support from my "
                "family helped me improve the project instead of quitting."
            ),
            video_transcript=transcript_text,
            experience_summary=(
                "I mentor younger students in my town, help run community workshops, and my family supports my "
                "decision to study at inVision U. A school teacher inspires me to keep learning."
            ),
            project_descriptions=[
                "I led a school design sprint, coordinated tasks, and resolved a conflict about deadlines.",
                "I created an app for club registration and practiced presenting it in English every week.",
            ],
            internal_test_answers=[
                {
                    "question_id": "q1",
                    "answer_text": "I would choose the fair option because responsibility and honesty matter.",
                }
            ],
        )

    def test_extract_signals_returns_foundation_interview_envelope(self) -> None:
        """M5 should detect the Foundation Year interview criteria in the candidate text."""

        request = self.build_request(
            transcript_text=(
                "Why are you applying to inVision U? I want to study in the Foundation Year because it will prepare "
                "me for bachelor study in digital products and improve my academic English. "
                "The biggest challenge I overcame was when our first prototype failed and some teammates wanted to quit, "
                "but support from my family and my physics teacher helped me continue. "
                "My long-term goal is to create digital services for students from regional schools, and this program "
                "will help me build the English, teamwork, and design skills for that goal. "
                "To me, a leader listens, takes responsibility, and keeps the team moving; I showed that when I organized "
                "tasks and motivated my team during a school sprint. "
                "In one team situation I took the role of coordinator, resolved a conflict about deadlines, and helped "
                "the group split the work. "
                "My family supports my choice to join inVision U, and my older sister inspires me because she continued "
                "studying despite obstacles. "
                "In English, my dream is to create products that help rural students. I practice speaking every day, "
                "watch lessons in English, and I can already present my project confidently."
            )
        )

        envelope = self.service.extract_signals(request)

        self.assertEqual(envelope.signal_schema_version, "v1")
        self.assertEqual(envelope.m5_model_version, "heuristic-groq-v1")
        self.assertEqual(envelope.selected_program, "Foundation Year")
        self.assertTrue(envelope.program_id)
        self.assertGreater(len(envelope.signals), 12)
        self.assertNotIn("insufficient_interview_coverage", envelope.data_flags)
        self.assertNotIn("requires_human_review", envelope.data_flags)
        for signal_name in [
            "leadership_indicators",
            "growth_trajectory",
            "motivation_clarity",
            "program_alignment",
            "goal_specificity",
            "future_goals_alignment",
            "challenges_overcome",
            "resilience_evidence",
            "leadership_reflection",
            "teamwork_problem_solving",
            "support_network",
            "english_growth",
            "clarity_score",
        ]:
            self.assertIn(signal_name, envelope.signals)
            self.assertGreaterEqual(envelope.signals[signal_name].value, 0.0)
            self.assertLessEqual(envelope.signals[signal_name].value, 1.0)
            self.assertGreater(len(envelope.signals[signal_name].evidence), 0)

        score = ScoringService().score_candidate(envelope)
        self.assertGreaterEqual(score.review_priority_index, 0.0)
        self.assertLessEqual(score.review_priority_index, 1.0)
        self.assertGreater(score.sub_scores["leadership_potential"], 0.50)
        self.assertGreater(score.sub_scores["motivation_clarity"], 0.50)
        self.assertGreater(score.sub_scores["learning_agility"], 0.50)
        print(_build_terminal_report(envelope, score), file=sys.stderr, flush=True)

    def test_extract_signals_uses_transcription_fallback_when_needed(self) -> None:
        """M5 should use the transcription client and still recover interview criteria."""

        fake_client = FakeTranscriptionClient(
            text=(
                "I want to join the Foundation Year because it will prepare me for university study and improve my "
                "English. The hardest challenge I overcame was rebuilding a failed project, and support from my "
                "mother and teacher helped me continue. My long-term goal is to study digital product design and "
                "build tools for regional students. A leader listens and takes responsibility, and I showed that "
                "when I coordinated my team and solved a deadline conflict. In English, my dream is to launch an app "
                "for rural schools, and I practice speaking every day."
            )
        )
        service = NLPSignalExtractionService(transcription_client=fake_client)
        request = self.build_request(transcript_text="")
        request = request.model_copy(update={"interview_media_path": "mock_interview.mp4"})

        envelope = service.extract_signals(request)

        self.assertTrue(fake_client.called)
        self.assertIn("clarity_score", envelope.signals)
        self.assertIn("english_growth", envelope.signals)
        self.assertNotIn("insufficient_interview_coverage", envelope.data_flags)
        self.assertNotIn("requires_human_review", envelope.data_flags)

    def test_extract_signals_ignores_exam_scores_and_flags_missing_interview_content(self) -> None:
        """Exam-score mentions should not count as interview-quality evidence."""

        request = M5ExtractionRequest(
            candidate_id=uuid4(),
            completeness=0.92,
            selected_program="Foundation Year",
            essay_text="My IELTS score is 6.5 and my ENT score is 95.",
            video_transcript=(
                "I scored 95 on ENT, got IELTS 6.5, and uploaded my TOEFL certificate."
            ),
        )

        envelope = self.service.extract_signals(request)

        self.assertIn("insufficient_interview_coverage", envelope.data_flags)
        self.assertIn("requires_human_review", envelope.data_flags)
        self.assertNotIn("english_growth", envelope.signals)
        self.assertNotIn("motivation_clarity", envelope.signals)


if __name__ == "__main__":
    unittest.main()


# File summary: test_service.py
# Covers canonical envelope generation, M6 compatibility, and transcription fallback for M5.
