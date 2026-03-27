"""
File: service.py
Purpose: Backward-compatible public service wrapper for M5 NLP extraction.
"""

from __future__ import annotations

from .signal_extraction_service import GroupedNLPSignalExtractionService


class NLPSignalExtractionService(GroupedNLPSignalExtractionService):
    """Compatibility alias for the grouped M5 extraction service."""


nlp_signal_extraction_service = NLPSignalExtractionService()


# File summary: service.py
# Keeps the legacy import path stable while delegating to the grouped M5 service.
