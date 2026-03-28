"""
File: test_client.py
Purpose: Safety tests for the M5 media transcription client.
"""

from __future__ import annotations

import unittest

from backend.app.modules.m5_nlp.client import GroqTranscriptionClient


class GroqTranscriptionClientSafetyTests(unittest.TestCase):
    """Validate trusted-root path handling for media transcription."""

    def test_resolve_media_path_rejects_path_outside_trusted_roots(self) -> None:
        client = GroqTranscriptionClient()

        with self.assertRaises(RuntimeError):
            client._resolve_media_path("C:\\Windows\\System32\\drivers\\etc\\hosts")


if __name__ == "__main__":
    unittest.main()


# File summary: test_client.py
# Covers trusted media path validation for the M5 transcription client.
