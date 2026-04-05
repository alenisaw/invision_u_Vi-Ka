"""
File: groq_llm_client.py
Purpose: Groq-backed LLM client for extraction-stage signal generation (OpenAI-compatible API).
"""

from __future__ import annotations

import json
import logging
import os
import random
import time
from typing import Any

import httpx

from app.modules.scoring.schemas import SignalPayload

from .embeddings import clamp, normalize_text
from .llm_shared import (
    BACKOFF_BASE_SECONDS,
    MAX_LLM_ATTEMPTS,
    RETRYABLE_STATUS_CODES,
    SignalGroupSpec,
    normalize_signal_container,
)
from .prompts import M5_GROUP_PROMPT_HINTS, M5_SYSTEM_PROMPT
from .source_bundle import SourceBundle


logger = logging.getLogger(__name__)

DEFAULT_GROQ_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_GROQ_LLM_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


class GroqSignalClient:
    """OpenAI-compatible Groq client for per-group extraction."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout_s: float = 45.0,
    ) -> None:
        self.api_key = (api_key or os.getenv("GROQ_API_KEY") or "").strip()
        self.base_url = (base_url or os.getenv("GROQ_LLM_BASE_URL") or DEFAULT_GROQ_BASE_URL).rstrip("/")
        self.primary_model = model or os.getenv("M5_LLM_MODEL") or DEFAULT_GROQ_LLM_MODEL
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
            raise RuntimeError("GROQ_API_KEY is not set.")

        user_prompt = self._user_prompt(
            spec=spec,
            request_candidate_id=request_candidate_id,
            sources=sources,
        )
        payload = {
            "model": self.primary_model,
            "messages": [
                {"role": "system", "content": M5_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=self.timeout_s) as client:
            response = self._post_with_retry(
                client,
                url,
                headers=headers,
                json_payload=payload,
                provider_name="Groq",
            )

        parsed = self._parse_response(response.json())
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
                "response_format": {
                    "signals": {
                        "<signal_name>": {
                            "value": 0.0,
                            "confidence": 0.0,
                            "source": ["essay"],
                            "evidence": ["quote"],
                            "reasoning": "why",
                        }
                    }
                },
            },
            "source_texts": sources.llm_payload(spec.source_fields),
        }
        return json.dumps(safe_payload, ensure_ascii=False)

    @staticmethod
    def _parse_response(payload: dict[str, Any]) -> dict[str, Any]:
        choices = payload.get("choices")
        content = ""
        if isinstance(choices, list) and choices:
            message = choices[0].get("message", {})
            content = message.get("content", "")
        else:
            candidates = payload.get("candidates")
            if isinstance(candidates, list) and candidates:
                parts = (((candidates[0] or {}).get("content") or {}).get("parts") or [])
                if parts and isinstance(parts[0], dict):
                    content = str(parts[0].get("text", ""))
        if not content:
            logger.error("Groq response has no usable content. Payload: %s", json.dumps(payload, ensure_ascii=False)[:2000])
            raise ValueError("Groq response does not contain usable content.")
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            logger.error("Groq returned invalid JSON. Content: %s", content[:2000])
            raise ValueError(f"Groq response is not valid JSON: {exc}") from exc

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
