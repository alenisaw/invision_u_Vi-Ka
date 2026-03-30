from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.modules.m2_intake.schemas import CandidateIntakeRequest
from app.modules.m3_privacy.redactor import collect_known_names, redact_text, redact_texts


@dataclass(frozen=True)
class Layer1PII:
    """Encrypted PII — never sent to AI models."""

    snapshot: dict[str, Any]


@dataclass(frozen=True)
class Layer2Metadata:
    """Operational metadata — used for eligibility checks, not for scoring."""

    age_eligible: bool | None
    language_threshold_met: bool | None
    language_exam_type: str | None
    has_video: bool
    data_completeness: float
    data_flags: list[str]


@dataclass(frozen=True)
class Layer3ModelInput:
    """Redacted model input — the only data sent to LLM."""

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


def _compact_mapping(payload: dict[str, Any]) -> dict[str, Any]:
    compacted: dict[str, Any] = {}
    for key, value in payload.items():
        if value is None or value == "":
            continue
        if isinstance(value, dict):
            nested = _compact_mapping(value)
            if nested:
                compacted[key] = nested
            continue
        if isinstance(value, list):
            filtered_list = [item for item in value if item not in (None, "", [], {})]
            if filtered_list:
                compacted[key] = filtered_list
            continue
        compacted[key] = value
    return compacted


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
        payload: Raw intake request from M2.
        age_eligible: Pre-computed age eligibility from M2.
        language_threshold_met: Pre-computed language check from M2.
        data_completeness: Pre-computed completeness score from M2.
        data_flags: Pre-computed data flags from M2.
        video_transcript: ASR output (from M13 or empty).
        asr_confidence: ASR confidence score.
        asr_flags: ASR quality flags.

    Returns:
        SeparatedLayers with all three privacy layers.
    """
    personal_dict = payload.personal.model_dump(mode="json")
    parents_dict = payload.parents.model_dump(mode="json")
    known_names = collect_known_names(personal_dict, parents_dict)

    # Layer 1: only sensitive administrative fields (will be encrypted)
    layer1 = Layer1PII(
        snapshot=_compact_mapping(
            {
                "personal": {
                    "last_name": payload.personal.last_name,
                    "first_name": payload.personal.first_name,
                    "patronymic": payload.personal.patronymic,
                    "date_of_birth": payload.personal.date_of_birth,
                    "gender": payload.personal.gender,
                    "citizenship": payload.personal.citizenship,
                    "iin": payload.personal.iin,
                    "document_type": payload.personal.document_type,
                    "document_no": payload.personal.document_no,
                    "document_authority": payload.personal.document_authority,
                    "document_date": payload.personal.document_date,
                },
                "contacts": payload.contacts.model_dump(mode="json", exclude_none=True),
                "parents": payload.parents.model_dump(mode="json", exclude_none=True),
                "address": payload.address.model_dump(mode="json", exclude_none=True),
                "social_status": payload.social_status.model_dump(
                    mode="json",
                    exclude_none=True,
                ),
            }
        )
    )

    # Layer 2: operational metadata only
    layer2 = Layer2Metadata(
        age_eligible=age_eligible,
        language_threshold_met=language_threshold_met,
        language_exam_type=payload.academic.language_exam_type,
        has_video=bool(payload.content.video_url),
        data_completeness=data_completeness,
        data_flags=data_flags,
    )

    # Layer 3: redacted model input
    clean_essay = _clean_text(payload.content.essay_text)
    clean_experience = _clean_text(payload.content.experience_summary)
    clean_transcript = _clean_text(video_transcript)
    clean_projects = [
        _clean_text(p) or "" for p in payload.content.project_descriptions if p
    ]

    redacted_essay = redact_text(clean_essay, known_names) if clean_essay else None
    redacted_experience = (
        redact_text(clean_experience, known_names) if clean_experience else None
    )
    redacted_transcript = (
        redact_text(clean_transcript, known_names) if clean_transcript else None
    )
    redacted_projects = redact_texts(clean_projects, known_names)

    redacted_answers = [
        {
            "question_id": a.question_id,
            "answer": redact_text(a.answer, known_names),
        }
        for a in payload.internal_test.answers
    ]

    layer3 = Layer3ModelInput(
        video_transcript=redacted_transcript,
        essay_text=redacted_essay,
        internal_test_answers=redacted_answers,
        project_descriptions=redacted_projects,
        experience_summary=redacted_experience,
        asr_confidence=asr_confidence,
        asr_flags=asr_flags or [],
    )

    return SeparatedLayers(layer1=layer1, layer2=layer2, layer3=layer3)
