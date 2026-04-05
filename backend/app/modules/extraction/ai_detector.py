# app/modules/extraction/ai_detector.py
"""
Heuristic authenticity and specificity helpers for the extraction stage.

Purpose:
- Estimate whether a text is concrete or overly generic.
- Provide advisory consistency signals across essay, transcript, and projects.
"""

from __future__ import annotations

import re

from .embeddings import clamp, normalize_text, semantic_similarity, tokenize

GENERIC_PHRASES = [
    "i am passionate",
    "i have always dreamed",
    "highly motivated",
    "driven individual",
    "make a positive impact",
    "my unique journey",
    "\u044f \u043e\u0447\u0435\u043d\u044c \u043c\u043e\u0442\u0438\u0432\u0438\u0440\u043e\u0432\u0430\u043d",
    "\u044f \u0432\u0441\u0435\u0433\u0434\u0430 \u043c\u0435\u0447\u0442\u0430\u043b",
    "\u0445\u043e\u0447\u0443 \u0432\u043d\u0435\u0441\u0442\u0438 \u0432\u043a\u043b\u0430\u0434",
    "\u0441\u0442\u0440\u0435\u043c\u043b\u044e\u0441\u044c \u0440\u0430\u0437\u0432\u0438\u0432\u0430\u0442\u044c\u0441\u044f",
    "\u0441 \u0440\u0430\u043d\u043d\u0435\u0433\u043e \u0432\u043e\u0437\u0440\u0430\u0441\u0442\u0430",
]

DETAIL_RE = re.compile(
    r"\b\d+\b|%|team of|"
    r"\u043a\u043e\u043c\u0430\u043d\u0434[\u0430\u044b]\s+\d+|"
    r"project|\u043f\u0440\u043e\u0435\u043a\u0442|"
    r"volunteer|\u0432\u043e\u043b\u043e\u043d\u0442\u0435\u0440",
    re.IGNORECASE,
)


def _generic_phrase_hits(text: str) -> int:
    lowered = normalize_text(text).lower()
    return sum(1 for phrase in GENERIC_PHRASES if phrase in lowered)


def specificity_score(text: str) -> float:
    """Estimate how concrete and example-rich a text is."""

    normalized = normalize_text(text)
    if not normalized:
        return 0.0

    tokens = tokenize(normalized)
    detail_hits = len(DETAIL_RE.findall(normalized.lower()))
    lexical_diversity = len(set(tokens)) / max(len(tokens), 1)
    generic_penalty = 0.08 * _generic_phrase_hits(normalized)

    value = (
        0.30
        + min(0.40, 0.08 * detail_hits)
        + min(0.30, lexical_diversity * 0.35)
        - generic_penalty
    )
    return clamp(value)


def voice_consistency_score(essay_text: str, transcript_text: str) -> float:
    """Estimate whether the written and spoken narrative feel aligned."""

    if not essay_text or not transcript_text:
        return 0.50

    similarity = semantic_similarity(essay_text, transcript_text)
    return clamp(0.35 + similarity * 0.65)


def authenticity_risk_score(primary_text: str, supporting_text: str = "", project_text: str = "") -> float:
    """Estimate advisory authenticity risk from genericity, specificity, and cross-source support."""

    primary_specificity = specificity_score(primary_text)
    supporting_specificity = specificity_score(supporting_text) if supporting_text else primary_specificity
    project_specificity = specificity_score(project_text) if project_text else 0.50
    genericity = min(1.0, _generic_phrase_hits(primary_text) / 4) if primary_text else 0.0
    cross_source_consistency = (
        semantic_similarity(primary_text, supporting_text)
        if primary_text and supporting_text
        else 0.55
    )
    support_specificity = (
        (supporting_specificity + project_specificity) / 2
        if supporting_text or project_text
        else max(primary_specificity, 0.50)
    )

    risk = (
        0.45 * (1.0 - primary_specificity)
        + 0.25 * genericity
        + 0.15 * max(0.0, 0.58 - cross_source_consistency)
        + 0.15 * max(0.0, 0.55 - support_specificity)
    )
    return clamp(risk)


def ai_writing_risk_score(essay_text: str, transcript_text: str, project_text: str = "") -> float:
    """Backward-compatible wrapper for essay-centric authenticity checks."""

    return authenticity_risk_score(
        primary_text=essay_text,
        supporting_text=transcript_text,
        project_text=project_text,
    )


def transcript_authenticity_risk_score(transcript_text: str, essay_text: str = "", project_text: str = "") -> float:
    """Estimate advisory authenticity risk for transcript-first candidates."""

    return authenticity_risk_score(
        primary_text=transcript_text,
        supporting_text=essay_text,
        project_text=project_text,
    )


def authenticity_confidence(essay_text: str, transcript_text: str) -> float:
    """Estimate confidence of the authenticity heuristics."""

    total_length = len(normalize_text(essay_text)) + len(normalize_text(transcript_text))
    evidence_strength = min(1.0, total_length / 900)
    return clamp(0.45 + evidence_strength * 0.40)
