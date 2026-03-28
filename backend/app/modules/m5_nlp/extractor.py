"""
File: extractor.py
Purpose: Deterministic baseline signal extractor for M5.

Notes:
- This module emits the exact `SignalEnvelope v1` shape expected by M6.
- It is intentionally heuristic so the team can ship an MVP before full LLM extraction.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from app.modules.m6_scoring.schemas import SignalPayload

from .ai_detector import (
    ai_writing_risk_score,
    authenticity_confidence,
    specificity_score,
    voice_consistency_score,
)
from .embeddings import (
    clamp,
    normalize_text,
    split_sentences,
    strip_admissions_exam_content,
    token_overlap_ratio,
    tokenize,
)
from .schemas import M5ExtractionRequest
from ..m6_scoring.program_policy import get_program_definition, normalize_program_id

SOURCE_ORDER = [
    "video_transcript",
    "essay",
    "project_descriptions",
    "experience_summary",
    "internal_test_answers",
]

KEYWORDS: dict[str, list[str]] = {
    "leadership_indicators": [
        "lead", "led", "leader", "managed", "organized", "captain", "mentor", "coordinated",
        "руковод", "лидер", "организ", "координир", "настав", "возглав",
    ],
    "team_leadership": [
        "team", "group", "committee", "peers", "collaborat", "crew",
        "команд", "групп", "вместе", "коллектив", "участник",
    ],
    "growth_trajectory": [
        "improved", "learned", "grew", "adapted", "challenge", "overcame", "progress",
        "улучш", "науч", "вырос", "адапт", "преодол", "опыт", "развив",
    ],
    "challenges_overcome": [
        "challenge", "problem", "difficult", "failed", "mistake", "obstacle",
        "сложн", "проблем", "ошиб", "трудн", "неудач", "препятств",
    ],
    "motivation_clarity": [
        "goal", "purpose", "motivation", "want", "aspire", "why", "future",
        "цель", "мотива", "хочу", "стрем", "будущ", "почему",
    ],
    "goal_specificity": [
        "plan", "roadmap", "next year", "specific", "step", "milestone", "long-term goal", "goal is",
        "plan to", "in five years", "become", "план", "шаг", "конкрет", "в течение", "этап",
        "долгосроч", "цель", "хочу стать",
    ],
    "agency_signals": [
        "started", "built", "created", "founded", "launched", "took initiative",
        "создал", "запуст", "инициир", "сам", "организовал", "сделал",
    ],
    "self_started_projects": [
        "project", "app", "platform", "club", "startup", "initiative",
        "проект", "прилож", "клуб", "стартап", "инициатив",
    ],
    "proactivity_examples": [
        "before asked", "on my own", "proactive", "volunteer", "extra",
        "самостоятель", "заранее", "дополнительно", "волонтер", "инициатив",
    ],
    "learning_agility": [
        "adapt", "learn", "quickly", "feedback", "new skill", "experiment",
        "адапт", "обратн", "новый навык", "быстро", "изуч", "эксперимент",
    ],
    "resilience_evidence": [
        "obstacle", "challenge", "failed", "kept going", "support helped", "did not quit", "pushed through",
        "препятств", "сложност", "неудач", "поддерж", "не сдал", "продолж", "преодол",
    ],
    "ethical_reasoning": [
        "fair", "ethical", "responsible", "honest", "tradeoff", "integrity",
        "справед", "этич", "ответствен", "честн", "компромисс",
    ],
    "civic_orientation": [
        "community", "volunteer", "helped", "social impact", "support others",
        "сообще", "волонтер", "помог", "обществен", "поддерж",
    ],
    "future_goals_alignment": [
        "long-term goal", "long term", "future goal", "career", "become", "my dream", "this program will help",
        "foundation year will help", "prepare me", "goal", "future", "мечта", "долгосроч", "будущ",
        "поможет мне", "подготов", "хочу стать", "карьер",
    ],
    "leadership_reflection": [
        "being a leader", "leader means", "to me a leader", "lead by example", "take responsibility",
        "leader listens", "быть лидером", "лидер это", "для меня лидер", "вести за собой", "служить примером",
        "брать ответственность",
    ],
    "teamwork_problem_solving": [
        "team problem", "resolved a conflict", "split the work", "worked together", "my role", "coordinator",
        "deadline", "solution", "команд", "конфликт", "решили", "вместе", "роль", "координ",
        "распредел", "срок",
    ],
    "support_network": [
        "my family", "family support", "supported my choice", "encouraged me", "inspired me", "mentor",
        "teacher", "mother", "father", "sister", "brother", "семья", "поддерж", "вдохнов", "настав",
        "учитель", "мама", "папа", "сестра", "брат",
    ],
    "english_growth": [
        "english", "i practice", "speaking", "vocabulary", "reading", "watch lessons", "present in english",
        "learn the language", "speaking every day", "англий", "учу язык", "словар", "читаю", "смотрю",
        "говорю", "практикую", "уроки",
    ],
}

STRUCTURE_MARKERS = [
    "first", "second", "then", "finally", "because", "therefore",
    "сначала", "затем", "потом", "наконец", "потому", "поэтому",
]

IDEA_MARKERS = [
    "for example", "for instance", "because", "so that", "which means",
    "например", "потому что", "это значит", "поэтому",
]

FOUNDATION_PROGRAM_MARKERS = [
    "foundation year",
    "foundation",
    "подготовитель",
]

FOUNDATION_ALIGNMENT_KEYWORDS = [
    "foundation",
    "academic english",
    "english",
    "bachelor",
    "university",
    "prepare",
    "preparation",
    "adapt",
    "transition",
    "skills",
    "бакалавр",
    "академ",
    "англий",
    "подготов",
    "университ",
    "адапт",
]


@dataclass
class SourceBundle:
    """Normalized source texts used to derive signals."""

    video_transcript: str
    essay: str
    project_descriptions: str
    experience_summary: str
    internal_test_answers: str
    selected_program: str

    def get(self, source_name: str) -> str:
        return getattr(self, source_name, "")


class HeuristicSignalExtractor:
    """MVP baseline extractor that produces M6-compatible signals."""

    def extract(self, request: M5ExtractionRequest, transcript_text: str | None = None) -> dict[str, SignalPayload]:
        """Extract a signal map from safe candidate content."""

        sources = self._build_sources(request, transcript_text=transcript_text)
        signals: dict[str, SignalPayload] = {}

        for signal_name, source_names in [
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
        ]:
            payload = self._keyword_signal(
                sources=sources,
                source_names=source_names,
                keywords=KEYWORDS[signal_name],
                reasoning=f"{signal_name.replace('_', ' ')} is supported by concrete text cues.",
            )
            if payload is not None:
                signals[signal_name] = payload

        clarity = self._clarity_signal(sources)
        if clarity is not None:
            signals["clarity_score"] = clarity

        structure = self._structure_signal(sources)
        if structure is not None:
            signals["structure_score"] = structure

        idea_articulation = self._idea_articulation_signal(sources)
        if idea_articulation is not None:
            signals["idea_articulation"] = idea_articulation

        program_alignment = self._program_alignment_signal(sources)
        if program_alignment is not None:
            signals["program_alignment"] = program_alignment

        consistency = self._essay_transcript_consistency_signal(sources)
        if consistency is not None:
            signals["essay_transcript_consistency"] = consistency

        claims_match = self._claims_evidence_match_signal(sources)
        if claims_match is not None:
            signals["claims_evidence_match"] = claims_match

        specificity = self._specificity_signal(sources)
        if specificity is not None:
            signals["specificity_score"] = specificity

        voice_consistency = self._voice_consistency_signal(sources)
        if voice_consistency is not None:
            signals["voice_consistency"] = voice_consistency

        ai_risk = self._ai_writing_risk_signal(sources)
        if ai_risk is not None:
            signals["ai_writing_risk"] = ai_risk

        return signals

    def _build_sources(self, request: M5ExtractionRequest, transcript_text: str | None = None) -> SourceBundle:
        """Normalize all safe input sources into a consistent bundle."""

        internal_test_text = " ".join(answer.answer_text for answer in request.internal_test_answers if answer.answer_text)
        projects_text = " ".join(project for project in request.project_descriptions if project)
        return SourceBundle(
            video_transcript=strip_admissions_exam_content(transcript_text or request.video_transcript),
            essay=strip_admissions_exam_content(request.essay_text),
            project_descriptions=strip_admissions_exam_content(projects_text),
            experience_summary=strip_admissions_exam_content(request.experience_summary),
            internal_test_answers=strip_admissions_exam_content(internal_test_text),
            selected_program=normalize_text(request.selected_program),
        )

    def _keyword_signal(
        self,
        *,
        sources: SourceBundle,
        source_names: list[str],
        keywords: list[str],
        reasoning: str,
    ) -> SignalPayload | None:
        """Create one keyword-driven signal from a subset of sources."""

        evidence: list[str] = []
        matched_sources: list[str] = []
        total_hits = 0
        specificity_values: list[float] = []

        for source_name in source_names:
            text = sources.get(source_name)
            if not text:
                continue

            matches = self._matching_sentences(text, keywords)
            if matches:
                matched_sources.append(source_name)
                evidence.extend(matches[:1])
                total_hits += len(matches)
                specificity_values.append(specificity_score(" ".join(matches[:1])))

        if not evidence:
            return None

        value = clamp(
            0.30
            + min(0.30, total_hits * 0.10)
            + min(0.20, len(matched_sources) * 0.07)
            + min(0.20, mean(specificity_values) * 0.25 if specificity_values else 0.0)
        )
        confidence = clamp(
            0.45
            + min(0.20, total_hits * 0.06)
            + min(0.15, len(matched_sources) * 0.05)
            + min(0.15, len(evidence) * 0.05)
        )
        return SignalPayload(
            value=value,
            confidence=confidence,
            source=matched_sources,
            evidence=evidence[:2],
            reasoning=reasoning,
        )

    def _matching_sentences(self, text: str, keywords: list[str], limit: int = 2) -> list[str]:
        """Return the best matching sentences for a keyword bundle."""

        matches: list[str] = []
        for sentence in split_sentences(text):
            lowered = sentence.lower()
            if any(keyword in lowered for keyword in keywords):
                matches.append(sentence[:220])
            if len(matches) >= limit:
                break
        return matches

    def _clarity_signal(self, sources: SourceBundle) -> SignalPayload | None:
        """Estimate communication clarity from transcript and essay structure."""

        primary_text = sources.video_transcript or sources.essay
        if not primary_text:
            return None

        sentences = split_sentences(primary_text)
        if not sentences:
            return None
        sentence_lengths = [len(tokenize(sentence)) for sentence in sentences[:8]]
        avg_length = mean(sentence_lengths) if sentence_lengths else 0.0
        balanced_length = 1.0 - min(1.0, abs(avg_length - 16) / 16) if avg_length else 0.0
        value = clamp(0.35 + balanced_length * 0.45 + min(0.20, len(sentences) / 20))
        confidence = clamp(0.45 + min(0.25, len(sentences) / 20))
        return SignalPayload(
            value=value,
            confidence=confidence,
            source=["video_transcript"] if sources.video_transcript else ["essay"],
            evidence=sentences[:2],
            reasoning="communication remains understandable and organized across available narrative text.",
        )

    def _structure_signal(self, sources: SourceBundle) -> SignalPayload | None:
        """Estimate explicit text structure from discourse markers."""

        text = sources.video_transcript or sources.essay
        if not text:
            return None

        lowered = text.lower()
        hits = sum(1 for marker in STRUCTURE_MARKERS if marker in lowered)
        sentences = split_sentences(text)
        value = clamp(0.30 + min(0.45, hits * 0.10) + min(0.20, len(sentences) / 25))
        confidence = clamp(0.40 + min(0.25, hits * 0.07) + min(0.15, len(sentences) / 25))
        evidence = self._matching_sentences(text, STRUCTURE_MARKERS, limit=2) or sentences[:2]
        return SignalPayload(
            value=value,
            confidence=confidence,
            source=["video_transcript"] if sources.video_transcript else ["essay"],
            evidence=evidence,
            reasoning="candidate uses ordering or causal markers that improve structure.",
        )

    def _idea_articulation_signal(self, sources: SourceBundle) -> SignalPayload | None:
        """Estimate how clearly the candidate explains examples and reasoning."""

        text = " ".join(part for part in [sources.video_transcript, sources.essay, sources.internal_test_answers] if part)
        if not text:
            return None

        lowered = text.lower()
        hits = sum(1 for marker in IDEA_MARKERS if marker in lowered)
        evidence = self._matching_sentences(text, IDEA_MARKERS, limit=2) or split_sentences(text)[:2]
        value = clamp(0.32 + min(0.48, hits * 0.12) + min(0.12, specificity_score(text) * 0.15))
        confidence = clamp(0.42 + min(0.25, hits * 0.07) + min(0.10, len(evidence) * 0.05))
        return SignalPayload(
            value=value,
            confidence=confidence,
            source=[name for name in ["video_transcript", "essay", "internal_test_answers"] if sources.get(name)],
            evidence=evidence,
            reasoning="candidate articulates examples and causal logic in narrative answers.",
        )

    def _program_alignment_signal(self, sources: SourceBundle) -> SignalPayload | None:
        """Measure alignment between selected program and candidate narrative."""

        if not sources.selected_program:
            return None

        candidate_text = " ".join(
            part
            for part in [sources.essay, sources.project_descriptions, sources.experience_summary, sources.video_transcript]
            if part
        )
        if not candidate_text:
            return None

        program_id = normalize_program_id(sources.selected_program)
        program_definition = get_program_definition(program_id)
        display_name = str(program_definition.get("display_name", sources.selected_program))
        fit_keywords = [str(keyword).lower() for keyword in program_definition.get("fit_keywords", [])]
        overlap = token_overlap_ratio(display_name, candidate_text)
        foundation_bonus = 0.0
        selected_program_lower = display_name.lower()
        candidate_text_lower = candidate_text.lower()
        if any(marker in selected_program_lower for marker in FOUNDATION_PROGRAM_MARKERS):
            foundation_hits = sum(1 for keyword in FOUNDATION_ALIGNMENT_KEYWORDS if keyword in candidate_text_lower)
            foundation_bonus = min(0.18, foundation_hits * 0.03 + specificity_score(candidate_text) * 0.04)
        program_tokens = tokenize(display_name)
        overlap_tokens = sorted(set(program_tokens) & set(tokenize(candidate_text)))
        keyword_hits = sum(1 for keyword in fit_keywords if keyword in candidate_text_lower)
        evidence = split_sentences(candidate_text)[:2]
        if overlap_tokens:
            evidence = [f"Program overlap keywords: {', '.join(overlap_tokens[:6])}"] + evidence[:1]
        elif keyword_hits:
            evidence = [f"Program-fit cues: {', '.join(fit_keywords[:6])}"] + evidence[:1]

        value = clamp(
            0.24
            + overlap * 0.50
            + min(0.18, keyword_hits * 0.04)
            + min(0.15, specificity_score(candidate_text) * 0.15)
            + foundation_bonus
        )
        confidence = clamp(0.45 + overlap * 0.28 + min(0.14, keyword_hits * 0.025) + min(0.10, foundation_bonus * 0.5))
        return SignalPayload(
            value=value,
            confidence=confidence,
            source=[name for name in ["essay", "project_descriptions", "experience_summary", "video_transcript"] if sources.get(name)] + ["selected_program"],
            evidence=evidence[:2],
            reasoning="selected program shares topical overlap and program-specific competency cues with the candidate narrative.",
        )

    def _essay_transcript_consistency_signal(self, sources: SourceBundle) -> SignalPayload | None:
        """Estimate cross-source consistency between essay and transcript."""

        if not sources.essay or not sources.video_transcript:
            return None

        overlap = token_overlap_ratio(sources.essay, sources.video_transcript)
        value = clamp(0.25 + overlap * 0.75)
        confidence = clamp(0.50 + min(0.25, len(tokenize(sources.essay + sources.video_transcript)) / 250))
        evidence = [
            split_sentences(sources.essay)[0] if split_sentences(sources.essay) else sources.essay[:180],
            split_sentences(sources.video_transcript)[0] if split_sentences(sources.video_transcript) else sources.video_transcript[:180],
        ]
        return SignalPayload(
            value=value,
            confidence=confidence,
            source=["essay", "video_transcript"],
            evidence=evidence,
            reasoning="essay and spoken narrative share lexical and thematic overlap.",
        )

    def _claims_evidence_match_signal(self, sources: SourceBundle) -> SignalPayload | None:
        """Estimate whether narrative claims are supported by concrete details."""

        texts = [part for part in [sources.essay, sources.project_descriptions, sources.experience_summary, sources.video_transcript] if part]
        if not texts:
            return None

        specificities = [specificity_score(text) for text in texts]
        value = clamp(0.30 + mean(specificities) * 0.60)
        confidence = clamp(0.45 + min(0.25, len(texts) * 0.06))
        evidence = []
        for text in texts[:2]:
            evidence.extend(split_sentences(text)[:1])
        return SignalPayload(
            value=value,
            confidence=confidence,
            source=[name for name in SOURCE_ORDER if sources.get(name)],
            evidence=evidence[:2],
            reasoning="claims are evaluated against the amount of concrete detail and example density.",
        )

    def _specificity_signal(self, sources: SourceBundle) -> SignalPayload | None:
        """Estimate how specific and example-driven the narrative is."""

        narrative = " ".join(part for part in [sources.essay, sources.project_descriptions, sources.experience_summary, sources.video_transcript] if part)
        if not narrative:
            return None

        value = specificity_score(narrative)
        confidence = clamp(0.45 + min(0.25, len(tokenize(narrative)) / 180))
        return SignalPayload(
            value=value,
            confidence=confidence,
            source=[name for name in SOURCE_ORDER if sources.get(name)],
            evidence=split_sentences(narrative)[:2],
            reasoning="specificity is derived from the amount of concrete, example-based narrative detail.",
        )

    def _voice_consistency_signal(self, sources: SourceBundle) -> SignalPayload | None:
        """Estimate whether written and spoken voice are reasonably aligned."""

        if not sources.essay or not sources.video_transcript:
            return None

        value = voice_consistency_score(sources.essay, sources.video_transcript)
        confidence = authenticity_confidence(sources.essay, sources.video_transcript)
        return SignalPayload(
            value=value,
            confidence=confidence,
            source=["essay", "video_transcript"],
            evidence=[
                split_sentences(sources.essay)[0] if split_sentences(sources.essay) else sources.essay[:180],
                split_sentences(sources.video_transcript)[0] if split_sentences(sources.video_transcript) else sources.video_transcript[:180],
            ],
            reasoning="voice consistency compares lexical and narrative overlap between written and spoken responses.",
        )

    def _ai_writing_risk_signal(self, sources: SourceBundle) -> SignalPayload | None:
        """Estimate advisory AI-writing risk from essay/transcript mismatch and genericity."""

        if not sources.essay:
            return None

        value = ai_writing_risk_score(
            essay_text=sources.essay,
            transcript_text=sources.video_transcript,
            project_text=sources.project_descriptions,
        )
        confidence = authenticity_confidence(sources.essay, sources.video_transcript)
        evidence = split_sentences(sources.essay)[:1]
        if sources.video_transcript:
            evidence.extend(split_sentences(sources.video_transcript)[:1])
        return SignalPayload(
            value=value,
            confidence=confidence,
            source=["essay"] + (["video_transcript"] if sources.video_transcript else []),
            evidence=evidence[:2],
            reasoning="ai-writing risk is advisory and based on genericity, specificity, and voice alignment heuristics.",
        )


# File summary: extractor.py
# Implements a deterministic multilingual baseline extractor for M5 signals.
