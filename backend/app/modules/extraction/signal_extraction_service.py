"""
File: signal_extraction_service.py
Purpose: Grouped extraction with Groq-backed Llama support and heuristic fallback.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.modules.scoring.program_policy import normalize_program_id
from app.modules.scoring.schemas import SignalEnvelope, SignalPayload

from .ai_detector import (
    ai_writing_risk_score,
    authenticity_confidence,
    authenticity_risk_score,
    specificity_score,
    transcript_authenticity_risk_score,
    voice_consistency_score,
)
from .client import GroqTranscriptionClient
from .embeddings import clamp, tokenize
from .extractor import HeuristicSignalExtractor
from .groq_llm_client import GroqSignalClient
from .llm_shared import SignalGroupSpec
from .schemas import ExtractionRequest
from .source_bundle import SourceBundle, build_source_bundle, default_evidence, keyword_signal


logger = logging.getLogger(__name__)

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
FOUNDATION_YEAR_MARKERS = (
    "foundation year",
    "foundation",
    "\u043f\u043e\u0434\u0433\u043e\u0442\u043e\u0432\u0438\u0442\u0435\u043b\u044c",
)
FOUNDATION_INTERVIEW_CRITERIA = {
    "motivation": ("motivation_clarity", "program_alignment"),
    "goals": ("goal_specificity", "future_goals_alignment"),
    "resilience": ("challenges_overcome", "resilience_evidence"),
    "leadership": ("leadership_indicators", "leadership_reflection"),
    "teamwork": ("team_leadership", "teamwork_problem_solving"),
    "support_context": ("support_network",),
    "english_growth": ("english_growth",),
}
RESPONSIBILITY_KEYWORDS = ["responsible", "responsibility", "accountable", "ownership", "deadline", "budget", "mentored"]
DECISION_KEYWORDS = ["decide", "decision", "tradeoff", "consider", "because", "choose", "alternative", "risk", "balance", "criteria"]


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
        signals=("authenticity_risk", "ai_writing_risk", "voice_consistency", "specificity_score"),
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
        purpose="Capture support context without turning family background into a positive proxy score.",
        model_tier="fast",
    ),
)


@dataclass(frozen=True)
class SignalGroupResult:
    group_name: str
    backend: str
    signals: dict[str, SignalPayload]
    source_fields: tuple[str, ...]
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class GroupedExtractionResult:
    envelope: SignalEnvelope
    groups: tuple[SignalGroupResult, ...]
    used_transcription_fallback: bool = False


class GroupedExtractionService:
    """Architecture-aligned extraction service with grouped provider-aware fallback."""

    def __init__(
        self,
        extractor: HeuristicSignalExtractor | None = None,
        transcription_client: GroqTranscriptionClient | None = None,
        llm_client: GroqSignalClient | None = None,
        enable_llm: bool | None = None,
    ) -> None:
        self.extractor = extractor or HeuristicSignalExtractor()
        self.transcription_client = transcription_client or GroqTranscriptionClient()
        self.llm_client = llm_client or self._build_default_llm_client()
        self.enable_llm = self.llm_client.enabled if enable_llm is None else bool(enable_llm and self.llm_client.enabled)

    @staticmethod
    def _build_default_llm_client() -> GroqSignalClient:
        """Use Groq as the only active LLM backend for the extraction stage."""
        groq_client = GroqSignalClient()
        if groq_client.enabled:
            logger.info("Extraction LLM backend: Groq (%s)", groq_client.primary_model)
            return groq_client
        logger.warning("Extraction LLM backend: none (heuristic-only mode)")
        return groq_client

    def extract_signals(self, request: ExtractionRequest) -> SignalEnvelope:
        return self.extract_signal_groups(request).envelope

    def extract_from_payload(self, payload: dict) -> SignalEnvelope:
        return self.extract_signals(ExtractionRequest.model_validate(payload))

    def extract_signal_groups(self, request: ExtractionRequest) -> GroupedExtractionResult:
        transcript_text, data_flags, used_transcription_fallback = self._resolve_transcript(request)
        sources = build_source_bundle(request, transcript_text=transcript_text)
        heuristic_signals = self._build_heuristic_signal_map(request=request, transcript_text=transcript_text, sources=sources)

        grouped_results: list[SignalGroupResult] = []
        merged_signals: dict[str, SignalPayload] = {}
        llm_used = False
        for spec in SIGNAL_GROUP_SPECS:
            group_result = self._extract_one_group(spec=spec, request=request, sources=sources, heuristic_signals=heuristic_signals)
            grouped_results.append(group_result)
            merged_signals.update(group_result.signals)
            llm_used = llm_used or group_result.backend != "heuristic"

        data_flags = self._finalize_data_flags(
            request=request,
            transcript_text=transcript_text,
            used_transcription_fallback=used_transcription_fallback,
            merged_signals=merged_signals,
            data_flags=data_flags,
        )
        model_version = self._resolve_model_version(request, llm_used)
        envelope = SignalEnvelope(
            candidate_id=request.candidate_id,
            signal_schema_version=request.signal_schema_version,
            extraction_model_version=model_version,
            selected_program=request.selected_program,
            program_id=normalize_program_id(request.selected_program),
            completeness=clamp(request.completeness),
            data_flags=data_flags,
            signals=merged_signals,
        )
        return GroupedExtractionResult(
            envelope=envelope,
            groups=tuple(grouped_results),
            used_transcription_fallback=used_transcription_fallback,
        )

    def _resolve_transcript(self, request: ExtractionRequest) -> tuple[str, list[str], bool]:
        transcript_text = request.video_transcript
        data_flags = list(dict.fromkeys(request.data_flags))
        used_transcription_fallback = False
        if transcript_text or not request.interview_media_path:
            return transcript_text, data_flags, used_transcription_fallback

        used_transcription_fallback = True
        transcription_payload = self.transcription_client.transcribe_media(request.interview_media_path, language=request.language)
        transcript_text = str(transcription_payload.get("text", "")).strip()
        if not transcript_text:
            data_flags.append("no_speech_detected")
        return transcript_text, data_flags, used_transcription_fallback

    def _extract_one_group(
        self,
        *,
        spec: SignalGroupSpec,
        request: ExtractionRequest,
        sources: SourceBundle,
        heuristic_signals: dict[str, SignalPayload],
    ) -> SignalGroupResult:
        available_sources = sources.available(spec.source_fields)
        fallback_signals = {signal_name: heuristic_signals[signal_name] for signal_name in spec.signals if signal_name in heuristic_signals}
        notes: list[str] = []
        if self.enable_llm and available_sources:
            provider_name = self._llm_backend_name()
            try:
                llm_signals = self.llm_client.extract_group(spec=spec, request_candidate_id=str(request.candidate_id), sources=sources)
                merged = self._merge_group_signals(spec, llm_signals, fallback_signals, list(available_sources), sources)
                return SignalGroupResult(
                    group_name=spec.name,
                    backend=provider_name,
                    signals=merged,
                    source_fields=available_sources,
                    notes=tuple(notes),
                )
            except Exception as exc:  # pragma: no cover
                logger.warning(
                    "Extraction backend %s fell back for group %s: %s",
                    provider_name,
                    spec.name,
                    exc.__class__.__name__,
                )
                notes.append(f"llm_fallback:{exc.__class__.__name__}")
        return SignalGroupResult(
            group_name=spec.name,
            backend="heuristic",
            signals=fallback_signals,
            source_fields=available_sources,
            notes=tuple(notes),
        )

    def _llm_backend_name(self) -> str:
        return "groq"

    def _merge_group_signals(
        self,
        spec: SignalGroupSpec,
        llm_signals: dict[str, SignalPayload],
        fallback_signals: dict[str, SignalPayload],
        available_sources: list[str],
        sources: SourceBundle,
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
                evidence=(payload.evidence or default_evidence(sources, available_sources))[:2],
                reasoning=payload.reasoning,
            )
        return merged

    def _build_heuristic_signal_map(
        self,
        *,
        request: ExtractionRequest,
        transcript_text: str,
        sources: SourceBundle,
    ) -> dict[str, SignalPayload]:
        signal_map = dict(self.extractor.extract(request, transcript_text=transcript_text))

        if "responsibility_examples" not in signal_map:
            responsibility_signal = keyword_signal(
                sources=sources,
                source_names=["video_transcript", "essay", "experience_summary", "project_descriptions"],
                keywords=RESPONSIBILITY_KEYWORDS,
                reasoning="responsibility examples are supported by explicit ownership or accountability cues.",
            )
            if responsibility_signal is not None:
                signal_map["responsibility_examples"] = responsibility_signal

        if "leadership_reflection" not in signal_map and "leadership_indicators" in signal_map:
            leadership_reflection = keyword_signal(
                sources=sources,
                source_names=["video_transcript", "essay", "internal_test_answers"],
                keywords=["leader", "leadership", "responsibility", "coordinate", "guide", "motivate"],
                reasoning="leadership reflection is inferred from self-description of leadership values or behavior.",
                base_score=0.28,
                hit_weight=0.08,
                source_weight=0.06,
                specificity_weight=0.18,
            )
            if leadership_reflection is not None:
                signal_map["leadership_reflection"] = leadership_reflection

        if "decision_making_style" not in signal_map:
            decision_signal = self._decision_making_signal(sources)
            if decision_signal is not None:
                signal_map["decision_making_style"] = decision_signal

        self._ensure_authenticity_signals(signal_map, sources)
        return signal_map

    def _ensure_authenticity_signals(self, signal_map: dict[str, SignalPayload], sources: SourceBundle) -> None:
        if "voice_consistency" not in signal_map and sources.essay and sources.video_transcript:
            signal_map["voice_consistency"] = SignalPayload(
                value=voice_consistency_score(sources.essay, sources.video_transcript),
                confidence=authenticity_confidence(sources.essay, sources.video_transcript),
                source=["essay", "video_transcript"],
                evidence=default_evidence(sources, ["essay", "video_transcript"]),
                reasoning="voice consistency compares written and spoken narrative overlap.",
            )

        if "specificity_score" not in signal_map:
            narrative = " ".join(part for part in [sources.essay, sources.project_descriptions, sources.experience_summary, sources.video_transcript] if part)
            if narrative:
                signal_map["specificity_score"] = SignalPayload(
                    value=specificity_score(narrative),
                    confidence=clamp(0.45 + min(0.25, len(tokenize(narrative)) / 180)),
                    source=[name for name in ["essay", "project_descriptions", "experience_summary", "video_transcript"] if sources.get(name)],
                    evidence=default_evidence(sources, ["essay", "project_descriptions", "experience_summary", "video_transcript"]),
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
                evidence=default_evidence(sources, ["essay", "video_transcript"]),
                reasoning="ai-writing risk is advisory and based on genericity, specificity, and voice alignment.",
            )

        if "authenticity_risk" not in signal_map and (sources.essay or sources.video_transcript):
            if sources.essay:
                value = authenticity_risk_score(
                    primary_text=sources.essay,
                    supporting_text=sources.video_transcript,
                    project_text=sources.project_descriptions,
                )
                source_names = ["essay", "video_transcript", "project_descriptions"]
                reasoning = "authenticity risk is advisory and combines essay genericity, cross-source alignment, and supporting detail."
            else:
                value = transcript_authenticity_risk_score(
                    transcript_text=sources.video_transcript,
                    essay_text=sources.essay,
                    project_text=sources.project_descriptions,
                )
                source_names = ["video_transcript", "project_descriptions"]
                reasoning = "authenticity risk is advisory and combines spoken genericity, supporting detail, and consistency with other safe sources."
            signal_map["authenticity_risk"] = SignalPayload(
                value=value,
                confidence=authenticity_confidence(sources.essay, sources.video_transcript),
                source=[name for name in source_names if sources.get(name)],
                evidence=default_evidence(sources, source_names),
                reasoning=reasoning,
            )

    def _decision_making_signal(self, sources: SourceBundle) -> SignalPayload | None:
        text = " ".join(part for part in [sources.internal_test_answers, sources.essay, sources.video_transcript] if part)
        if not text:
            return None
        keyword_hits = sum(1 for keyword in DECISION_KEYWORDS if keyword in text.lower())
        evidence = default_evidence(sources, ["internal_test_answers", "essay", "video_transcript"])
        if keyword_hits == 0 and not evidence:
            return None
        return SignalPayload(
            value=clamp(0.28 + min(0.34, keyword_hits * 0.06) + min(0.20, specificity_score(text) * 0.24) + min(0.12, len(evidence) * 0.05)),
            confidence=clamp(0.42 + min(0.24, keyword_hits * 0.05) + min(0.10, len(evidence) * 0.04) + min(0.08, len(text) / 600)),
            source=[name for name in ["internal_test_answers", "essay", "video_transcript"] if sources.get(name)],
            evidence=evidence[:2],
            reasoning="decision making style is inferred from explicit tradeoff, criteria, and justification language.",
        )

    def _finalize_data_flags(
        self,
        *,
        request: ExtractionRequest,
        transcript_text: str,
        used_transcription_fallback: bool,
        merged_signals: dict[str, SignalPayload],
        data_flags: list[str],
    ) -> list[str]:
        if not (request.essay_text or "").strip() and (transcript_text or "").strip():
            data_flags.append("essay_replaced_by_video_transcript")
        elif not (request.essay_text or "").strip():
            data_flags.append("missing_essay")
        if not (transcript_text or "").strip():
            data_flags.append("missing_video_transcript")
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
        return list(dict.fromkeys(data_flags))

    def _resolve_model_version(self, request: ExtractionRequest, llm_used: bool) -> str:
        if llm_used:
            return f"{self.llm_client.primary_model}:grouped-v1"
        return request.extraction_model_version

    @staticmethod
    def _has_minimum_signal_coverage(signals: dict[str, SignalPayload]) -> bool:
        return any(signal_name in signals for signal_name in CORE_SIGNAL_NAMES)

    @staticmethod
    def _foundation_interview_coverage(signals: dict[str, SignalPayload]) -> int:
        return sum(1 for required_signals in FOUNDATION_INTERVIEW_CRITERIA.values() if any(signal_name in signals for signal_name in required_signals))

    @staticmethod
    def _is_foundation_year_request(request: ExtractionRequest) -> bool:
        selected_program = request.selected_program.strip().lower()
        return any(marker in selected_program for marker in FOUNDATION_YEAR_MARKERS)
