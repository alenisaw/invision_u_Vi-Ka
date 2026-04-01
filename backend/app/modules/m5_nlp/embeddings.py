# app/modules/m5_nlp/embeddings.py
"""
Text normalization and similarity helpers for M5.

Purpose:
- Provide lightweight lexical similarity when API embeddings are unavailable.
- Wrap the Jina embeddings API behind a small, testable client.
"""

from __future__ import annotations

import math
import os
import re
from collections import Counter
from typing import Any

import httpx


TOKEN_RE = re.compile(r"[A-Za-z\u0400-\u04FF0-9_]+")
SENTENCE_SPLIT_RE = re.compile(r"[.!?\n\r]+")
ADMISSIONS_EXAM_RE = re.compile(
    r"\b(?:ent|unt|\u0435\u043d\u0442|ielts|toefl|duolingo)\b",
    re.IGNORECASE,
)
DEFAULT_JINA_EMBEDDING_MODEL = "jina-embeddings-v5"
DEFAULT_JINA_BASE_URL = "https://api.jina.ai/v1/embeddings"


def clamp(value: float) -> float:
    return max(0.0, min(1.0, round(value, 4)))


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(normalize_text(text)) if len(token) >= 2]


def split_sentences(text: str) -> list[str]:
    sentences = [sentence.strip() for sentence in SENTENCE_SPLIT_RE.split(normalize_text(text))]
    return [sentence for sentence in sentences if sentence]


def strip_admissions_exam_content(text: str) -> str:
    sentences = split_sentences(text)
    if not sentences:
        return normalize_text(text)
    retained = [sentence for sentence in sentences if not ADMISSIONS_EXAM_RE.search(sentence)]
    return normalize_text(". ".join(retained)) if retained else ""


def token_overlap_ratio(text_a: str, text_b: str) -> float:
    tokens_a = set(tokenize(text_a))
    tokens_b = set(tokenize(text_b))
    if not tokens_a or not tokens_b:
        return 0.0
    return clamp(len(tokens_a & tokens_b) / len(tokens_a | tokens_b))


def cosine_similarity(text_a: str, text_b: str) -> float:
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


class JinaEmbeddingsClient:
    """Minimal Jina embeddings client with lexical fallback support."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout_s: float = 20.0,
    ) -> None:
        self.api_key = (api_key or os.getenv("JINA_API_KEY") or "").strip()
        self.model = model or os.getenv("EMBEDDING_MODEL") or DEFAULT_JINA_EMBEDDING_MODEL
        self.base_url = (base_url or os.getenv("JINA_EMBEDDING_BASE_URL") or DEFAULT_JINA_BASE_URL).rstrip("/")
        self.timeout_s = timeout_s

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not self.enabled:
            raise RuntimeError("JINA_API_KEY is not set.")
        payload: dict[str, Any] = {"model": self.model, "input": texts}
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        with httpx.Client(timeout=self.timeout_s) as client:
            response = client.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
        raw_items = response.json().get("data", [])
        return [list(item.get("embedding", [])) for item in raw_items if isinstance(item, dict)]


def _vector_cosine(vector_a: list[float], vector_b: list[float]) -> float:
    if not vector_a or not vector_b or len(vector_a) != len(vector_b):
        return 0.0
    numerator = sum(a * b for a, b in zip(vector_a, vector_b))
    norm_a = math.sqrt(sum(value * value for value in vector_a))
    norm_b = math.sqrt(sum(value * value for value in vector_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return clamp(numerator / (norm_a * norm_b))


def semantic_similarity(text_a: str, text_b: str, client: JinaEmbeddingsClient | None = None) -> float:
    """Prefer Jina embeddings when configured, otherwise fall back to lexical cosine."""

    if not text_a or not text_b:
        return 0.0
    embeddings_client = client or JinaEmbeddingsClient()
    if not embeddings_client.enabled:
        return cosine_similarity(text_a, text_b)
    try:
        vectors = embeddings_client.embed_texts([text_a, text_b])
        if len(vectors) != 2:
            return cosine_similarity(text_a, text_b)
        return _vector_cosine(vectors[0], vectors[1])
    except Exception:
        return cosine_similarity(text_a, text_b)
