"""
File: test_client.py
Purpose: Safety tests for the extraction-stage media transcription client.
"""

from __future__ import annotations

import unittest

from app.modules.extraction.client import GroqTranscriptionClient


class GroqTranscriptionClientSafetyTests(unittest.TestCase):
    """Validate trusted-root path handling for media transcription."""

    def test_resolve_media_path_rejects_path_outside_trusted_roots(self) -> None:
        client = GroqTranscriptionClient()

        with self.assertRaises(RuntimeError):
            client._resolve_media_path("C:\\Windows\\System32\\drivers\\etc\\hosts")


if __name__ == "__main__":
    unittest.main()

