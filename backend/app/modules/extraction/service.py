"""
File: service.py
Purpose: Public service wrappers for the extraction stage.
"""

from __future__ import annotations

from .signal_extraction_service import GroupedExtractionService


class ExtractionService(GroupedExtractionService):
    """Stage-based public service wrapper for grouped extraction."""


extraction_service = ExtractionService()
