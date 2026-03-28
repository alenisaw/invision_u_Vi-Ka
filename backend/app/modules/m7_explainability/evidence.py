"""
File: evidence.py
Purpose: Evidence selection helpers for M7 explainability output.
"""

from __future__ import annotations

from .schemas import EvidenceItem, ExplainabilityInput


def collect_factor_evidence(handoff: ExplainabilityInput, factor_name: str, limit: int = 2) -> list[EvidenceItem]:
    """Collect the best available evidence snippets for one factor."""

    evidence_items: list[EvidenceItem] = []
    for signal_name, signal in handoff.signal_context.items():
        if signal_name == factor_name or factor_name in signal_name:
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


# File summary: evidence.py
# Pulls short, source-backed evidence snippets from the M6 handoff payload.
