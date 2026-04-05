"""
File: quality_checker.py
Purpose: Explicit ASR quality checks and human-review routing for the ASR stage.
"""

from __future__ import annotations

from statistics import mean

from .schemas import ASRQualitySummary, ASRSegment


UNCLEAR_CONFIDENCE_MAX = 0.60
SHORT_DURATION_MAX_SECONDS = 60.0
LOW_MEAN_CONFIDENCE_MAX = 0.75
HIGH_UNCLEAR_RATIO_MIN = 0.20
LOW_AUDIO_QUALITY_CONFIDENCE_MAX = 0.55
LOW_AUDIO_QUALITY_UNCLEAR_RATIO_MIN = 0.35
LOW_SEGMENT_CONFIDENCE_VARIANCE_MAX = 0.003
LOW_SEGMENT_DURATION_VARIANCE_MAX = 4.0
LOW_HESITATION_DENSITY_MAX = 0.005
SPEECH_AUTHENTICITY_DURATION_MIN = 20.0
HESITATION_MARKERS = (" um ", " uh ", " erm ", " мм ", " эм ", " ээ ")


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, round(float(value), 4)))


def mark_unclear_segments(segments: list[ASRSegment]) -> list[ASRSegment]:
    """Mark low-confidence segments explicitly instead of hiding them."""
    updated_segments: list[ASRSegment] = []
    for segment in segments:
        updated_segments.append(
            segment.model_copy(
                update={"is_unclear": bool(segment.confidence < UNCLEAR_CONFIDENCE_MAX)}
            )
        )
    return updated_segments


def build_quality_summary(
    transcript: str,
    segments: list[ASRSegment],
    duration_seconds: float,
) -> ASRQualitySummary:
    """Compute compact ASR quality metrics and flags."""
    cleaned_transcript = transcript.strip()
    if segments:
        mean_confidence = _clamp_unit(
            sum(segment.confidence for segment in segments) / len(segments)
        )
        unclear_ratio = _clamp_unit(
            sum(1 for segment in segments if segment.is_unclear) / len(segments)
        )
        inferred_duration = max(duration_seconds, max(segment.end for segment in segments))
    else:
        mean_confidence = 0.0
        unclear_ratio = 0.0
        inferred_duration = max(duration_seconds, 0.0)

    flags: list[str] = []
    if not cleaned_transcript:
        flags.append("no_speech_detected")
    if inferred_duration and inferred_duration < SHORT_DURATION_MAX_SECONDS:
        flags.append("short_duration")
    if mean_confidence and mean_confidence < LOW_MEAN_CONFIDENCE_MAX:
        flags.append("low_asr_confidence")
    if unclear_ratio > HIGH_UNCLEAR_RATIO_MIN:
        flags.append("unclear_segments_high")
    if (
        mean_confidence
        and mean_confidence < LOW_AUDIO_QUALITY_CONFIDENCE_MAX
        and unclear_ratio > LOW_AUDIO_QUALITY_UNCLEAR_RATIO_MIN
    ):
        flags.append("low_audio_quality")
    if _speech_authenticity_risk(
        transcript=cleaned_transcript,
        segments=segments,
        duration_seconds=inferred_duration,
    ):
        flags.append("speech_authenticity_risk")

    review_reasons: list[str] = []
    critical_review_flags = {
        "no_speech_detected",
        "short_duration",
        "low_asr_confidence",
        "unclear_segments_high",
        "low_audio_quality",
    }
    for flag in flags:
        if flag in critical_review_flags:
            review_reasons.append(flag)

    requires_human_review = bool(review_reasons)
    if requires_human_review:
        flags.append("requires_human_review")

    return ASRQualitySummary(
        mean_confidence=mean_confidence,
        unclear_ratio=unclear_ratio,
        audio_duration_seconds=round(inferred_duration, 3),
        flags=list(dict.fromkeys(flags)),
        requires_human_review=requires_human_review,
        review_reasons=list(dict.fromkeys(review_reasons)),
    )


# File summary: quality_checker.py
# Derives explicit ASR quality metrics and review flags from normalized segments.


def _speech_authenticity_risk(
    *,
    transcript: str,
    segments: list[ASRSegment],
    duration_seconds: float,
) -> bool:
    """Return an advisory speech-authenticity flag for unnaturally uniform audio."""

    if len(segments) < 3 or duration_seconds < SPEECH_AUTHENTICITY_DURATION_MIN:
        return False

    confidences = [segment.confidence for segment in segments]
    durations = [max(0.0, segment.end - segment.start) for segment in segments]
    confidence_mean = mean(confidences)
    confidence_variance = mean((value - confidence_mean) ** 2 for value in confidences)
    duration_mean = mean(durations)
    duration_variance = mean((value - duration_mean) ** 2 for value in durations)

    normalized = f" {transcript.lower()} "
    words = normalized.split()
    hesitation_hits = sum(normalized.count(marker) for marker in HESITATION_MARKERS)
    hesitation_density = hesitation_hits / max(len(words), 1)

    return (
        confidence_mean >= 0.88
        and confidence_variance <= LOW_SEGMENT_CONFIDENCE_VARIANCE_MAX
        and duration_variance <= LOW_SEGMENT_DURATION_VARIANCE_MAX
        and hesitation_density <= LOW_HESITATION_DENSITY_MAX
    )
