from __future__ import annotations

from app.modules.m4_profile.schemas import CandidateProfile, ModelInput, ProfileMetadata
from app.modules.m9_storage.models import Candidate, CandidateMetadata, CandidateModelInput


def assemble(
    candidate: Candidate,
    metadata: CandidateMetadata,
    model_input: CandidateModelInput,
) -> CandidateProfile:
    """Build a unified CandidateProfile from ORM objects.

    Args:
        candidate: Base candidate record.
        metadata: Layer 2 operational metadata.
        model_input: Layer 3 redacted model input.

    Returns:
        CandidateProfile ready for downstream modules (M5, M6).
    """
    profile_metadata = ProfileMetadata(
        age_eligible=metadata.age_eligible,
        language_threshold_met=metadata.language_threshold_met,
        language_exam_type=metadata.language_exam_type,
        has_video=metadata.has_video,
        data_completeness=metadata.data_completeness or 0.0,
        data_flags=metadata.data_flags if isinstance(metadata.data_flags, list) else [],
    )

    layer3 = ModelInput(
        video_transcript=model_input.video_transcript,
        essay_text=model_input.essay_text,
        internal_test_answers=(
            model_input.internal_test_answers
            if isinstance(model_input.internal_test_answers, list)
            else []
        ),
        project_descriptions=(
            model_input.project_descriptions
            if isinstance(model_input.project_descriptions, list)
            else []
        ),
        experience_summary=model_input.experience_summary,
        asr_confidence=model_input.asr_confidence,
        asr_flags=(
            model_input.asr_flags
            if isinstance(model_input.asr_flags, list)
            else []
        ),
    )

    data_flags = list(profile_metadata.data_flags)
    data_flags.extend(_extra_flags(layer3))
    data_flags = list(dict.fromkeys(data_flags))

    return CandidateProfile(
        candidate_id=candidate.id,
        selected_program=candidate.selected_program,
        model_input=layer3,
        metadata=profile_metadata,
        completeness=profile_metadata.data_completeness,
        data_flags=data_flags,
        created_at=candidate.created_at,
    )


def _extra_flags(model_input: ModelInput) -> list[str]:
    """Compute additional data-quality flags from Layer 3 content."""
    flags: list[str] = list(model_input.asr_flags)

    if model_input.asr_confidence is not None and model_input.asr_confidence < 0.6:
        flags.append("low_asr_confidence")

    if model_input.essay_text and len(model_input.essay_text.split()) < 30:
        flags.append("short_essay")

    return list(dict.fromkeys(flags))
