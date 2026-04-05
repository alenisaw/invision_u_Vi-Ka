"""Prompt registry for grouped extraction."""

from .authenticity import PROMPT_HINT as AUTHENTICITY_HINT
from .consistency import PROMPT_HINT as CONSISTENCY_HINT
from .growth import PROMPT_HINT as GROWTH_HINT
from .initiative import PROMPT_HINT as INITIATIVE_HINT
from .leadership import PROMPT_HINT as LEADERSHIP_HINT
from .motivation import PROMPT_HINT as MOTIVATION_HINT

M5_SYSTEM_PROMPT = (
    "You are the Extraction Service for inVision U. "
    "Use only the provided safe Layer 3 text. "
    "Never infer demographic, social, geographic, or protected attributes. "
    "If there is not enough evidence for a signal, omit it. "
    "Return your response as a single json object."
)

M5_GROUP_PROMPT_HINTS = {
    "leadership": LEADERSHIP_HINT,
    "growth": GROWTH_HINT,
    "motivation": MOTIVATION_HINT,
    "initiative": INITIATIVE_HINT,
    "consistency": CONSISTENCY_HINT,
    "authenticity": AUTHENTICITY_HINT,
    "thinking": "Focus on ethical reasoning, civic orientation, and how the candidate justifies decisions.",
    "communication": "Focus on clarity, structure, articulation, and communication maturity rather than style polish.",
    "support": "Capture support context carefully without turning family or social background into a positive score.",
}

__all__ = ["M5_GROUP_PROMPT_HINTS", "M5_SYSTEM_PROMPT"]
