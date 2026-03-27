"""
File: __init__.py
Purpose: Public exports for the M6 scoring module.
"""

from .schemas import CandidateScore, LabeledEnvelope, SignalEnvelope, SignalPayload
from .service import ScoringService

__all__ = [
    "CandidateScore",
    "LabeledEnvelope",
    "ScoringService",
    "SignalEnvelope",
    "SignalPayload",
]

# File summary: __init__.py
# Re-exports the compact public surface of the scoring module.
