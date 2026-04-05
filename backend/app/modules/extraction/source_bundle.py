"""
File: source_bundle.py
Purpose: Shared normalized source bundle and signal helper functions for the extraction stage.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.modules.scoring.schemas import SignalPayload

from .ai_detector import specificity_score
from .embeddings import clamp, normalize_text, split_sentences, strip_admissions_exam_content
from .schemas import ExtractionRequest


@dataclass(frozen=True)
class SourceBundle:
    """Normalized safe text sources used by both heuristic and LLM extraction."""

    video_transcript: str = ""
    essay: str = ""
    project_descriptions: str = ""
    experience_summary: str = ""
    internal_test_answers: str = ""
    selected_program: str = ""

    def get(self, source_name: str) -> str:
        return getattr(self, source_name, "")

    def available(self, field_names: tuple[str, ...] | list[str]) -> tuple[str, ...]:
        return tuple(field_name for field_name in field_names if self.get(field_name))

    def llm_payload(self, field_names: tuple[str, ...] | list[str]) -> dict[str, str]:
        return {field_name: self.get(field_name) for field_name in field_names if self.get(field_name)}


def build_source_bundle(request: ExtractionRequest, transcript_text: str | None = None) -> SourceBundle:
    """Normalize request texts into one reusable immutable bundle."""

    internal_test_text = " ".join(answer.answer_text for answer in request.internal_test_answers if answer.answer_text)
    projects_text = " ".join(project for project in request.project_descriptions if project)
    return SourceBundle(
        video_transcript=strip_admissions_exam_content(transcript_text or request.video_transcript),
        essay=strip_admissions_exam_content(request.essay_text),
        project_descriptions=strip_admissions_exam_content(projects_text),
        experience_summary=strip_admissions_exam_content(request.experience_summary),
        internal_test_answers=strip_admissions_exam_content(internal_test_text),
        selected_program=normalize_text(request.selected_program),
    )


def matching_snippets(text: str, keywords: list[str], limit: int = 2) -> list[str]:
    """Return up to `limit` sentence snippets that match any keyword."""

    matches: list[str] = []
    for sentence in split_sentences(text):
        lowered = sentence.lower()
        if any(keyword in lowered for keyword in keywords):
            matches.append(sentence[:220])
        if len(matches) >= limit:
            break
    return matches


def default_evidence(sources: SourceBundle, source_names: list[str] | tuple[str, ...], limit: int = 2) -> list[str]:
    """Select the first sentence from the first available sources."""

    evidence: list[str] = []
    for source_name in source_names:
        text = sources.get(source_name)
        if not text:
            continue
        sentences = split_sentences(text)
        if sentences:
            evidence.append(sentences[0][:220])
        if len(evidence) >= limit:
            break
    return evidence


def keyword_signal(
    *,
    sources: SourceBundle,
    source_names: list[str] | tuple[str, ...],
    keywords: list[str],
    reasoning: str,
    base_score: float = 0.30,
    hit_weight: float = 0.09,
    source_weight: float = 0.07,
    specificity_weight: float = 0.22,
) -> SignalPayload | None:
    """Build one deterministic signal from explicit keyword-backed evidence."""

    evidence: list[str] = []
    matched_sources: list[str] = []
    hit_count = 0
    snippet_specificity: list[float] = []

    for source_name in source_names:
        text = sources.get(source_name)
        if not text:
            continue
        matches = matching_snippets(text, keywords, limit=2)
        if not matches:
            continue
        matched_sources.append(source_name)
        evidence.extend(matches[:1])
        hit_count += len(matches)
        snippet_specificity.append(specificity_score(" ".join(matches[:1])))

    if not evidence:
        return None

    value = clamp(
        base_score
        + min(0.28, hit_count * hit_weight)
        + min(0.18, len(matched_sources) * source_weight)
        + min(0.18, (sum(snippet_specificity) / len(snippet_specificity) if snippet_specificity else 0.0) * specificity_weight)
    )
    confidence = clamp(
        0.45
        + min(0.22, hit_count * 0.06)
        + min(0.12, len(matched_sources) * 0.05)
        + min(0.08, len(evidence) * 0.04)
    )
    return SignalPayload(
        value=value,
        confidence=confidence,
        source=matched_sources,
        evidence=evidence[:2],
        reasoning=reasoning,
    )

