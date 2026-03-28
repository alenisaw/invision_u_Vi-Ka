from __future__ import annotations

import unittest

from backend.app.modules.m5_nlp.embeddings import cosine_similarity, split_sentences, strip_admissions_exam_content, token_overlap_ratio


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


if __name__ == "__main__":
    unittest.main()
