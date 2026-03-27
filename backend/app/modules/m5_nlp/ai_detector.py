"""
File: ai_detector.py
Purpose: Heuristic authenticity and specificity helpers for M5.
"""

from __future__ import annotations

import re

from .embeddings import clamp, cosine_similarity, normalize_text, tokenize

GENERIC_PHRASES = [
    "i am passionate",
    "i have always dreamed",
    "highly motivated",
    "driven individual",
    "make a positive impact",
    "my unique journey",
    "я очень мотивирован",
    "я всегда мечтал",
    "хочу внести вклад",
    "стремлюсь развиваться",
    "с раннего возраста",
]

DETAIL_RE = re.compile(r"\b\d+\b|%|team of|команд[аы]\s+\d+|project|проект|volunteer|волонтер")


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

    value = 0.30 + min(0.40, 0.08 * detail_hits) + min(0.30, lexical_diversity * 0.35) - generic_penalty
    return clamp(value)


def voice_consistency_score(essay_text: str, transcript_text: str) -> float:
    """Estimate whether the written and spoken narrative feel aligned."""

    if not essay_text or not transcript_text:
        return 0.50

    similarity = cosine_similarity(essay_text, transcript_text)
    return clamp(0.35 + similarity * 0.65)


def ai_writing_risk_score(essay_text: str, transcript_text: str, project_text: str = "") -> float:
    """Estimate advisory AI-writing risk from genericity and low specificity."""

    essay_specificity = specificity_score(essay_text)
    transcript_specificity = specificity_score(transcript_text) if transcript_text else essay_specificity
    project_specificity = specificity_score(project_text) if project_text else 0.50
    genericity = min(1.0, _generic_phrase_hits(essay_text) / 4) if essay_text else 0.0
    consistency = voice_consistency_score(essay_text, transcript_text)

    risk = (
        0.40 * (1.0 - essay_specificity)
        + 0.25 * genericity
        + 0.20 * max(0.0, 0.60 - consistency)
        + 0.15 * max(0.0, 0.55 - ((transcript_specificity + project_specificity) / 2))
    )
    return clamp(risk)


def authenticity_confidence(essay_text: str, transcript_text: str) -> float:
    """Estimate confidence of the authenticity heuristics."""

    total_length = len(normalize_text(essay_text)) + len(normalize_text(transcript_text))
    evidence_strength = min(1.0, total_length / 900)
    return clamp(0.45 + evidence_strength * 0.40)


# File summary: ai_detector.py
# Provides deterministic advisory heuristics for AI-writing risk and specificity.
