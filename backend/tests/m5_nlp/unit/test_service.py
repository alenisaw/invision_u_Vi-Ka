"""
File: test_service.py
Purpose: Unit tests for the M5 NLP signal extraction service.
"""

from __future__ import annotations

import unittest
from uuid import uuid4

from app.modules.m5_nlp.schemas import M5ExtractionRequest
from app.modules.m5_nlp.service import NLPSignalExtractionService
from app.modules.m6_scoring.service import ScoringService

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
        self.service = NLPSignalExtractionService(
            transcription_client=FakeTranscriptionClient(text=""),
            enable_llm=False,
        )

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
                "I am applying to the Foundation Year because it will prepare me for bachelor study and improve my academic English. "
                "My goal is to build digital services for students from regional schools. "
                "When our first prototype failed, I reorganized the team, solved a deadline conflict, and kept the group moving. "
                "My family and teacher supported me, and I practice English every day by presenting my projects."
            )
        )

        envelope = self.service.extract_signals(request)

        self.assertEqual(envelope.signal_schema_version, "v1")
        self.assertEqual(envelope.m5_model_version, "heuristic-v1")
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

        self.assertGreater(envelope.signals["leadership_indicators"].value, 0.30)
        self.assertGreater(envelope.signals["motivation_clarity"].value, 0.30)
        self.assertGreater(envelope.signals["learning_agility"].value, 0.20)

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
        service = NLPSignalExtractionService(
            transcription_client=fake_client,
            enable_llm=False,
        )
        request = self.build_request(transcript_text="")
        request = request.model_copy(update={"interview_media_path": "mock_interview.mp4"})

        envelope = service.extract_signals(request)

        self.assertTrue(fake_client.called)
        self.assertIn("clarity_score", envelope.signals)
        self.assertIn("english_growth", envelope.signals)
        self.assertNotIn("insufficient_interview_coverage", envelope.data_flags)
        self.assertNotIn("requires_human_review", envelope.data_flags)

    def test_extract_signals_builds_authenticity_signal_for_transcript_only_case(self) -> None:
        request = M5ExtractionRequest(
            candidate_id=uuid4(),
            completeness=0.86,
            selected_program="Digital Media and Marketing",
            video_transcript=(
                "I want to study digital media because I already record short interviews, edit videos for school events, "
                "and test ways to reach new audiences. Last semester I helped our debate club publish weekly clips and "
                "learned how different formats affect engagement."
            ),
            project_descriptions=[
                "Edited weekly club videos and tracked which clips students actually watched."
            ],
        )

        envelope = self.service.extract_signals(request)

        self.assertIn("authenticity_risk", envelope.signals)
        self.assertNotIn("ai_writing_risk", envelope.signals)
        self.assertEqual(envelope.signals["authenticity_risk"].source[0], "video_transcript")

    def test_extract_signals_uses_essay_when_video_transcript_absent(self) -> None:
        request = M5ExtractionRequest(
            candidate_id=uuid4(),
            completeness=0.88,
            selected_program="Creative Engineering",
            essay_text=(
                "I built a prototype lamp, learned from mistakes, and want to study creative engineering so I can "
                "combine design with practical technology projects."
            ),
        )

        envelope = self.service.extract_signals(request)

        self.assertIn("motivation_clarity", envelope.signals)
        self.assertIn("clarity_score", envelope.signals)
        self.assertEqual(envelope.signals["clarity_score"].source, ["essay"])
        self.assertIn("missing_video_transcript", envelope.data_flags)

    def test_extract_signals_combines_essay_and_video_transcript_when_both_exist(self) -> None:
        request = M5ExtractionRequest(
            candidate_id=uuid4(),
            completeness=0.91,
            selected_program="Digital Media and Marketing",
            essay_text=(
                "I want to study digital media because I already run a small school content team and I care about "
                "storytelling that helps local communities."
            ),
            video_transcript=(
                "In the interview I explained how I organize shoots, edit clips, and test what formats people "
                "actually watch."
            ),
        )

        envelope = self.service.extract_signals(request)

        self.assertIn("specificity_score", envelope.signals)
        self.assertIn("essay", envelope.signals["specificity_score"].source)
        self.assertIn("video_transcript", envelope.signals["specificity_score"].source)
        self.assertIn("essay_transcript_consistency", envelope.signals)

    def test_extract_signals_marks_transcript_replacement_when_essay_is_missing(self) -> None:
        request = M5ExtractionRequest(
            candidate_id=uuid4(),
            completeness=0.89,
            selected_program="Creative Engineering",
            essay_text="",
            video_transcript=(
                "I explained how I rebuilt a broken prototype, learned from the failure, "
                "and kept iterating until the team could demo the final version."
            ),
        )

        envelope = self.service.extract_signals(request)

        self.assertIn("essay_replaced_by_video_transcript", envelope.data_flags)
        self.assertNotIn("missing_essay", envelope.data_flags)
        self.assertNotIn("missing_video_transcript", envelope.data_flags)
        self.assertIn("clarity_score", envelope.signals)

    def test_extract_signals_recovers_initiative_from_video_transcript(self) -> None:
        request = M5ExtractionRequest(
            candidate_id=uuid4(),
            completeness=0.90,
            selected_program="Creative Engineering",
            video_transcript=(
                "At school I opened two clubs, organized a robotics club, and set up a small makerspace so younger "
                "students could build simple prototypes after class. Later I ran weekly sessions myself and recruited volunteers."
            ),
        )

        envelope = self.service.extract_signals(request)
        score = ScoringService().score_candidate(envelope)

        self.assertIn("agency_signals", envelope.signals)
        self.assertIn("self_started_projects", envelope.signals)
        self.assertGreater(score.sub_scores["initiative_agency"], 0.30)

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
