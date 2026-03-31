"""
File: extractor.py
Purpose: Deterministic baseline signal extractor for M5.
"""

from __future__ import annotations

from statistics import mean

from app.modules.m6_scoring.program_policy import get_program_definition, normalize_program_id
from app.modules.m6_scoring.schemas import SignalPayload

from .ai_detector import (
    ai_writing_risk_score,
    authenticity_confidence,
    authenticity_risk_score,
    specificity_score,
    transcript_authenticity_risk_score,
    voice_consistency_score,
)
from .embeddings import clamp, split_sentences, token_overlap_ratio, tokenize
from .schemas import M5ExtractionRequest
from .source_bundle import SourceBundle, build_source_bundle, default_evidence, keyword_signal, matching_snippets


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
    "agency_signals": [
        "started", "built", "created", "founded", "launched", "took initiative", "opened", "set up",
        "organized", "established", "initiated", "formed", "ran", "started a club",
        "created a club", "opened a club", "founded a club", "создал", "основал", "открыл",
        "запустил", "организовал", "инициировал",
    ],
    "self_started_projects": [
        "project", "app", "platform", "club", "startup", "initiative", "community", "makerspace",
        "society", "chapter", "клуб", "кружок", "сообщество", "инициатив",
    ],
    "proactivity_examples": [
        "before asked", "on my own", "proactive", "volunteer", "extra", "noticed a problem",
        "saw a need", "decided to", "took it on", "without being asked", "сам", "сама",
        "по своей инициативе", "решил", "решила",
    ],
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
BEHAVIORAL_CUE_SPECS: dict[str, dict[str, object]] = {
    "leadership_indicators": {
        "source_names": ["video_transcript", "essay", "project_descriptions", "experience_summary"],
        "actions": ["led", "coordinated", "organized", "managed", "mentored", "guided", "delegated", "chaired", "facilitated", "руковод", "координиров", "организ", "настав"],
        "contexts": ["team", "group", "club", "students", "volunteers", "committee", "class", "команд", "групп", "клуб", "ученик", "волонтер"],
        "outcomes": ["resolved", "delivered", "finished", "deadline", "conflict", "improved", "kept", "recruited", "resolved a conflict", "срок", "конфликт", "результат"],
        "self_labels": ["leader", "leadership", "лидер"],
        "reasoning": "Leadership is supported by behavioral evidence showing coordination, guidance, or responsibility for other people and outcomes.",
    },
    "team_leadership": {
        "source_names": ["video_transcript", "essay", "project_descriptions", "experience_summary"],
        "actions": ["coordinated", "delegated", "aligned", "motivated", "mediated", "listened", "resolved", "распредел", "соглас", "мотив", "разреш"],
        "contexts": ["team", "group", "peers", "students", "volunteers", "команд", "групп", "ребят", "ученик"],
        "outcomes": ["conflict", "deadline", "delivery", "together", "finished", "completed", "конфликт", "вместе", "заверш"],
        "self_labels": ["team lead", "captain", "координатор"],
        "reasoning": "Team leadership is supported by evidence of coordinating others, resolving friction, or keeping shared work moving.",
    },
    "growth_trajectory": {
        "source_names": ["video_transcript", "essay", "experience_summary", "project_descriptions"],
        "actions": ["learned", "improved", "adapted", "rebuilt", "practiced", "changed", "refined", "учил", "улучш", "адапт", "пересобр", "исправ"],
        "contexts": ["feedback", "failure", "mistake", "challenge", "new skill", "prototype", "feedback", "ошиб", "сложност", "вызов", "прототип", "навык"],
        "outcomes": ["better", "improved", "more confident", "next version", "results", "better than before", "лучше", "результат", "рост"],
        "self_labels": ["growth", "growing", "развива"],
        "reasoning": "Growth trajectory is supported by evidence of change after feedback, mistakes, or new learning.",
    },
    "challenges_overcome": {
        "source_names": ["video_transcript", "essay", "experience_summary"],
        "actions": ["overcame", "solved", "kept going", "continued", "rebuilt", "fixed", "преодол", "решил", "продолж", "справ"],
        "contexts": ["challenge", "problem", "obstacle", "failure", "difficulty", "setback", "challenge", "проблем", "препятств", "неудач", "трудност"],
        "outcomes": ["finished", "improved", "recovered", "delivered", "completed", "получил", "заверш", "улучш"],
        "self_labels": ["resilient", "persistent", "устойчив"],
        "reasoning": "Challenges overcome is supported by evidence that the candidate faced a difficulty and still moved the work forward.",
    },
    "motivation_clarity": {
        "source_names": ["video_transcript", "essay", "internal_test_answers"],
        "actions": ["want", "aim", "hope", "plan", "intend", "choose", "хочу", "планир", "стремл", "выбира"],
        "contexts": ["because", "so that", "future", "goal", "purpose", "program", "because", "потому", "чтобы", "цель", "будущ", "программ"],
        "outcomes": ["become", "build", "study", "help", "improve", "learn", "стать", "созда", "учить", "помог", "разв"],
        "self_labels": ["motivated", "motivation", "мотивир"],
        "reasoning": "Motivation clarity is supported by a clear chain between intention, reason, and future direction.",
    },
    "goal_specificity": {
        "source_names": ["video_transcript", "essay", "selected_program"],
        "actions": ["plan", "step", "roadmap", "apply", "prepare", "build", "план", "шаг", "дорожн", "готов"],
        "contexts": ["specific", "milestone", "next year", "next step", "program", "bachelor", "specific", "конкрет", "этап", "следующ", "бакалав"],
        "outcomes": ["internship", "portfolio", "startup", "research", "prototype", "стажир", "портфол", "стартап", "исслед", "прототип"],
        "self_labels": ["goal", "goals", "цель"],
        "reasoning": "Goal specificity is supported by concrete next steps, milestones, or tangible future outcomes.",
    },
    "agency_signals": {
        "source_names": ["video_transcript", "project_descriptions", "essay", "experience_summary"],
        "actions": ["started", "opened", "set up", "created", "founded", "launched", "organized", "established", "initiated", "formed", "ran", "создал", "открыл", "запуст", "организ", "основал", "инициир"],
        "contexts": ["project", "club", "app", "community", "makerspace", "program", "event", "platform", "project", "клуб", "кружок", "сообщество", "проект", "мероприят"],
        "outcomes": ["members", "users", "weekly", "sessions", "participants", "used by", "grew", "joined", "участник", "пользоват", "заняти", "встреч", "рост"],
        "self_labels": ["initiative", "initiated", "инициатив"],
        "reasoning": "Initiative is supported by self-started actions, not just self-description, especially when they produced a concrete activity or artifact.",
    },
    "self_started_projects": {
        "source_names": ["video_transcript", "project_descriptions", "essay", "experience_summary"],
        "actions": ["built", "created", "founded", "opened", "designed", "launched", "developed", "собрал", "создал", "основал", "открыл", "разработ"],
        "contexts": ["project", "app", "platform", "club", "community", "makerspace", "tool", "initiative", "проект", "приложен", "клуб", "сообщество", "кружок"],
        "outcomes": ["users", "members", "prototype", "workshop", "events", "adoption", "пользоват", "участник", "прототип", "воркшоп", "мероприят"],
        "self_labels": ["project", "initiative", "инициатив"],
        "reasoning": "Self-started projects are supported when the candidate describes creating and sustaining a concrete activity, product, or group.",
    },
    "proactivity_examples": {
        "source_names": ["video_transcript", "essay", "experience_summary", "project_descriptions"],
        "actions": ["noticed", "decided", "took it on", "without being asked", "solved", "volunteered", "увидел", "заметил", "решил", "взял", "сама", "сам"],
        "contexts": ["problem", "need", "gap", "issue", "deadline", "challenge", "problem", "проблем", "нужд", "пробел", "срок", "вызов"],
        "outcomes": ["fixed", "helped", "organized", "improved", "supported", "resolved", "исправ", "помог", "организ", "улучш", "решил"],
        "self_labels": ["proactive", "initiative", "проактив"],
        "reasoning": "Proactivity is supported when the candidate acts before external prompting and ties that action to a visible need or result.",
    },
    "learning_agility": {
        "source_names": ["video_transcript", "essay", "internal_test_answers", "experience_summary"],
        "actions": ["learned", "taught myself", "practiced", "adapted", "experimented", "iterated", "учил", "самоуч", "практиков", "адапт", "эксперимент", "итерац"],
        "contexts": ["feedback", "new tool", "new skill", "language", "prototype", "mistake", "feedback", "нов", "язык", "навык", "ошиб", "инструмент"],
        "outcomes": ["improved", "faster", "better", "confident", "next version", "improved results", "улучш", "лучше", "уверен", "результат"],
        "self_labels": ["quick learner", "curious", "любозн"],
        "reasoning": "Learning agility is supported by evidence that the candidate learns, adapts, and applies lessons in practice.",
    },
    "ethical_reasoning": {
        "source_names": ["internal_test_answers", "essay", "video_transcript"],
        "actions": ["considered", "chose", "balanced", "protected", "respected", "учел", "выбрал", "сбаланс", "уваж"],
        "contexts": ["fair", "responsible", "honest", "tradeoff", "people", "community", "fair", "справед", "ответствен", "честн", "людей", "сообществ"],
        "outcomes": ["safe", "inclusive", "fairer", "responsible decision", "безопас", "инклюз", "справедлив"],
        "self_labels": ["ethical", "responsible", "этич", "ответствен"],
        "reasoning": "Ethical reasoning is supported when the candidate explains how fairness, responsibility, or tradeoffs shaped a decision.",
    },
    "civic_orientation": {
        "source_names": ["experience_summary", "essay", "video_transcript"],
        "actions": ["helped", "volunteered", "mentored", "supported", "organized", "помог", "волонтер", "поддерж", "организ"],
        "contexts": ["community", "school", "students", "region", "social", "people", "сообществ", "школ", "ученик", "регион", "людей"],
        "outcomes": ["benefit", "access", "inclusion", "support", "impact", "польз", "доступ", "инклюз", "вклад"],
        "self_labels": ["community", "social impact", "социаль"],
        "reasoning": "Civic orientation is supported by evidence of helping communities, widening access, or solving problems for others.",
    },
}


class HeuristicSignalExtractor:
    """Deterministic baseline extractor that keeps M5 -> M6 available without LLM access."""

    def extract(self, request: M5ExtractionRequest, transcript_text: str | None = None) -> dict[str, SignalPayload]:
        sources = build_source_bundle(request, transcript_text=transcript_text)
        signals = self._extract_keyword_signals(sources)
        self._apply_behavioral_cue_overrides(signals, sources)
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

    def _apply_behavioral_cue_overrides(
        self,
        signals: dict[str, SignalPayload],
        sources: SourceBundle,
    ) -> None:
        for signal_name, spec in BEHAVIORAL_CUE_SPECS.items():
            cue_payload = self._behavioral_cue_signal(
                sources=sources,
                source_names=spec["source_names"],
                action_markers=spec["actions"],
                context_markers=spec["contexts"],
                outcome_markers=spec["outcomes"],
                self_label_markers=spec["self_labels"],
                reasoning=str(spec["reasoning"]),
            )
            if cue_payload is None:
                continue
            existing_payload = signals.get(signal_name)
            signals[signal_name] = (
                cue_payload
                if existing_payload is None
                else self._merge_signal_payloads(existing_payload, cue_payload)
            )

    def _behavioral_cue_signal(
        self,
        *,
        sources: SourceBundle,
        source_names: list[str],
        action_markers: list[str],
        context_markers: list[str],
        outcome_markers: list[str],
        self_label_markers: list[str],
        reasoning: str,
    ) -> SignalPayload | None:
        source_hits: list[str] = []
        evidence: list[str] = []
        cue_scores: list[float] = []
        direct_hit_count = 0
        indirect_hit_count = 0

        for source_name in source_names:
            text = sources.get(source_name)
            if not text:
                continue
            for sentence in split_sentences(text):
                lowered = sentence.lower()
                action_hit = any(marker in lowered for marker in action_markers)
                context_hit = any(marker in lowered for marker in context_markers)
                outcome_hit = any(marker in lowered for marker in outcome_markers)
                self_label_hit = any(marker in lowered for marker in self_label_markers)
                if not (action_hit or outcome_hit or self_label_hit):
                    continue

                direct_evidence = action_hit and (context_hit or outcome_hit)
                indirect_evidence = (
                    (action_hit and self_label_hit)
                    or (outcome_hit and context_hit)
                    or (action_hit and specificity_score(sentence) >= 0.50)
                )
                if not direct_evidence and not indirect_evidence and not self_label_hit:
                    continue

                score = (
                    0.18
                    + (0.22 if action_hit else 0.0)
                    + (0.16 if context_hit else 0.0)
                    + (0.15 if outcome_hit else 0.0)
                    + (0.05 if self_label_hit else 0.0)
                    + (0.12 if direct_evidence else 0.0)
                    + (0.06 if indirect_evidence and not direct_evidence else 0.0)
                    + min(0.12, specificity_score(sentence) * 0.18)
                )
                cue_scores.append(score)
                if direct_evidence:
                    direct_hit_count += 1
                elif indirect_evidence:
                    indirect_hit_count += 1
                if source_name not in source_hits:
                    source_hits.append(source_name)
                if len(evidence) < 2:
                    cue_label = "direct cue" if direct_evidence else "indirect cue"
                    evidence.append(f"[{cue_label}] {sentence[:200]}")

        if not cue_scores:
            return None

        source_diversity_bonus = min(0.10, len(source_hits) * 0.03)
        cross_source_bonus = 0.08 if len(source_hits) >= 2 else 0.0
        evidence_count_bonus = min(0.06, len(evidence) * 0.03)
        value = clamp(
            0.18
            + min(0.46, mean(sorted(cue_scores, reverse=True)[:2]) * 0.60)
            + source_diversity_bonus
            + cross_source_bonus
            + evidence_count_bonus
        )
        confidence = clamp(
            0.42
            + min(0.20, direct_hit_count * 0.06)
            + min(0.10, indirect_hit_count * 0.04)
            + source_diversity_bonus
            + min(0.08, len(evidence) * 0.04)
        )
        reasoning_prefix = (
            "Supported by direct behavioral evidence. "
            if direct_hit_count
            else "Supported by indirect behavioral evidence. "
        )
        return SignalPayload(
            value=value,
            confidence=confidence,
            source=source_hits,
            evidence=evidence[:2],
            reasoning=reasoning_prefix + reasoning,
        )

    def _merge_signal_payloads(self, existing: SignalPayload, cue_payload: SignalPayload) -> SignalPayload:
        merged_sources = list(dict.fromkeys(existing.source + cue_payload.source))
        merged_evidence = list(dict.fromkeys(existing.evidence + cue_payload.evidence))[:2]
        if cue_payload.value >= existing.value:
            reasoning = cue_payload.reasoning
            value = cue_payload.value
        else:
            reasoning = existing.reasoning
            value = clamp(max(existing.value, (existing.value * 0.6) + (cue_payload.value * 0.4)))
        return SignalPayload(
            value=value,
            confidence=max(existing.confidence, cue_payload.confidence),
            source=merged_sources,
            evidence=merged_evidence,
            reasoning=reasoning,
        )

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
            ("authenticity_risk", self._authenticity_risk_signal),
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
            ("agency_signals", ["video_transcript", "project_descriptions", "essay", "experience_summary"]),
            ("self_started_projects", ["video_transcript", "project_descriptions", "essay", "experience_summary"]),
            ("proactivity_examples", ["video_transcript", "essay", "experience_summary", "project_descriptions"]),
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

    def _authenticity_risk_signal(self, sources: SourceBundle) -> SignalPayload | None:
        primary_text = sources.essay or sources.video_transcript
        supporting_text = sources.video_transcript if sources.essay else sources.essay
        if not primary_text:
            return None

        evidence = default_evidence(
            sources,
            ["essay", "video_transcript", "project_descriptions"],
        )
        if sources.essay:
            value = authenticity_risk_score(
                primary_text=sources.essay,
                supporting_text=sources.video_transcript,
                project_text=sources.project_descriptions,
            )
            source = ["essay"] + (["video_transcript"] if sources.video_transcript else [])
            reasoning = "authenticity risk is advisory and combines essay genericity, cross-source alignment, and supporting detail."
        else:
            value = transcript_authenticity_risk_score(
                transcript_text=sources.video_transcript,
                essay_text=sources.essay,
                project_text=sources.project_descriptions,
            )
            source = ["video_transcript"] + (["project_descriptions"] if sources.project_descriptions else [])
            reasoning = "authenticity risk is advisory and combines spoken genericity, supporting detail, and consistency with other safe sources."

        return SignalPayload(
            value=value,
            confidence=authenticity_confidence(sources.essay, sources.video_transcript),
            source=source,
            evidence=evidence[:2],
            reasoning=reasoning,
        )


