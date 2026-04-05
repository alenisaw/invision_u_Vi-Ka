from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.core.text_sanitizer import mask_profanity, mask_profanity_list
from app.modules.intake.schemas import CandidateIntakeRequest
from app.modules.privacy.redactor import collect_known_names, redact_text, redact_texts


@dataclass(frozen=True)
class Layer1PII:
    """Encrypted PII never sent to AI models."""

    snapshot: dict[str, Any]


@dataclass(frozen=True)
class Layer2Metadata:
    """Operational metadata used for eligibility checks, not for scoring."""

    age_eligible: bool | None
    language_threshold_met: bool | None
    language_exam_type: str | None
    has_video: bool
    data_completeness: float
    data_flags: list[str]


@dataclass(frozen=True)
class Layer3ModelInput:
    """Redacted analytical input sent to downstream model stages."""

    video_transcript: str | None
    essay_text: str | None
    internal_test_answers: list[dict[str, str]]
    project_descriptions: list[str]
    experience_summary: str | None
    asr_confidence: float | None
    asr_flags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SeparatedLayers:
    """All three layers produced by the separator."""

    layer1: Layer1PII
    layer2: Layer2Metadata
    layer3: Layer3ModelInput


_STRIP_HTML_RE = re.compile(r"<[^>]+>")


def _clean_text(text: str | None) -> str | None:
    """Strip HTML tags and normalize whitespace."""
    if not text:
        return text
    cleaned = _STRIP_HTML_RE.sub("", text)
    cleaned = " ".join(cleaned.split())
    return cleaned


def separate(
    payload: CandidateIntakeRequest,
    *,
    age_eligible: bool | None,
    language_threshold_met: bool | None,
    data_completeness: float,
    data_flags: list[str],
    video_transcript: str | None = None,
    asr_confidence: float | None = None,
    asr_flags: list[str] | None = None,
) -> SeparatedLayers:
    """Split intake data into three privacy layers.

    Args:
        payload: Raw input intake request.
        age_eligible: Pre-computed age eligibility from input intake.
        language_threshold_met: Pre-computed language check from input intake.
        data_completeness: Pre-computed completeness score from input intake.
        data_flags: Pre-computed data flags from input intake.
        video_transcript: ASR output when media was transcribed.
        asr_confidence: ASR confidence score.
        asr_flags: ASR quality flags.

    Returns:
        SeparatedLayers with all three privacy layers.
    """
    personal_dict = payload.personal.model_dump(mode="json")
    parents_dict = payload.parents.model_dump(mode="json")
    known_names = collect_known_names(personal_dict, parents_dict)

    layer1 = Layer1PII(snapshot=payload.model_dump(mode="json"))

    layer2 = Layer2Metadata(
        age_eligible=age_eligible,
        language_threshold_met=language_threshold_met,
        language_exam_type=payload.academic.language_exam_type,
        has_video=bool(payload.content.video_url),
        data_completeness=data_completeness,
        data_flags=data_flags,
    )

    clean_essay = mask_profanity(_clean_text(payload.content.essay_text))
    clean_transcript = mask_profanity(_clean_text(video_transcript))

    redacted_essay = redact_text(clean_essay, known_names) if clean_essay else None
    redacted_transcript = redact_text(clean_transcript, known_names) if clean_transcript else None

    redacted_answers = [
        {
            "question_id": answer.question_id,
            "answer": redact_text(mask_profanity(answer.answer) or "", known_names),
        }
        for answer in payload.internal_test.answers
    ]

    layer3 = Layer3ModelInput(
        video_transcript=redacted_transcript,
        essay_text=redacted_essay,
        internal_test_answers=redacted_answers,
        project_descriptions=[],
        experience_summary=None,
        asr_confidence=asr_confidence,
        asr_flags=asr_flags or [],
    )

    return SeparatedLayers(layer1=layer1, layer2=layer2, layer3=layer3)
