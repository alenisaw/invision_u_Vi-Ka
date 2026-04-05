"""Backend module registry namespace."""

from app.modules.stage_registry import PACKAGE_TO_STAGE, STAGE_REGISTRY, StageDescriptor, get_stage_name

__all__ = [
    "PACKAGE_TO_STAGE",
    "STAGE_REGISTRY",
    "StageDescriptor",
    "get_stage_name",
]
