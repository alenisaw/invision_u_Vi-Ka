# app/modules/extraction/embeddings.py
"""
Text normalization and similarity helpers for the extraction stage.

Purpose:
- Provide lightweight lexical similarity when local embeddings are unavailable.
- Wrap a local Hugging Face embedding model behind a small, testable client.
"""

from __future__ import annotations

import math
import os
import re
from collections import Counter
from functools import lru_cache
from typing import Any


TOKEN_RE = re.compile(r"[A-Za-z\u0400-\u04FF0-9_]+")
SENTENCE_SPLIT_RE = re.compile(r"[.!?\n\r]+")
ADMISSIONS_EXAM_RE = re.compile(
    r"\b(?:ent|unt|\u0435\u043d\u0442|ielts|toefl|duolingo)\b",
    re.IGNORECASE,
)
DEFAULT_EMBEDDING_MODEL = "jinaai/jina-embeddings-v5-text-nano"
DEFAULT_EMBEDDING_TASK = "text-matching"
DEFAULT_EMBEDDING_DEVICE = "auto"


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


def _env_flag(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache(maxsize=4)
def _load_local_embedding_backend(
    model_name: str,
    device_name: str,
    trust_remote_code: bool,
) -> tuple[Any, str]:
    try:
        import torch
        from transformers import AutoModel
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "Local embeddings require `transformers`, `torch`, and `peft` from backend/requirements.txt."
        ) from exc

    resolved_device = device_name or DEFAULT_EMBEDDING_DEVICE
    if resolved_device == "auto":
        resolved_device = "cuda" if torch.cuda.is_available() else "cpu"

    dtype = torch.bfloat16 if resolved_device.startswith("cuda") else torch.float32
    try:
        model = AutoModel.from_pretrained(
            model_name,
            trust_remote_code=trust_remote_code,
            dtype=dtype,
        )
    except TypeError:
        model = AutoModel.from_pretrained(
            model_name,
            trust_remote_code=trust_remote_code,
            torch_dtype=dtype,
        )
    if hasattr(model, "to"):
        model = model.to(device=resolved_device)
    if hasattr(model, "eval"):
        model = model.eval()
    return model, resolved_device


def _coerce_embedding_vectors(raw_vectors: Any) -> list[list[float]]:
    if hasattr(raw_vectors, "tolist"):
        raw_vectors = raw_vectors.tolist()
    if isinstance(raw_vectors, tuple):
        raw_vectors = list(raw_vectors)
    if not isinstance(raw_vectors, list):
        return []
    if raw_vectors and isinstance(raw_vectors[0], (int, float)):
        return [[float(value) for value in raw_vectors]]
    vectors: list[list[float]] = []
    for row in raw_vectors:
        if isinstance(row, tuple):
            row = list(row)
        if isinstance(row, list):
            vectors.append([float(value) for value in row])
    return vectors


class LocalEmbeddingClient:
    """Minimal local embedding client with lexical fallback support."""

    def __init__(
        self,
        model: str | None = None,
        task: str | None = None,
        device: str | None = None,
        trust_remote_code: bool | None = None,
    ) -> None:
        env_model = (os.getenv("EMBEDDING_MODEL") or "").strip()
        self.model = (model if model is not None else env_model).strip()
        self.task = task or os.getenv("EMBEDDING_TASK") or DEFAULT_EMBEDDING_TASK
        self.device = (device or os.getenv("EMBEDDING_DEVICE") or DEFAULT_EMBEDDING_DEVICE).strip()
        self.trust_remote_code = (
            _env_flag("EMBEDDING_TRUST_REMOTE_CODE", True)
            if trust_remote_code is None
            else bool(trust_remote_code)
        )

    @property
    def enabled(self) -> bool:
        return bool(self.model)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if not self.enabled:
            raise RuntimeError("EMBEDDING_MODEL is not set.")

        model, _ = _load_local_embedding_backend(
            self.model,
            self.device,
            self.trust_remote_code,
        )
        normalized_texts = [normalize_text(text) for text in texts]
        raw_vectors = model.encode(texts=normalized_texts, task=self.task)
        return _coerce_embedding_vectors(raw_vectors)


JinaEmbeddingsClient = LocalEmbeddingClient


def _vector_cosine(vector_a: list[float], vector_b: list[float]) -> float:
    if not vector_a or not vector_b or len(vector_a) != len(vector_b):
        return 0.0
    numerator = sum(a * b for a, b in zip(vector_a, vector_b))
    norm_a = math.sqrt(sum(value * value for value in vector_a))
    norm_b = math.sqrt(sum(value * value for value in vector_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return clamp(numerator / (norm_a * norm_b))


def semantic_similarity(text_a: str, text_b: str, client: LocalEmbeddingClient | None = None) -> float:
    """Prefer local embeddings when configured, otherwise fall back to lexical cosine."""

    if not text_a or not text_b:
        return 0.0
    embeddings_client = client or LocalEmbeddingClient()
    if not embeddings_client.enabled:
        return cosine_similarity(text_a, text_b)
    try:
        vectors = embeddings_client.embed_texts([text_a, text_b])
        if len(vectors) != 2:
            return cosine_similarity(text_a, text_b)
        return _vector_cosine(vectors[0], vectors[1])
    except Exception:
        return cosine_similarity(text_a, text_b)
