from __future__ import annotations

import unittest
from unittest.mock import patch

from app.modules.m5_nlp.gemini_client import (
    GeminiSignalClient,
    SignalGroupSpec,
    normalize_signal_container,
)
from app.modules.m5_nlp.source_bundle import SourceBundle


class _DummyResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload
        self.status_code = 200
        self.request = object()

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class _DummyClient:
    def __init__(self) -> None:
        self.last_kwargs: dict | None = None

    def __enter__(self) -> "_DummyClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def post(self, url: str, **kwargs):
        self.last_kwargs = {"url": url, **kwargs}
        return _DummyResponse(
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": (
                                        '{"signals":[{"signal_name":"motivation_clarity",'
                                        '"value":0.8,"confidence":0.7,"source":["essay"],'
                                        '"evidence":["clear goal"],"reasoning":"stated goal"}]}'
                                    )
                                }
                            ]
                        }
                    }
                ]
            }
        )


class LLMClientTests(unittest.TestCase):
    def test_normalize_signal_container_accepts_list_payload(self) -> None:
        normalized = normalize_signal_container(
            {
                "signals": [
                    {
                        "signal_name": "leadership_potential",
                        "value": 0.9,
                        "confidence": 0.8,
                    }
                ]
            },
            "leadership",
        )

        self.assertIn("leadership_potential", normalized)
        self.assertEqual(normalized["leadership_potential"]["value"], 0.9)

    def test_gemini_client_uses_header_auth_without_query_string(self) -> None:
        dummy_client = _DummyClient()
        client = GeminiSignalClient(api_key="gemini-secret-key")
        spec = SignalGroupSpec(
            name="motivation",
            signals=("motivation_clarity",),
            source_fields=("essay",),
            purpose="Extract motivation signals.",
        )
        sources = SourceBundle(essay="I want to build products.")

        with patch("app.modules.m5_nlp.gemini_client.httpx.Client", return_value=dummy_client):
            result = client.extract_group(spec, "candidate-1", sources)

        self.assertIn("motivation_clarity", result)
        assert dummy_client.last_kwargs is not None
        self.assertNotIn("params", dummy_client.last_kwargs)
        self.assertEqual(
            dummy_client.last_kwargs["headers"]["x-goog-api-key"],
            "gemini-secret-key",
        )


if __name__ == "__main__":
    unittest.main()
