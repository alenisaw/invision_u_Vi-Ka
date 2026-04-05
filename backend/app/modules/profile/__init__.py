"""Profile stage for assembling the canonical candidate profile."""

from app.modules.profile.assembler import assemble
from app.modules.profile.schemas import CandidateProfile, ModelInput, ProfileMetadata
from app.modules.profile.service import ProfileService

__all__ = [
    "CandidateProfile",
    "ModelInput",
    "ProfileMetadata",
    "ProfileService",
    "assemble",
]
