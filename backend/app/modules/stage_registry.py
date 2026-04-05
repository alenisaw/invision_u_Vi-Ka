"""Public stage naming registry for the current admissions runtime."""

from dataclasses import dataclass


@dataclass(frozen=True)
class StageDescriptor:
    package: str
    public_name: str
    category: str


STAGE_REGISTRY: tuple[StageDescriptor, ...] = (
    StageDescriptor("gateway", "Gateway", "runtime"),
    StageDescriptor("intake", "Input Intake", "input"),
    StageDescriptor("asr", "ASR", "runtime"),
    StageDescriptor("privacy", "Privacy", "runtime"),
    StageDescriptor("profile", "Profile", "runtime"),
    StageDescriptor("extraction", "Extraction", "runtime"),
    StageDescriptor("extraction.ai_detector", "AI Detect", "supplementary"),
    StageDescriptor("scoring", "Scoring", "runtime"),
    StageDescriptor("explanation", "Explanation", "runtime"),
    StageDescriptor("workspace", "Review Workspace", "review"),
    StageDescriptor("review", "Review Audit", "review"),
    StageDescriptor("storage", "Storage", "infrastructure"),
    StageDescriptor("demo", "Demo Layer", "supporting"),
)


PACKAGE_TO_STAGE = {item.package: item for item in STAGE_REGISTRY}


def get_stage_name(package: str) -> str:
    """Return the public stage name for an internal package or submodule."""
    descriptor = PACKAGE_TO_STAGE.get(package)
    if descriptor is not None:
        return descriptor.public_name

    head = package.split(".", 1)[0]
    descriptor = PACKAGE_TO_STAGE.get(head)
    return descriptor.public_name if descriptor is not None else package
