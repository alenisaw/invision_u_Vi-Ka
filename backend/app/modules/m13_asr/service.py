"""
File: service.py
Purpose: Main orchestration layer for the M13 ASR module.
"""

from __future__ import annotations

import asyncio
import logging

from .downloader import cleanup_paths, resolve_request_media
from .quality_checker import build_quality_summary, mark_unclear_segments
from .schemas import ASRRequest, ASRTranscriptResult
from .transcriber import GroqWhisperTranscriber


logger = logging.getLogger(__name__)


class ASRService:
    """Resolve media, transcribe speech, and return quality-aware ASR output."""

    def __init__(self, transcriber: GroqWhisperTranscriber | None = None) -> None:
        self.transcriber = transcriber or GroqWhisperTranscriber()

    def transcribe(self, request: ASRRequest) -> ASRTranscriptResult:
        """Run the full M13 flow for one media source."""

        resolved_media = resolve_request_media(request)
        try:
            transcription = self.transcriber.transcribe(
                resolved_media.path,
                language=request.language_hint,
            )
            segments = mark_unclear_segments(list(transcription.get("segments", [])))
            quality = build_quality_summary(
                transcript=str(transcription.get("transcript", "")),
                segments=segments,
                duration_seconds=float(transcription.get("audio_duration_seconds", 0.0) or 0.0),
            )
            return ASRTranscriptResult(
                candidate_id=request.candidate_id,
                transcript=str(transcription.get("transcript", "")),
                segments=segments,
                mean_confidence=quality.mean_confidence,
                unclear_ratio=quality.unclear_ratio,
                detected_languages=list(transcription.get("detected_languages", [])),
                audio_duration_seconds=quality.audio_duration_seconds,
                flags=quality.flags,
                requires_human_review=quality.requires_human_review,
                review_reasons=quality.review_reasons,
                transcriber_backend=str(transcription.get("transcriber_backend", "groq")),
                transcriber_model=str(transcription.get("transcriber_model", self.transcriber.model)),
            )
        finally:
            cleanup_paths(resolved_media.cleanup_paths)

    async def transcribe_async(self, request: ASRRequest) -> ASRTranscriptResult:
        """Run the blocking ASR path in a worker thread to protect the event loop."""

        return await asyncio.to_thread(self.transcribe, request)


asr_service = ASRService()


