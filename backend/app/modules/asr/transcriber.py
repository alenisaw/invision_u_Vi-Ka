"""
File: transcriber.py
Purpose: API-backed Whisper Large V3 Turbo integration for the ASR stage.
"""

from __future__ import annotations

import math
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import httpx

try:
    from dotenv import dotenv_values
except ImportError:  # pragma: no cover
    dotenv_values = None  # type: ignore[assignment]

from .schemas import ASRSegment


VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}
ASR_API_BASE_URL = "https://api.groq.com/openai/v1"
ASR_MODEL_NAME = "whisper-large-v3-turbo"


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, round(float(value), 4)))


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _segment_confidence(raw_segment: dict[str, Any]) -> float:
    if "confidence" in raw_segment:
        return _clamp_unit(_safe_float(raw_segment.get("confidence"), 0.0))
    if "avg_logprob" in raw_segment:
        return _clamp_unit(math.exp(_safe_float(raw_segment.get("avg_logprob"), -1.0)))
    no_speech_prob = raw_segment.get("no_speech_prob")
    if no_speech_prob is not None:
        return _clamp_unit(1.0 - _safe_float(no_speech_prob, 1.0))
    text = str(raw_segment.get("text", "")).strip()
    return 0.5 if text else 0.0


def _load_env_api_key() -> str:
    if dotenv_values is None:
        return ""
    repo_root = Path(__file__).resolve().parents[4]
    for env_name in (".env.local", ".env"):
        env_path = repo_root / env_name
        if not env_path.exists():
            continue
        values = dotenv_values(env_path)
        key = str(values.get("M13_ASR_API_KEY") or values.get("GROQ_API_KEY") or "").strip()
        if key:
            return key
    return ""


class GroqWhisperTranscriber:
    """Thin OpenAI-compatible client for Groq Whisper transcription."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout_s: float = 90.0,
    ) -> None:
        self.api_key = (
            api_key
            or os.getenv("M13_ASR_API_KEY")
            or os.getenv("GROQ_API_KEY")
            or _load_env_api_key()
            or ""
        ).strip()
        self.base_url = (base_url or os.getenv("M13_ASR_BASE_URL") or ASR_API_BASE_URL).rstrip("/")
        self.model = (model or os.getenv("M13_ASR_MODEL") or ASR_MODEL_NAME).strip()
        self.timeout_s = timeout_s

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def transcribe(self, media_path: str | Path, language: str = "auto") -> dict[str, Any]:
        """Transcribe media and normalize the response into a compact internal dict."""
        if not self.enabled:
            raise RuntimeError("ASR API key is not set.")

        prepared_audio, cleanup_paths = self._prepare_audio_input(Path(media_path))
        try:
            payload = self._transcribe_audio(prepared_audio, language=language)
            return self._normalize_payload(payload, fallback_language=language)
        finally:
            for cleanup_path in cleanup_paths:
                if cleanup_path.exists():
                    if cleanup_path.is_dir():
                        for child in cleanup_path.iterdir():
                            child.unlink(missing_ok=True)
                        cleanup_path.rmdir()
                    else:
                        cleanup_path.unlink(missing_ok=True)

    def _prepare_audio_input(self, media_path: Path) -> tuple[Path, tuple[Path, ...]]:
        if media_path.suffix.lower() not in VIDEO_EXTENSIONS:
            return media_path, ()
        temp_dir = Path(tempfile.mkdtemp(prefix="m13_audio_"))
        audio_path = temp_dir / f"{media_path.stem}.wav"
        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(media_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            str(audio_path),
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=False)
        except FileNotFoundError as exc:
            raise RuntimeError("ffmpeg is not installed or not available in PATH.") from exc
        if result.returncode != 0:
            raise RuntimeError("ffmpeg failed to extract audio for ASR transcription.")
        return audio_path, (temp_dir,)

    def _transcribe_audio(self, audio_path: Path, language: str = "auto") -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        data: dict[str, Any] = {
            "model": self.model,
            "temperature": "0",
            "response_format": "verbose_json",
        }
        if language and language != "auto":
            data["language"] = language

        with audio_path.open("rb") as file_handle:
            files = {"file": (audio_path.name, file_handle, "audio/wav")}
            with httpx.Client(timeout=self.timeout_s) as client:
                response = client.post(
                    f"{self.base_url}/audio/transcriptions",
                    headers=headers,
                    data=data,
                    files=files,
                )
                response.raise_for_status()
        return response.json()

    def _normalize_payload(self, payload: dict[str, Any], fallback_language: str) -> dict[str, Any]:
        transcript = str(payload.get("text", "")).strip()
        payload_language = str(payload.get("language", "")).strip()
        normalized_segments: list[ASRSegment] = []

        raw_segments = payload.get("segments", [])
        if isinstance(raw_segments, list):
            for raw_segment in raw_segments:
                if not isinstance(raw_segment, dict):
                    continue
                text = str(raw_segment.get("text", "")).strip()
                if not text:
                    continue
                start = max(0.0, _safe_float(raw_segment.get("start"), 0.0))
                end = max(start, _safe_float(raw_segment.get("end"), start))
                language = str(raw_segment.get("language", "")).strip() or payload_language
                normalized_segments.append(
                    ASRSegment(
                        start=round(start, 3),
                        end=round(end, 3),
                        text=text,
                        confidence=_segment_confidence(raw_segment),
                        language=language or (fallback_language if fallback_language != "auto" else ""),
                    )
                )

        duration = _safe_float(payload.get("duration"), 0.0)
        if not normalized_segments and transcript:
            normalized_segments.append(
                ASRSegment(
                    start=0.0,
                    end=max(duration, 0.0),
                    text=transcript,
                    confidence=0.5,
                    language=payload_language or (fallback_language if fallback_language != "auto" else ""),
                )
            )

        detected_languages = sorted(
            {segment.language for segment in normalized_segments if segment.language}
        )
        if not detected_languages and payload_language:
            detected_languages = [payload_language]

        inferred_duration = duration or (normalized_segments[-1].end if normalized_segments else 0.0)
        return {
            "transcript": transcript,
            "segments": normalized_segments,
            "detected_languages": detected_languages,
            "audio_duration_seconds": round(max(inferred_duration, 0.0), 3),
            "transcriber_backend": "groq",
            "transcriber_model": self.model,
        }


# File summary: transcriber.py
# Calls Groq Whisper Large V3 Turbo via API and normalizes transcript segments.
