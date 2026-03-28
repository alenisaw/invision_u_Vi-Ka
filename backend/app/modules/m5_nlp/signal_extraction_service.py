"""
File: signal_extraction_service.py
Purpose: Grouped M5 NLP extraction with OpenRouter-ready prompts and heuristic fallback.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from statistics import mean
from typing import Any

import httpx

from backend.app.modules.m6_scoring.schemas import SignalEnvelope, SignalPayload
from backend.app.modules.m6_scoring.program_policy import normalize_program_id

from .ai_detector import (
    ai_writing_risk_score,
    authenticity_confidence,
    specificity_score,
    voice_consistency_score,
)
from .client import GroqTranscriptionClient
from .embeddings import clamp, normalize_text, split_sentences, strip_admissions_exam_content, tokenize
from .extractor import HeuristicSignalExtractor
from .schemas import M5ExtractionRequest

DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_PRIMARY_MODEL = "qwen/qwen-3.5-72b-instruct"
OPENROUTER_FAST_MODEL = "qwen/qwen-3.5-7b-instruct"

CORE_SIGNAL_NAMES = {
    "leadership_indicators",
    "growth_trajectory",
    "motivation_clarity",
    "agency_signals",
    "learning_agility",
    "clarity_score",
    "ethical_reasoning",
    "program_alignment",
}

FOUNDATION_INTERVIEW_CRITERIA = {
    "motivation": ("motivation_clarity", "program_alignment"),
    "goals": ("goal_specificity", "future_goals_alignment"),
    "resilience": ("challenges_overcome", "resilience_evidence"),
    "leadership": ("leadership_indicators", "leadership_reflection"),
    "teamwork": ("team_leadership", "teamwork_problem_solving"),
    "support_context": ("support_network",),
    "english_growth": ("english_growth",),
}

FOUNDATION_YEAR_MARKERS = (
    "foundation year",
    "foundation",
    "подготовитель",
)

RESPONSIBILITY_KEYWORDS = [
    "responsible", "responsibility", "accountable", "ownership", "owned", "deliverable",
    "deadline", "budget", "mentored", "answerable", "ответствен", "отвечал", "обязан",
    "обязательств", "срок", "курировал", "наставлял",
]

DECISION_KEYWORDS = [
    "decide", "decision", "tradeoff", "consider", "because", "choose", "alternative",
    "risk", "balance", "criteria", "решил", "решение", "выбрал", "потому",
    "компромисс", "риск", "критер",
]


@dataclass(frozen=True)
class SignalGroupSpec:
    name: str
    signals: tuple[str, ...]
    source_fields: tuple[str, ...]
    purpose: str
    model_tier: str = "primary"


@dataclass
class SignalGroupResult:
    group_name: str
    backend: str
    signals: dict[str, SignalPayload]
    source_fields: list[str]
    notes: list[str] = field(default_factory=list)


@dataclass
class GroupedExtractionResult:
    envelope: SignalEnvelope
    groups: list[SignalGroupResult]
    used_transcription_fallback: bool = False


@dataclass
class NormalizedSources:
    video_transcript: str = ""
    essay: str = ""
    project_descriptions: str = ""
    experience_summary: str = ""
    internal_test_answers: str = ""
    selected_program: str = ""

    def get(self, field_name: str) -> str:
        return getattr(self, field_name, "")

    def available(self, field_names: tuple[str, ...] | list[str]) -> list[str]:
        return [field_name for field_name in field_names if self.get(field_name)]

    def llm_payload(self, field_names: tuple[str, ...] | list[str]) -> dict[str, str]:
        return {field_name: self.get(field_name) for field_name in field_names if self.get(field_name)}


SIGNAL_GROUP_SPECS = (
    SignalGroupSpec(
        name="leadership",
        signals=("leadership_indicators", "responsibility_examples", "team_leadership", "leadership_reflection"),
        source_fields=("video_transcript", "essay", "project_descriptions", "experience_summary"),
        purpose="Extract leadership behavior, ownership, team guidance, and leadership self-reflection.",
    ),
    SignalGroupSpec(
        name="growth",
        signals=("growth_trajectory", "challenges_overcome", "learning_agility", "resilience_evidence"),
        source_fields=("essay", "experience_summary", "video_transcript", "internal_test_answers"),
        purpose="Assess growth trajectory, challenges overcome, resilience, and learning agility.",
    ),
    SignalGroupSpec(
        name="motivation",
        signals=("motivation_clarity", "goal_specificity", "program_alignment", "future_goals_alignment"),
        source_fields=("essay", "video_transcript", "selected_program", "project_descriptions"),
        purpose="Assess motivation clarity, long-term goals, and program fit.",
    ),
    SignalGroupSpec(
        name="initiative",
        signals=("agency_signals", "self_started_projects", "proactivity_examples", "teamwork_problem_solving"),
        source_fields=("project_descriptions", "essay", "experience_summary", "video_transcript"),
        purpose="Assess initiative, self-started projects, proactivity, and teamwork problem solving.",
    ),
    SignalGroupSpec(
        name="consistency",
        signals=("essay_transcript_consistency", "claims_evidence_match"),
        source_fields=("essay", "video_transcript", "project_descriptions", "experience_summary"),
        purpose="Check cross-source consistency and evidence support for claims.",
        model_tier="fast",
    ),
    SignalGroupSpec(
        name="authenticity",
        signals=("ai_writing_risk", "voice_consistency", "specificity_score"),
        source_fields=("essay", "video_transcript", "project_descriptions"),
        purpose="Assess advisory AI-writing risk, voice consistency, and narrative specificity.",
        model_tier="fast",
    ),
    SignalGroupSpec(
        name="thinking",
        signals=("decision_making_style", "ethical_reasoning", "civic_orientation"),
        source_fields=("internal_test_answers", "essay", "video_transcript", "experience_summary"),
        purpose="Assess decision making, ethical reasoning, and civic orientation.",
    ),
    SignalGroupSpec(
        name="communication",
        signals=("clarity_score", "structure_score", "idea_articulation", "english_growth"),
        source_fields=("video_transcript", "essay", "internal_test_answers"),
        purpose="Assess clarity, structure, idea articulation, and English-learning progress.",
        model_tier="fast",
    ),
    SignalGroupSpec(
        name="support",
        signals=("support_network",),
        source_fields=("video_transcript", "essay", "experience_summary"),
        purpose="Capture whether the candidate addresses family support or inspiration context without treating it as a score on its own.",
        model_tier="fast",
    ),
)


class OpenRouterSignalClient:
    """Structured-output client for per-group M5 extraction."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        primary_model: str | None = None,
        fast_model: str | None = None,
        timeout_s: float = 45.0,
    ) -> None:
        self.api_key = (api_key or os.getenv("OPENROUTER_API_KEY") or "").strip()
        self.base_url = (base_url or os.getenv("OPENROUTER_BASE_URL") or DEFAULT_OPENROUTER_BASE_URL).rstrip("/")
        self.primary_model = primary_model or os.getenv("LLM_PRIMARY_MODEL") or OPENROUTER_PRIMARY_MODEL
        self.fast_model = fast_model or os.getenv("LLM_FAST_MODEL") or OPENROUTER_FAST_MODEL
        self.timeout_s = timeout_s

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def extract_group(
        self,
        spec: SignalGroupSpec,
        request: M5ExtractionRequest,
        sources: NormalizedSources,
    ) -> dict[str, SignalPayload]:
        if not self.enabled:
            raise RuntimeError("OPENROUTER_API_KEY is not set.")

        payload = {
            "model": self.primary_model if spec.model_tier == "primary" else self.fast_model,
            "temperature": 0.1,
            "messages": [
                {"role": "system", "content": self._system_prompt()},
                {"role": "user", "content": self._user_prompt(spec, request, sources)},
            ],
            "response_format": {"type": "json_schema", "json_schema": self._json_schema(spec)},
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=self.timeout_s) as client:
            response = client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            response.raise_for_status()

        parsed = self._parse_response_content(response.json())
        raw_signals = parsed.get("signals", {})
        if not isinstance(raw_signals, dict):
            raise ValueError("OpenRouter response does not contain `signals`.")

        source_fallback = sources.available(spec.source_fields)
        signals: dict[str, SignalPayload] = {}
        for signal_name in spec.signals:
            if raw_signals.get(signal_name) is None:
                continue
            signals[signal_name] = self._coerce_signal_payload(
                raw_payload=raw_signals[signal_name],
                source_fallback=source_fallback,
            )
        return signals

    def _system_prompt(self) -> str:
        return (
            "You are the M5 NLP Signal Extraction Service for inVision U. "
            "Use only the provided safe Layer 3 text. "
            "Never infer demographic or protected attributes. "
            "If there is not enough evidence for a signal, omit it. "
            "Return JSON only."
        )

    def _user_prompt(self, spec: SignalGroupSpec, request: M5ExtractionRequest, sources: NormalizedSources) -> str:
        safe_payload = {
            "candidate_id": str(request.candidate_id),
            "group": spec.name,
            "purpose": spec.purpose,
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

    def _json_schema(self, spec: SignalGroupSpec) -> dict[str, Any]:
        signal_payload_schema = {
            "type": "object",
            "properties": {
                "value": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "source": {"type": "array", "items": {"type": "string"}},
                "evidence": {"type": "array", "items": {"type": "string"}},
                "reasoning": {"type": "string"},
            },
            "required": ["value", "confidence", "source", "evidence", "reasoning"],
            "additionalProperties": False,
        }
        return {
            "name": f"m5_{spec.name}_signals",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "signals": {
                        "type": "object",
                        "properties": {signal_name: signal_payload_schema for signal_name in spec.signals},
                        "additionalProperties": False,
                    }
                },
                "required": ["signals"],
                "additionalProperties": False,
            },
        }

    def _parse_response_content(self, payload: dict[str, Any]) -> dict[str, Any]:
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("OpenRouter response does not contain completion choices.")
        content = choices[0].get("message", {}).get("content")
        if isinstance(content, dict):
            return content
        if isinstance(content, list):
            content = "".join(item.get("text", "") if isinstance(item, dict) else str(item) for item in content)
        if not isinstance(content, str):
            raise ValueError("OpenRouter response content is not JSON.")
        normalized = content.strip()
        if normalized.startswith("```") and normalized.endswith("```"):
            lines = normalized.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            normalized = "\n".join(lines).strip()
        return json.loads(normalized)

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

    def _safe_float(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0


class GroupedNLPSignalExtractionService:
    """Architecture-aligned M5 service with grouped extraction and offline fallback."""

    def __init__(
        self,
        extractor: HeuristicSignalExtractor | None = None,
        transcription_client: GroqTranscriptionClient | None = None,
        llm_client: OpenRouterSignalClient | None = None,
        enable_llm: bool | None = None,
    ) -> None:
        self.extractor = extractor or HeuristicSignalExtractor()
        self.transcription_client = transcription_client or GroqTranscriptionClient()
        self.llm_client = llm_client or OpenRouterSignalClient()
        self.enable_llm = self.llm_client.enabled if enable_llm is None else bool(enable_llm and self.llm_client.enabled)

    def extract_signals(self, request: M5ExtractionRequest) -> SignalEnvelope:
        return self.extract_signal_groups(request).envelope

    def extract_from_payload(self, payload: dict[str, Any]) -> SignalEnvelope:
        return self.extract_signals(M5ExtractionRequest.model_validate(payload))

    def extract_signal_groups(self, request: M5ExtractionRequest) -> GroupedExtractionResult:
        transcript_text = strip_admissions_exam_content(request.video_transcript)
        data_flags = list(dict.fromkeys(request.data_flags))
        used_transcription_fallback = False

        if not transcript_text and request.interview_media_path:
            used_transcription_fallback = True
            transcription_payload = self.transcription_client.transcribe_media(
                request.interview_media_path,
                language=request.language,
            )
            transcript_text = strip_admissions_exam_content(str(transcription_payload.get("text", "")))
            if not transcript_text:
                data_flags.append("no_speech_detected")

        sources = self._build_sources(request, transcript_text=transcript_text)
        heuristic_signals = self._build_heuristic_signal_map(
            request=request,
            transcript_text=transcript_text,
            sources=sources,
        )

        grouped_results: list[SignalGroupResult] = []
        merged_signals: dict[str, SignalPayload] = {}
        llm_used = False

        for spec in SIGNAL_GROUP_SPECS:
            group_result = self._extract_one_group(
                spec=spec,
                request=request,
                sources=sources,
                heuristic_signals=heuristic_signals,
            )
            grouped_results.append(group_result)
            merged_signals.update(group_result.signals)
            llm_used = llm_used or group_result.backend == "openrouter"

        if not self._has_minimum_signal_coverage(merged_signals):
            data_flags.append("requires_human_review")

        if self._is_foundation_year_request(request):
            interview_coverage = self._foundation_interview_coverage(merged_signals)
            if interview_coverage < 5:
                data_flags.append("insufficient_interview_coverage")
            if interview_coverage < 4:
                data_flags.append("requires_human_review")

        if used_transcription_fallback and transcript_text and len(transcript_text) < 40:
            data_flags.append("low_asr_confidence")

        model_version = request.m5_model_version
        if llm_used and model_version == "heuristic-groq-v1":
            model_version = f"{self.llm_client.primary_model}:grouped-v1"

        envelope = SignalEnvelope(
            candidate_id=request.candidate_id,
            signal_schema_version=request.signal_schema_version,
            m5_model_version=model_version,
            selected_program=request.selected_program,
            program_id=normalize_program_id(request.selected_program),
            completeness=clamp(request.completeness),
            data_flags=list(dict.fromkeys(data_flags)),
            signals=merged_signals,
        )
        return GroupedExtractionResult(
            envelope=envelope,
            groups=grouped_results,
            used_transcription_fallback=used_transcription_fallback,
        )

    def _extract_one_group(
        self,
        *,
        spec: SignalGroupSpec,
        request: M5ExtractionRequest,
        sources: NormalizedSources,
        heuristic_signals: dict[str, SignalPayload],
    ) -> SignalGroupResult:
        available_sources = sources.available(spec.source_fields)
        fallback_signals = {
            signal_name: heuristic_signals[signal_name]
            for signal_name in spec.signals
            if signal_name in heuristic_signals
        }
        notes: list[str] = []

        if self.enable_llm and available_sources:
            try:
                llm_signals = self.llm_client.extract_group(spec=spec, request=request, sources=sources)
                merged = self._merge_group_signals(
                    spec=spec,
                    llm_signals=llm_signals,
                    fallback_signals=fallback_signals,
                    available_sources=available_sources,
                    sources=sources,
                )
                return SignalGroupResult(
                    group_name=spec.name,
                    backend="openrouter",
                    signals=merged,
                    source_fields=available_sources,
                    notes=notes,
                )
            except Exception as exc:  # pragma: no cover
                notes.append(f"llm_fallback:{exc.__class__.__name__}")

        return SignalGroupResult(
            group_name=spec.name,
            backend="heuristic",
            signals=fallback_signals,
            source_fields=available_sources,
            notes=notes,
        )

    def _merge_group_signals(
        self,
        *,
        spec: SignalGroupSpec,
        llm_signals: dict[str, SignalPayload],
        fallback_signals: dict[str, SignalPayload],
        available_sources: list[str],
        sources: NormalizedSources,
    ) -> dict[str, SignalPayload]:
        merged: dict[str, SignalPayload] = {}
        for signal_name in spec.signals:
            payload = llm_signals.get(signal_name) or fallback_signals.get(signal_name)
            if payload is None:
                continue
            merged[signal_name] = SignalPayload(
                value=clamp(payload.value),
                confidence=clamp(payload.confidence),
                source=payload.source or available_sources,
                evidence=(payload.evidence or self._default_evidence(sources, available_sources))[:2],
                reasoning=payload.reasoning,
            )
        return merged

    def _build_sources(self, request: M5ExtractionRequest, transcript_text: str | None = None) -> NormalizedSources:
        internal_test_text = " ".join(answer.answer_text for answer in request.internal_test_answers if answer.answer_text)
        projects_text = " ".join(project for project in request.project_descriptions if project)
        return NormalizedSources(
            video_transcript=strip_admissions_exam_content(transcript_text or request.video_transcript),
            essay=strip_admissions_exam_content(request.essay_text),
            project_descriptions=strip_admissions_exam_content(projects_text),
            experience_summary=strip_admissions_exam_content(request.experience_summary),
            internal_test_answers=strip_admissions_exam_content(internal_test_text),
            selected_program=normalize_text(request.selected_program),
        )

    def _build_heuristic_signal_map(
        self,
        request: M5ExtractionRequest,
        *,
        transcript_text: str,
        sources: NormalizedSources,
    ) -> dict[str, SignalPayload]:
        signal_map = dict(self.extractor.extract(request, transcript_text=transcript_text))

        if "responsibility_examples" not in signal_map:
            responsibility_signal = self._keyword_signal(
                sources=sources,
                source_names=["video_transcript", "essay", "experience_summary", "project_descriptions"],
                keywords=RESPONSIBILITY_KEYWORDS,
                reasoning="responsibility examples are supported by explicit ownership or accountability cues.",
            )
            if responsibility_signal is not None:
                signal_map["responsibility_examples"] = responsibility_signal

        if "decision_making_style" not in signal_map:
            decision_signal = self._decision_making_signal(sources)
            if decision_signal is not None:
                signal_map["decision_making_style"] = decision_signal

        if "voice_consistency" not in signal_map and sources.essay and sources.video_transcript:
            signal_map["voice_consistency"] = SignalPayload(
                value=voice_consistency_score(sources.essay, sources.video_transcript),
                confidence=authenticity_confidence(sources.essay, sources.video_transcript),
                source=["essay", "video_transcript"],
                evidence=self._default_evidence(sources, ["essay", "video_transcript"]),
                reasoning="voice consistency compares written and spoken narrative overlap.",
            )

        if "specificity_score" not in signal_map:
            narrative = " ".join(
                part
                for part in [sources.essay, sources.project_descriptions, sources.experience_summary, sources.video_transcript]
                if part
            )
            if narrative:
                signal_map["specificity_score"] = SignalPayload(
                    value=specificity_score(narrative),
                    confidence=clamp(0.45 + min(0.25, len(tokenize(narrative)) / 180)),
                    source=[
                        source_name
                        for source_name in ["essay", "project_descriptions", "experience_summary", "video_transcript"]
                        if sources.get(source_name)
                    ],
                    evidence=self._default_evidence(
                        sources,
                        ["essay", "project_descriptions", "experience_summary", "video_transcript"],
                    ),
                    reasoning="specificity is derived from the amount of concrete examples in the narrative.",
                )

        if "ai_writing_risk" not in signal_map and sources.essay:
            signal_map["ai_writing_risk"] = SignalPayload(
                value=ai_writing_risk_score(
                    essay_text=sources.essay,
                    transcript_text=sources.video_transcript,
                    project_text=sources.project_descriptions,
                ),
                confidence=authenticity_confidence(sources.essay, sources.video_transcript),
                source=["essay"] + (["video_transcript"] if sources.video_transcript else []),
                evidence=self._default_evidence(sources, ["essay", "video_transcript"]),
                reasoning="ai-writing risk is advisory and based on genericity, specificity, and voice alignment.",
            )

        return signal_map

    def _keyword_signal(
        self,
        *,
        sources: NormalizedSources,
        source_names: list[str],
        keywords: list[str],
        reasoning: str,
    ) -> SignalPayload | None:
        evidence: list[str] = []
        matched_sources: list[str] = []
        hit_count = 0
        snippet_specificity: list[float] = []

        for source_name in source_names:
            text = sources.get(source_name)
            if not text:
                continue
            matches = self._matching_snippets(text, keywords, limit=2)
            if matches:
                matched_sources.append(source_name)
                evidence.extend(matches[:1])
                hit_count += len(matches)
                snippet_specificity.append(specificity_score(" ".join(matches[:1])))

        if not evidence:
            return None

        value = clamp(
            0.30
            + min(0.28, hit_count * 0.09)
            + min(0.18, len(matched_sources) * 0.07)
            + min(0.18, (mean(snippet_specificity) if snippet_specificity else 0.0) * 0.22)
        )
        confidence = clamp(
            0.45
            + min(0.22, hit_count * 0.06)
            + min(0.12, len(matched_sources) * 0.05)
            + min(0.08, len(evidence) * 0.04)
        )
        return SignalPayload(
            value=value,
            confidence=confidence,
            source=matched_sources,
            evidence=evidence[:2],
            reasoning=reasoning,
        )

    def _decision_making_signal(self, sources: NormalizedSources) -> SignalPayload | None:
        text = " ".join(part for part in [sources.internal_test_answers, sources.essay, sources.video_transcript] if part)
        if not text:
            return None

        lowered = text.lower()
        keyword_hits = sum(1 for keyword in DECISION_KEYWORDS if keyword in lowered)
        evidence = self._matching_snippets(text, DECISION_KEYWORDS, limit=2) or split_sentences(text)[:2]
        if keyword_hits == 0 and not evidence:
            return None

        value = clamp(
            0.28
            + min(0.34, keyword_hits * 0.06)
            + min(0.20, specificity_score(text) * 0.24)
            + min(0.12, len(evidence) * 0.05)
        )
        confidence = clamp(
            0.42
            + min(0.24, keyword_hits * 0.05)
            + min(0.10, len(evidence) * 0.04)
            + min(0.08, len(text) / 600)
        )
        return SignalPayload(
            value=value,
            confidence=confidence,
            source=[source_name for source_name in ["internal_test_answers", "essay", "video_transcript"] if sources.get(source_name)],
            evidence=evidence[:2],
            reasoning="decision making style is inferred from explicit tradeoff, criteria, and justification language.",
        )

    def _matching_snippets(self, text: str, keywords: list[str], limit: int = 2) -> list[str]:
        matches: list[str] = []
        for sentence in split_sentences(text):
            lowered = sentence.lower()
            if any(keyword in lowered for keyword in keywords):
                matches.append(sentence[:220])
            if len(matches) >= limit:
                break
        return matches

    def _default_evidence(self, sources: NormalizedSources, source_names: list[str]) -> list[str]:
        evidence: list[str] = []
        for source_name in source_names:
            text = sources.get(source_name)
            if not text:
                continue
            sentences = split_sentences(text)
            if sentences:
                evidence.append(sentences[0][:220])
            if len(evidence) >= 2:
                break
        return evidence

    def _has_minimum_signal_coverage(self, signals: dict[str, SignalPayload]) -> bool:
        return any(signal_name in signals for signal_name in CORE_SIGNAL_NAMES)

    def _is_foundation_year_request(self, request: M5ExtractionRequest) -> bool:
        selected_program = normalize_text(request.selected_program).lower()
        return any(marker in selected_program for marker in FOUNDATION_YEAR_MARKERS)

    def _foundation_interview_coverage(self, signals: dict[str, SignalPayload]) -> int:
        return sum(
            1
            for required_signals in FOUNDATION_INTERVIEW_CRITERIA.values()
            if any(signal_name in signals for signal_name in required_signals)
        )


# File summary: signal_extraction_service.py
# Provides a grouped M5 service with OpenRouter-ready extraction and heuristic fallback.
