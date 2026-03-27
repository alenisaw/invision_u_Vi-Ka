"""
File: client.py
Purpose: Optional Groq-backed interview transcription client for M5.

Notes:
- This adapts the logic from `transcribe_interview.py` into the backend module.
- The client is only used when a transcript is not provided directly.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

try:
    from groq import Groq
except ImportError:  # pragma: no cover
    Groq = None  # type: ignore[assignment]


VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}
AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".mpeg", ".mpga"}
MEDIA_EXTENSIONS = VIDEO_EXTENSIONS | AUDIO_EXTENSIONS


def ensure_groq_api_key() -> None:
    """Validate that the Groq API key is present before transcription."""

    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("GROQ_API_KEY is not set.")
    if Groq is None:
        raise RuntimeError("groq package is not installed. Install it with `pip install groq`.")


def is_video_file(path: Path) -> bool:
    """Check whether a path points to a supported video container."""

    return path.suffix.lower() in VIDEO_EXTENSIONS


def serialize_response(response: Any) -> dict[str, Any]:
    """Normalize Groq SDK responses into plain dictionaries."""

    if hasattr(response, "model_dump"):
        return response.model_dump()
    if hasattr(response, "to_dict"):
        return response.to_dict()
    if isinstance(response, dict):
        return response
    return {"text": getattr(response, "text", "")}


class GroqTranscriptionClient:
    """Thin wrapper around the Groq transcription API."""

    def __init__(self, model: str = "whisper-large-v3-turbo") -> None:
        self.model = model

    def extract_audio(self, video_path: Path) -> Path:
        """Extract mono 16k WAV audio from a video file via ffmpeg."""

        temp_dir = Path(tempfile.mkdtemp(prefix="m5_audio_"))
        audio_path = temp_dir / f"{video_path.stem}.wav"
        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            str(audio_path),
        ]

        try:
            result = subprocess.run(command, capture_output=True, text=True)
        except FileNotFoundError as exc:
            raise RuntimeError("ffmpeg is not installed or is not available in PATH.") from exc

        if result.returncode != 0:
            raise RuntimeError("ffmpeg failed to extract audio from the video file.")
        return audio_path

    def transcribe_file(self, file_path: Path, language: str = "auto") -> dict[str, Any]:
        """Transcribe an audio file using Groq Whisper."""

        ensure_groq_api_key()
        client = Groq()

        request: dict[str, Any] = {
            "model": self.model,
            "temperature": 0,
            "response_format": "verbose_json",
        }
        if language != "auto":
            request["language"] = language

        with file_path.open("rb") as file_handle:
            response = client.audio.transcriptions.create(
                file=(file_path.name, file_handle),
                **request,
            )
        return serialize_response(response)

    def transcribe_media(self, media_path: str | Path, language: str = "auto") -> dict[str, Any]:
        """Transcribe a media file, extracting audio first for videos."""

        path = Path(media_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Interview media file not found: {path}")
        if path.suffix.lower() not in MEDIA_EXTENSIONS:
            raise RuntimeError(f"Unsupported interview media type: {path.suffix}")

        working_path = self.extract_audio(path) if is_video_file(path) else path
        payload = self.transcribe_file(working_path, language=language)
        payload["text"] = payload.get("text", "")
        return payload


# File summary: client.py
# Adapts the root transcription script into a reusable Groq client for M5.
