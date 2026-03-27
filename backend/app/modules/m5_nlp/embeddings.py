"""
File: embeddings.py
Purpose: Lightweight text similarity helpers for the M5 heuristics.

Notes:
- These are deterministic lexical approximations for the MVP.
- They keep the module dependency-light while preserving M5 -> M6 compatibility.
"""

from __future__ import annotations

import math
import re
from collections import Counter

TOKEN_RE = re.compile(r"[A-Za-zА-Яа-яЁё0-9_]+")
SENTENCE_SPLIT_RE = re.compile(r"[.!?\n\r]+")
ADMISSIONS_EXAM_RE = re.compile(r"\b(?:ent|unt|ен[тt]|ielts|toefl|duolingo)\b", re.IGNORECASE)


def clamp(value: float) -> float:
    """Clamp values into the normalized score range."""

    return max(0.0, min(1.0, round(value, 4)))


def normalize_text(text: str) -> str:
    """Normalize whitespace without destroying punctuation."""

    return re.sub(r"\s+", " ", (text or "").strip())


def tokenize(text: str) -> list[str]:
    """Tokenize multilingual text into lowercase lexical tokens."""

    return [token.lower() for token in TOKEN_RE.findall(normalize_text(text)) if len(token) >= 2]


def split_sentences(text: str) -> list[str]:
    """Split text into compact sentence-like snippets."""

    sentences = [sentence.strip() for sentence in SENTENCE_SPLIT_RE.split(normalize_text(text))]
    return [sentence for sentence in sentences if sentence]


def strip_admissions_exam_content(text: str) -> str:
    """Remove admissions exam score sentences so interview scoring stays content-based."""

    sentences = split_sentences(text)
    if not sentences:
        return normalize_text(text)

    retained = [
        sentence
        for sentence in sentences
        if not ADMISSIONS_EXAM_RE.search(sentence)
    ]
    return normalize_text(". ".join(retained)) if retained else ""


def token_overlap_ratio(text_a: str, text_b: str) -> float:
    """Approximate lexical overlap between two texts."""

    tokens_a = set(tokenize(text_a))
    tokens_b = set(tokenize(text_b))
    if not tokens_a or not tokens_b:
        return 0.0
    return clamp(len(tokens_a & tokens_b) / len(tokens_a | tokens_b))


def cosine_similarity(text_a: str, text_b: str) -> float:
    """Approximate cosine similarity from bag-of-words counts."""

    counts_a = Counter(tokenize(text_a))
    counts_b = Counter(tokenize(text_b))
    if not counts_a or not counts_b:
        return 0.0

    shared = set(counts_a) & set(counts_b)
    numerator = sum(counts_a[token] * counts_b[token] for token in shared)
    norm_a = math.sqrt(sum(value * value for value in counts_a.values()))
    norm_b = math.sqrt(sum(value * value for value in counts_b.values()))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return clamp(numerator / (norm_a * norm_b))


# File summary: embeddings.py
# Provides normalized tokenization, sentence splitting, and similarity helpers for M5.
