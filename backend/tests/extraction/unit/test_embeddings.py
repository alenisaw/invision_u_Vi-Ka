from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from backend.app.modules.extraction.embeddings import (
    LocalEmbeddingClient,
    cosine_similarity,
    semantic_similarity,
    split_sentences,
    strip_admissions_exam_content,
    token_overlap_ratio,
)


class EmbeddingsHelperTests(unittest.TestCase):
    def test_strip_admissions_exam_content_removes_exam_sentences(self) -> None:
        text = "My IELTS score is 7.0. I built a project for school students."
        cleaned = strip_admissions_exam_content(text)
        self.assertNotIn("IELTS", cleaned)
        self.assertIn("project", cleaned.lower())

    def test_similarity_helpers_return_normalized_values(self) -> None:
        a = "I built a product for students."
        b = "I built a digital product for students."
        self.assertGreater(cosine_similarity(a, b), 0.0)
        self.assertGreater(token_overlap_ratio(a, b), 0.0)

    def test_split_sentences_returns_compact_segments(self) -> None:
        parts = split_sentences("First sentence. Second sentence!\nThird sentence?")
        self.assertEqual(len(parts), 3)

    def test_semantic_similarity_uses_local_embedding_backend(self) -> None:
        client = LocalEmbeddingClient(model="jinaai/jina-embeddings-v5-text-nano")
        model = Mock()
        model.encode.return_value = [[1.0, 0.0], [1.0, 0.0]]

        with patch("backend.app.modules.extraction.embeddings._load_local_embedding_backend", return_value=(model, "cpu")):
            similarity = semantic_similarity("I built a product.", "I built a product.", client=client)

        self.assertEqual(similarity, 1.0)
        model.encode.assert_called_once()

    def test_semantic_similarity_falls_back_to_lexical_cosine_when_local_embeddings_fail(self) -> None:
        client = LocalEmbeddingClient(model="jinaai/jina-embeddings-v5-text-nano")

        with patch.object(client, "embed_texts", side_effect=RuntimeError("model unavailable")):
            similarity = semantic_similarity(
                "I built a digital product for students.",
                "I built a product for students.",
                client=client,
            )

        self.assertGreater(similarity, 0.0)


if __name__ == "__main__":
    unittest.main()
