"""
File: evidence.py
Purpose: Evidence selection helpers for M7 explainability output.
"""

from __future__ import annotations

from .schemas import EvidenceItem, ExplainabilityInput, ExplainabilitySignalContext


FACTOR_SIGNAL_MAP = {
    "leadership_potential": ("leadership_indicators", "team_leadership", "leadership_reflection"),
    "growth_trajectory": ("growth_trajectory", "challenges_overcome", "resilience_evidence"),
    "motivation_clarity": ("motivation_clarity", "goal_specificity", "future_goals_alignment"),
    "initiative_agency": ("agency_signals", "self_started_projects", "proactivity_examples"),
    "learning_agility": ("learning_agility", "english_growth"),
    "communication_clarity": ("clarity_score", "structure_score", "idea_articulation"),
    "ethical_reasoning": ("ethical_reasoning", "civic_orientation", "decision_making_style"),
    "program_fit": ("program_alignment",),
}


def collect_factor_evidence(handoff: ExplainabilityInput, factor_name: str, limit: int = 2) -> list[EvidenceItem]:
    """Collect the best available evidence snippets for one factor."""

    evidence_items: list[EvidenceItem] = []
    preferred_signals = FACTOR_SIGNAL_MAP.get(factor_name, ())
    for signal_name in preferred_signals:
        signal = handoff.signal_context.get(signal_name)
        if signal is None:
            continue
        for quote in signal.evidence[:limit]:
            evidence_items.append(EvidenceItem(source=", ".join(signal.source[:2]), quote=quote))
            if len(evidence_items) >= limit:
                return evidence_items

    for signal in handoff.signal_context.values():
        for quote in signal.evidence[:1]:
            evidence_items.append(EvidenceItem(source=", ".join(signal.source[:2]), quote=quote))
            if len(evidence_items) >= limit:
                return evidence_items
    return evidence_items


def collect_factor_signal_contexts(
    handoff: ExplainabilityInput,
    factor_name: str,
    limit: int = 2,
) -> list[tuple[str, ExplainabilitySignalContext]]:
    """Collect the most relevant signal contexts for one factor."""

    contexts: list[tuple[str, ExplainabilitySignalContext]] = []
    preferred_signals = FACTOR_SIGNAL_MAP.get(factor_name, ())
    for signal_name in preferred_signals:
        signal = handoff.signal_context.get(signal_name)
        if signal is None:
            continue
        contexts.append((signal_name, signal))
        if len(contexts) >= limit:
            return contexts
    return contexts

