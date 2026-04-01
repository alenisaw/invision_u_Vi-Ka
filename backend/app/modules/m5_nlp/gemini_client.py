"""
File: gemini_client.py
Purpose: Gemini API client for structured M5 signal extraction.
"""

from __future__ import annotations

import json
import logging
import os
import random
import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.modules.m6_scoring.schemas import SignalPayload

from .embeddings import clamp, normalize_text
from .prompts import M5_GROUP_PROMPT_HINTS, M5_SYSTEM_PROMPT
from .source_bundle import SourceBundle


logger = logging.getLogger(__name__)

DEFAULT_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_M5_LLM_MODEL = "gemini-2.5-flash"
DEFAULT_M5_FAST_MODEL = "gemini-2.5-flash"
MAX_LLM_ATTEMPTS = 3
BACKOFF_BASE_SECONDS = 0.75
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


@dataclass(frozen=True)
class SignalGroupSpec:
    name: str
    signals: tuple[str, ...]
    source_fields: tuple[str, ...]
    purpose: str
    model_tier: str = "primary"


def normalize_signal_container(parsed: dict[str, Any], group_name: str) -> dict[str, Any]:
    raw_signals = parsed.get("signals", {})
    if isinstance(raw_signals, dict):
        return raw_signals
    if isinstance(raw_signals, list):
        normalized: dict[str, Any] = {}
        for item in raw_signals:
            if not isinstance(item, dict):
                continue
            signal_name = item.get("signal_name")
            if not isinstance(signal_name, str) or not signal_name.strip():
                continue
            normalized[signal_name.strip()] = {
                key: value
                for key, value in item.items()
                if key != "signal_name"
            }
        if normalized:
            logger.info(
                "Normalized list-based Gemini signals for group %s (%d items)",
                group_name,
                len(normalized),
            )
            return normalized
    logger.error(
        "Structured response for group %s has unexpected signals payload type: %s",
        group_name,
        type(raw_signals).__name__,
    )
    raise ValueError("LLM response does not contain a valid `signals` payload.")


class GeminiSignalClient:
    """Structured-output Gemini client for per-group M5 extraction."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        primary_model: str | None = None,
        fast_model: str | None = None,
        timeout_s: float = 45.0,
    ) -> None:
        self.api_key = (api_key or os.getenv("GEMINI_API_KEY") or "").strip()
        self.base_url = (base_url or os.getenv("GEMINI_BASE_URL") or DEFAULT_GEMINI_BASE_URL).rstrip("/")
        self.primary_model = primary_model or os.getenv("M5_LLM_MODEL") or DEFAULT_M5_LLM_MODEL
        self.fast_model = fast_model or os.getenv("M5_LLM_FAST_MODEL") or DEFAULT_M5_FAST_MODEL
        self.timeout_s = timeout_s

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def extract_group(
        self,
        spec: SignalGroupSpec,
        request_candidate_id: str,
        sources: SourceBundle,
    ) -> dict[str, SignalPayload]:
        if not self.enabled:
            raise RuntimeError("GEMINI_API_KEY is not set.")

        payload = {
            "systemInstruction": {"parts": [{"text": M5_SYSTEM_PROMPT}]},
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": self._user_prompt(
                                spec=spec,
                                request_candidate_id=request_candidate_id,
                                sources=sources,
                            )
                        }
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json",
            },
        }
        model_name = self.primary_model if spec.model_tier == "primary" else self.fast_model
        url = f"{self.base_url}/models/{model_name}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }
        with httpx.Client(timeout=self.timeout_s) as client:
            response = self._post_with_retry(
                client,
                url,
                headers=headers,
                json_payload=payload,
                provider_name="Gemini",
            )

        parsed = self._parse_response_content(response.json())
        raw_signals = normalize_signal_container(parsed, spec.name)

        source_fallback = list(sources.available(spec.source_fields))
        signals: dict[str, SignalPayload] = {}
        for signal_name in spec.signals:
            if raw_signals.get(signal_name) is None:
                continue
            signals[signal_name] = self._coerce_signal_payload(
                raw_payload=raw_signals[signal_name],
                source_fallback=source_fallback,
            )
        return signals

    def _user_prompt(self, *, spec: SignalGroupSpec, request_candidate_id: str, sources: SourceBundle) -> str:
        safe_payload = {
            "candidate_id": request_candidate_id,
            "group": spec.name,
            "purpose": spec.purpose,
            "prompt_hint": M5_GROUP_PROMPT_HINTS.get(spec.name, ""),
            "signals_to_extract": list(spec.signals),
            "instructions": {
                "omit_signals_without_evidence": True,
                "value_range": "0.0..1.0",
                "confidence_range": "0.0..1.0",
                "max_evidence_items": 2,
            },
            "source_texts": sources.llm_payload(spec.source_fields),
        }
        return json.dumps(safe_payload, ensure_ascii=False)

    def _parse_response_content(self, payload: dict[str, Any]) -> dict[str, Any]:
        candidates = payload.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise ValueError("Gemini response does not contain candidates.")
        parts = candidates[0].get("content", {}).get("parts", [])
        if not isinstance(parts, list) or not parts:
            raise ValueError("Gemini response does not contain content parts.")
        text_parts = [part.get("text", "") for part in parts if isinstance(part, dict) and part.get("text")]
        if not text_parts:
            raise ValueError("Gemini response does not contain JSON text.")
        content = "\n".join(text_parts).strip()
        if content.startswith("```") and content.endswith("```"):
            lines = content.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        return json.loads(content)

    def _post_with_retry(
        self,
        client: httpx.Client,
        url: str,
        *,
        headers: dict[str, str],
        json_payload: dict[str, Any],
        provider_name: str,
    ) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(1, MAX_LLM_ATTEMPTS + 1):
            try:
                response = client.post(url, headers=headers, json=json_payload)
                if response.status_code in RETRYABLE_STATUS_CODES:
                    raise httpx.HTTPStatusError(
                        f"{provider_name} temporary failure",
                        request=response.request,
                        response=response,
                    )
                response.raise_for_status()
                return response
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_error = exc
                response = getattr(exc, "response", None)
                status_code = response.status_code if response is not None else None
                retryable = status_code in RETRYABLE_STATUS_CODES or isinstance(
                    exc,
                    httpx.RequestError,
                )
                if not retryable or attempt == MAX_LLM_ATTEMPTS:
                    raise
                delay_seconds = (BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))) + random.uniform(
                    0.0,
                    0.25,
                )
                logger.warning(
                    "%s request failed on attempt %d/%d with status=%s. Retrying in %.2fs",
                    provider_name,
                    attempt,
                    MAX_LLM_ATTEMPTS,
                    status_code,
                    delay_seconds,
                )
                time.sleep(delay_seconds)
        if last_error is not None:  # pragma: no cover - defensive guard
            raise last_error
        raise RuntimeError(f"{provider_name} request failed without an explicit exception")

    def _coerce_signal_payload(self, *, raw_payload: Any, source_fallback: list[str]) -> SignalPayload:
        if not isinstance(raw_payload, dict):
            raise ValueError("Signal payload must be an object.")
        evidence = [
            normalize_text(str(item))[:220]
            for item in raw_payload.get("evidence", [])
            if normalize_text(str(item))
        ][:2]
        source = [str(item) for item in raw_payload.get("source", []) if str(item)] or source_fallback
        return SignalPayload(
            value=clamp(self._safe_float(raw_payload.get("value", 0.0))),
            confidence=clamp(self._safe_float(raw_payload.get("confidence", 0.0))),
            source=source,
            evidence=evidence,
            reasoning=normalize_text(str(raw_payload.get("reasoning", "")))[:280],
        )

    @staticmethod
    def _safe_float(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0


