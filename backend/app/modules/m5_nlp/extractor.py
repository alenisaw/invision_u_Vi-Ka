"""
File: extractor.py
Purpose: Deterministic baseline signal extractor for M5.
"""

from __future__ import annotations

from statistics import mean

from backend.app.modules.m6_scoring.schemas import SignalPayload
from backend.app.modules.m6_scoring.program_policy import get_program_definition, normalize_program_id

from .ai_detector import ai_writing_risk_score, authenticity_confidence, specificity_score, voice_consistency_score
from .embeddings import clamp, split_sentences, token_overlap_ratio, tokenize
from .schemas import M5ExtractionRequest
from .source_bundle import SourceBundle, build_source_bundle, keyword_signal, matching_snippets


SOURCE_ORDER = [
    "video_transcript",
    "essay",
    "project_descriptions",
    "experience_summary",
    "internal_test_answers",
]

KEYWORDS: dict[str, list[str]] = {
    "leadership_indicators": ["lead", "led", "leader", "managed", "organized", "captain", "mentor", "coordinated"],
    "team_leadership": ["team", "group", "committee", "peers", "collaborat", "crew"],
    "growth_trajectory": ["improved", "learned", "grew", "adapted", "challenge", "overcame", "progress"],
    "challenges_overcome": ["challenge", "problem", "difficult", "failed", "mistake", "obstacle"],
    "motivation_clarity": ["goal", "purpose", "motivation", "want", "aspire", "why", "future"],
    "goal_specificity": ["plan", "roadmap", "specific", "step", "milestone", "long-term goal", "goal is", "plan to"],
    "agency_signals": ["started", "built", "created", "founded", "launched", "took initiative"],
    "self_started_projects": ["project", "app", "platform", "club", "startup", "initiative"],
    "proactivity_examples": ["before asked", "on my own", "proactive", "volunteer", "extra"],
    "learning_agility": ["adapt", "learn", "quickly", "feedback", "new skill", "experiment"],
    "resilience_evidence": ["obstacle", "challenge", "failed", "kept going", "support helped", "did not quit"],
    "ethical_reasoning": ["fair", "ethical", "responsible", "honest", "tradeoff", "integrity"],
    "civic_orientation": ["community", "volunteer", "helped", "social impact", "support others"],
    "future_goals_alignment": ["long-term goal", "future goal", "career", "become", "my dream", "this program will help"],
    "leadership_reflection": ["leader means", "to me a leader", "lead by example", "take responsibility"],
    "teamwork_problem_solving": ["team problem", "resolved a conflict", "split the work", "worked together", "coordinator"],
    "support_network": ["family support", "supported my choice", "encouraged me", "inspired me", "mentor", "teacher"],
    "english_growth": ["english", "practice", "speaking", "vocabulary", "reading", "lessons"],
}

STRUCTURE_MARKERS = ["first", "second", "then", "finally", "because", "therefore"]
IDEA_MARKERS = ["for example", "for instance", "because", "so that", "which means"]
FOUNDATION_PROGRAM_MARKERS = ["foundation year", "foundation"]
FOUNDATION_ALIGNMENT_KEYWORDS = [
    "foundation", "academic english", "english", "bachelor", "university", "prepare", "preparation", "adapt",
]


class HeuristicSignalExtractor:
    """Deterministic baseline extractor that keeps M5 -> M6 available without LLM access."""

    def extract(self, request: M5ExtractionRequest, transcript_text: str | None = None) -> dict[str, SignalPayload]:
        sources = build_source_bundle(request, transcript_text=transcript_text)
        signals = self._extract_keyword_signals(sources)
        signals.update(self._extract_derived_signals(sources))
        return signals

    def _extract_keyword_signals(self, sources: SourceBundle) -> dict[str, SignalPayload]:
        signals: dict[str, SignalPayload] = {}
        for signal_name, source_names in self._keyword_specs():
            payload = keyword_signal(
                sources=sources,
                source_names=source_names,
                keywords=KEYWORDS[signal_name],
                reasoning=f"{signal_name.replace('_', ' ')} is supported by concrete text cues.",
            )
            if payload is not None:
                signals[signal_name] = payload
        return signals

    def _extract_derived_signals(self, sources: SourceBundle) -> dict[str, SignalPayload]:
        signals: dict[str, SignalPayload] = {}
        for signal_name, builder in (
            ("clarity_score", self._clarity_signal),
            ("structure_score", self._structure_signal),
            ("idea_articulation", self._idea_articulation_signal),
            ("program_alignment", self._program_alignment_signal),
            ("essay_transcript_consistency", self._essay_transcript_consistency_signal),
            ("claims_evidence_match", self._claims_evidence_match_signal),
            ("specificity_score", self._specificity_signal),
            ("voice_consistency", self._voice_consistency_signal),
            ("ai_writing_risk", self._ai_writing_risk_signal),
        ):
            payload = builder(sources)
            if payload is not None:
                signals[signal_name] = payload
        return signals

    def _keyword_specs(self) -> tuple[tuple[str, list[str]], ...]:
        return (
            ("leadership_indicators", ["video_transcript", "essay", "project_descriptions", "experience_summary"]),
            ("team_leadership", ["video_transcript", "essay", "project_descriptions"]),
            ("leadership_reflection", ["video_transcript", "essay", "internal_test_answers"]),
            ("growth_trajectory", ["essay", "experience_summary", "video_transcript"]),
            ("challenges_overcome", ["essay", "experience_summary", "video_transcript"]),
            ("resilience_evidence", ["video_transcript", "essay", "experience_summary"]),
            ("motivation_clarity", ["essay", "video_transcript"]),
            ("goal_specificity", ["essay", "video_transcript", "selected_program"]),
            ("future_goals_alignment", ["essay", "video_transcript", "selected_program"]),
            ("agency_signals", ["project_descriptions", "essay", "experience_summary"]),
            ("self_started_projects", ["project_descriptions", "essay"]),
            ("proactivity_examples", ["essay", "experience_summary", "project_descriptions"]),
            ("teamwork_problem_solving", ["video_transcript", "essay", "project_descriptions", "experience_summary"]),
            ("learning_agility", ["essay", "video_transcript", "internal_test_answers"]),
            ("english_growth", ["video_transcript", "essay"]),
            ("ethical_reasoning", ["internal_test_answers", "essay", "video_transcript"]),
            ("civic_orientation", ["experience_summary", "essay", "video_transcript"]),
            ("support_network", ["video_transcript", "essay", "experience_summary"]),
        )

    def _clarity_signal(self, sources: SourceBundle) -> SignalPayload | None:
        primary_text = sources.video_transcript or sources.essay
        if not primary_text:
            return None
        sentences = split_sentences(primary_text)
        if not sentences:
            return None
        sentence_lengths = [len(tokenize(sentence)) for sentence in sentences[:8]]
        avg_length = mean(sentence_lengths) if sentence_lengths else 0.0
        balanced_length = 1.0 - min(1.0, abs(avg_length - 16) / 16) if avg_length else 0.0
        return SignalPayload(
            value=clamp(0.35 + balanced_length * 0.45 + min(0.20, len(sentences) / 20)),
            confidence=clamp(0.45 + min(0.25, len(sentences) / 20)),
            source=["video_transcript"] if sources.video_transcript else ["essay"],
            evidence=sentences[:2],
            reasoning="communication remains understandable and organized across available narrative text.",
        )

    def _structure_signal(self, sources: SourceBundle) -> SignalPayload | None:
        text = sources.video_transcript or sources.essay
        if not text:
            return None
        hits = sum(1 for marker in STRUCTURE_MARKERS if marker in text.lower())
        sentences = split_sentences(text)
        evidence = matching_snippets(text, STRUCTURE_MARKERS, limit=2) or sentences[:2]
        return SignalPayload(
            value=clamp(0.30 + min(0.45, hits * 0.10) + min(0.20, len(sentences) / 25)),
            confidence=clamp(0.40 + min(0.25, hits * 0.07) + min(0.15, len(sentences) / 25)),
            source=["video_transcript"] if sources.video_transcript else ["essay"],
            evidence=evidence,
            reasoning="candidate uses ordering or causal markers that improve structure.",
        )

    def _idea_articulation_signal(self, sources: SourceBundle) -> SignalPayload | None:
        text = " ".join(part for part in [sources.video_transcript, sources.essay, sources.internal_test_answers] if part)
        if not text:
            return None
        hits = sum(1 for marker in IDEA_MARKERS if marker in text.lower())
        evidence = matching_snippets(text, IDEA_MARKERS, limit=2) or split_sentences(text)[:2]
        return SignalPayload(
            value=clamp(0.32 + min(0.48, hits * 0.12) + min(0.12, specificity_score(text) * 0.15)),
            confidence=clamp(0.42 + min(0.25, hits * 0.07) + min(0.10, len(evidence) * 0.05)),
            source=[name for name in ["video_transcript", "essay", "internal_test_answers"] if sources.get(name)],
            evidence=evidence,
            reasoning="candidate articulates examples and causal logic in narrative answers.",
        )

    def _program_alignment_signal(self, sources: SourceBundle) -> SignalPayload | None:
        if not sources.selected_program:
            return None
        candidate_text = " ".join(
            part for part in [sources.essay, sources.project_descriptions, sources.experience_summary, sources.video_transcript] if part
        )
        if not candidate_text:
            return None
        program_id = normalize_program_id(sources.selected_program)
        program_definition = get_program_definition(program_id)
        display_name = str(program_definition.get("display_name", sources.selected_program))
        fit_keywords = [str(keyword).lower() for keyword in program_definition.get("fit_keywords", [])]
        overlap = token_overlap_ratio(display_name, candidate_text)
        keyword_hits = sum(1 for keyword in fit_keywords if keyword in candidate_text.lower())
        foundation_bonus = 0.0
        if any(marker in display_name.lower() for marker in FOUNDATION_PROGRAM_MARKERS):
            foundation_hits = sum(1 for keyword in FOUNDATION_ALIGNMENT_KEYWORDS if keyword in candidate_text.lower())
            foundation_bonus = min(0.18, foundation_hits * 0.03 + specificity_score(candidate_text) * 0.04)
        evidence = split_sentences(candidate_text)[:2]
        return SignalPayload(
            value=clamp(0.24 + overlap * 0.50 + min(0.18, keyword_hits * 0.04) + min(0.15, specificity_score(candidate_text) * 0.15) + foundation_bonus),
            confidence=clamp(0.45 + overlap * 0.28 + min(0.14, keyword_hits * 0.025) + min(0.10, foundation_bonus * 0.5)),
            source=[name for name in ["essay", "project_descriptions", "experience_summary", "video_transcript"] if sources.get(name)] + ["selected_program"],
            evidence=evidence[:2],
            reasoning="selected program shares topical overlap and program-specific competency cues with the candidate narrative.",
        )

    def _essay_transcript_consistency_signal(self, sources: SourceBundle) -> SignalPayload | None:
        if not sources.essay or not sources.video_transcript:
            return None
        evidence = [
            split_sentences(sources.essay)[0] if split_sentences(sources.essay) else sources.essay[:180],
            split_sentences(sources.video_transcript)[0] if split_sentences(sources.video_transcript) else sources.video_transcript[:180],
        ]
        overlap = token_overlap_ratio(sources.essay, sources.video_transcript)
        return SignalPayload(
            value=clamp(0.25 + overlap * 0.75),
            confidence=clamp(0.50 + min(0.25, len(tokenize(sources.essay + sources.video_transcript)) / 250)),
            source=["essay", "video_transcript"],
            evidence=evidence,
            reasoning="essay and spoken narrative share lexical and thematic overlap.",
        )

    def _claims_evidence_match_signal(self, sources: SourceBundle) -> SignalPayload | None:
        texts = [part for part in [sources.essay, sources.project_descriptions, sources.experience_summary, sources.video_transcript] if part]
        if not texts:
            return None
        specificities = [specificity_score(text) for text in texts]
        evidence = [split_sentences(text)[0] for text in texts[:2] if split_sentences(text)]
        return SignalPayload(
            value=clamp(0.30 + mean(specificities) * 0.60),
            confidence=clamp(0.45 + min(0.25, len(texts) * 0.06)),
            source=[name for name in SOURCE_ORDER if sources.get(name)],
            evidence=evidence[:2],
            reasoning="claims are evaluated against the amount of concrete detail and example density.",
        )

    def _specificity_signal(self, sources: SourceBundle) -> SignalPayload | None:
        narrative = " ".join(part for part in [sources.essay, sources.project_descriptions, sources.experience_summary, sources.video_transcript] if part)
        if not narrative:
            return None
        return SignalPayload(
            value=specificity_score(narrative),
            confidence=clamp(0.45 + min(0.25, len(tokenize(narrative)) / 180)),
            source=[name for name in SOURCE_ORDER if sources.get(name)],
            evidence=split_sentences(narrative)[:2],
            reasoning="specificity is derived from the amount of concrete, example-based narrative detail.",
        )

    def _voice_consistency_signal(self, sources: SourceBundle) -> SignalPayload | None:
        if not sources.essay or not sources.video_transcript:
            return None
        evidence = [
            split_sentences(sources.essay)[0] if split_sentences(sources.essay) else sources.essay[:180],
            split_sentences(sources.video_transcript)[0] if split_sentences(sources.video_transcript) else sources.video_transcript[:180],
        ]
        return SignalPayload(
            value=voice_consistency_score(sources.essay, sources.video_transcript),
            confidence=authenticity_confidence(sources.essay, sources.video_transcript),
            source=["essay", "video_transcript"],
            evidence=evidence,
            reasoning="voice consistency compares lexical and narrative overlap between written and spoken responses.",
        )

    def _ai_writing_risk_signal(self, sources: SourceBundle) -> SignalPayload | None:
        if not sources.essay:
            return None
        evidence = split_sentences(sources.essay)[:1]
        if sources.video_transcript:
            evidence.extend(split_sentences(sources.video_transcript)[:1])
        return SignalPayload(
            value=ai_writing_risk_score(
                essay_text=sources.essay,
                transcript_text=sources.video_transcript,
                project_text=sources.project_descriptions,
            ),
            confidence=authenticity_confidence(sources.essay, sources.video_transcript),
            source=["essay"] + (["video_transcript"] if sources.video_transcript else []),
            evidence=evidence[:2],
            reasoning="ai-writing risk is advisory and based on genericity, specificity, and voice alignment heuristics.",
        )


# File summary: extractor.py
# Implements a deterministic baseline extractor for M5 using shared source helpers.
