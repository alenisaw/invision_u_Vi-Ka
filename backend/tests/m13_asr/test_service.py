from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from backend.app.modules.m13_asr import downloader as downloader_module
from backend.app.modules.m13_asr.downloader import ResolvedMedia, resolve_request_media
from backend.app.modules.m13_asr.quality_checker import build_quality_summary, mark_unclear_segments
from backend.app.modules.m13_asr.schemas import ASRRequest, ASRSegment
from backend.app.modules.m13_asr.service import ASRService
from backend.app.modules.m13_asr.transcriber import GroqWhisperTranscriber


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "backend" / "tests"


class _FakeTranscriber:
    model = "whisper-large-v3-turbo"

    def transcribe(self, media_path: str | Path, language: str = "auto") -> dict:
        return {
            "transcript": "I launched a community project and led a small team.",
            "segments": [
                ASRSegment(start=0.0, end=32.0, text="I launched a community project.", confidence=0.91, language="en"),
                ASRSegment(start=32.0, end=65.0, text="And led a small team.", confidence=0.88, language="en"),
            ],
            "detected_languages": ["en"],
            "audio_duration_seconds": 65.0,
            "transcriber_backend": "groq",
            "transcriber_model": self.model,
        }


class TestM13Downloader(unittest.TestCase):
    def test_resolve_request_media_accepts_trusted_local_path(self) -> None:
        with tempfile.NamedTemporaryFile(dir=TEST_ROOT, suffix=".mp4", delete=False) as handle:
            media_path = Path(handle.name)
        try:
            request = ASRRequest(candidate_id=uuid4(), media_path=str(media_path))
            resolved = resolve_request_media(request)
            self.assertEqual(resolved.path, media_path.resolve())
            self.assertEqual(resolved.source_kind, "local")
        finally:
            media_path.unlink(missing_ok=True)

    def test_resolve_request_media_blocks_untrusted_local_path(self) -> None:
        request = ASRRequest(candidate_id=uuid4(), media_path="C:/Windows/not_allowed.mp4")
        with self.assertRaises(RuntimeError):
            resolve_request_media(request)

    def test_resolve_request_media_prefers_ytdlp_for_page_urls(self) -> None:
        fake_resolved = ResolvedMedia(path=TEST_ROOT / "download.webm", source_kind="yt_dlp")
        request = ASRRequest(candidate_id=uuid4(), video_url="https://youtube.com/watch?v=abc123")

        with patch.object(
            downloader_module,
            "_download_media_with_ytdlp",
            return_value=fake_resolved,
        ) as ytdlp_mock, patch.object(
            downloader_module,
            "_download_media_with_request",
            side_effect=AssertionError("direct request fallback should not run for page URLs"),
        ):
            resolved = resolve_request_media(request)

        self.assertEqual(resolved.source_kind, "yt_dlp")
        ytdlp_mock.assert_called_once()


class TestM13Quality(unittest.TestCase):
    def test_quality_checker_sets_flags_for_low_quality_audio(self) -> None:
        segments = mark_unclear_segments(
            [
                ASRSegment(start=0.0, end=10.0, text="short", confidence=0.41, language="en"),
                ASRSegment(start=10.0, end=20.0, text="clip", confidence=0.45, language="en"),
            ]
        )
        summary = build_quality_summary("short clip", segments, duration_seconds=20.0)

        self.assertIn("short_duration", summary.flags)
        self.assertIn("low_asr_confidence", summary.flags)
        self.assertIn("unclear_segments_high", summary.flags)
        self.assertTrue(summary.requires_human_review)


class TestM13Service(unittest.TestCase):
    def test_service_returns_structured_transcript_result(self) -> None:
        with tempfile.NamedTemporaryFile(dir=TEST_ROOT, suffix=".wav", delete=False) as handle:
            media_path = Path(handle.name)
        try:
            service = ASRService(transcriber=_FakeTranscriber())
            request = ASRRequest(candidate_id=uuid4(), media_path=str(media_path))

            result = service.transcribe(request)

            self.assertTrue(result.transcript)
            self.assertEqual(result.transcriber_model, "whisper-large-v3-turbo")
            self.assertEqual(result.detected_languages, ["en"])
            self.assertGreaterEqual(result.mean_confidence, 0.0)
            self.assertEqual(len(result.segments), 2)
            self.assertFalse(result.requires_human_review)
        finally:
            media_path.unlink(missing_ok=True)


class TestM13TranscriberNormalization(unittest.TestCase):
    def test_normalize_payload_maps_segments(self) -> None:
        transcriber = GroqWhisperTranscriber(api_key="test-key")
        normalized = transcriber._normalize_payload(
            {
                "text": "Hello world",
                "language": "en",
                "duration": 4.2,
                "segments": [
                    {"start": 0.0, "end": 2.0, "text": "Hello", "confidence": 0.9},
                    {"start": 2.0, "end": 4.2, "text": "world", "avg_logprob": -0.1},
                ],
            },
            fallback_language="auto",
        )

        self.assertEqual(normalized["transcript"], "Hello world")
        self.assertEqual(len(normalized["segments"]), 2)
        self.assertEqual(normalized["detected_languages"], ["en"])
        self.assertGreater(normalized["segments"][1].confidence, 0.0)


if __name__ == "__main__":
    unittest.main()
