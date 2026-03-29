"""
File: m6_scoring_config.py
Purpose: Typed loader for the YAML-based M6 scoring config.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass(frozen=True)
class DecisionThresholds:
    """Explicit class boundaries for calibrated scores."""

    strong_recommend_min: float
    recommend_min: float
    waitlist_min: float
    declined_completeness_max: float


@dataclass(frozen=True)
class ConfidenceBands:
    """UI-facing confidence bands."""

    high_min: float
    medium_min: float


@dataclass(frozen=True)
class UncertaintyPolicy:
    """Interpretable uncertainty routing thresholds."""

    hard_flags: tuple[str, ...]
    declined_manual_review_score_min: float
    low_confidence_max: float
    low_signal_confidence_max: float
    low_coverage_max: float
    low_quality_completeness_max: float
    disagreement_max: float
    soft_caution_min: int
    narrow_margin_max: float
    instability_radius_base: float
    instability_confidence_weight: float
    instability_disagreement_weight: float
    instability_low_quality_weight: float
    manual_review_trigger_count: int
    uncertainty_flag_trigger_count: int


@dataclass(frozen=True)
class DecisionPolicyConfig:
    """Full decision-layer policy config."""

    scoring_version: str
    blend_weight_ml: float
    model_family: str
    calibration_mode: str
    supported_signal_schema_versions: tuple[str, ...]
    default_program_id: str
    trusted_model_artifact_dirs: tuple[str, ...]
    trusted_report_dirs: tuple[str, ...]
    status_order: tuple[str, ...]
    thresholds: DecisionThresholds
    confidence_bands: ConfidenceBands
    uncertainty_policy: UncertaintyPolicy
    confidence_rules: dict[str, float]
    confidence_weights: dict[str, float]
    shortlist_eligible_statuses: set[str] = field(default_factory=set)
    modifier_signal_names: set[str] = field(default_factory=set)
    critical_data_flags: set[str] = field(default_factory=set)
    soft_caution_flags: set[str] = field(default_factory=set)
    subscore_signal_weights: dict[str, dict[str, float]] = field(default_factory=dict)
    scoring_weights: dict[str, float] = field(default_factory=dict)
    program_catalog: dict[str, dict[str, str | list[str]]] = field(default_factory=dict)
    program_weight_profiles: dict[str, dict[str, float]] = field(default_factory=dict)
    status_summary_templates: dict[str, str] = field(default_factory=dict)


def _load_yaml() -> dict:
    """Load the colocated YAML config file."""

    config_path = Path(__file__).with_name("m6_scoring_config.yaml")
    try:
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:  # pragma: no cover
        raise RuntimeError(f"M6 config file is missing: {config_path}") from exc
    except yaml.YAMLError as exc:  # pragma: no cover
        raise RuntimeError(f"M6 config file is invalid YAML: {config_path}") from exc

    if not isinstance(payload, dict):
        raise RuntimeError(f"M6 config file must contain a mapping object: {config_path}")
    return payload


def _merge(base: dict, overrides: dict) -> dict:
    """Merge a shallow nested override dict into the base config."""

    merged = dict(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            nested = dict(merged[key])
            nested.update(value)
            merged[key] = nested
        else:
            merged[key] = value
    return merged


def build_policy_config(overrides: dict | None = None) -> DecisionPolicyConfig:
    """Build a typed policy config from YAML plus optional overrides."""

    raw = _load_yaml()
    if overrides:
        raw = _merge(raw, overrides)

    return DecisionPolicyConfig(
        scoring_version=raw["scoring_version"],
        blend_weight_ml=raw["default_blend_weight_ml"],
        model_family=raw["default_model_family"],
        calibration_mode=raw["default_calibration_mode"],
        supported_signal_schema_versions=tuple(raw.get("supported_signal_schema_versions", ["v1"])),
        default_program_id=raw.get("default_program_id", "digital_products_and_services"),
        trusted_model_artifact_dirs=tuple(raw.get("trusted_model_artifact_dirs", ())),
        trusted_report_dirs=tuple(raw.get("trusted_report_dirs", ())),
        status_order=tuple(raw["status_order"]),
        thresholds=DecisionThresholds(**raw["status_thresholds"]),
        confidence_bands=ConfidenceBands(**raw["confidence_band_thresholds"]),
        uncertainty_policy=UncertaintyPolicy(
            hard_flags=tuple(raw["uncertainty_policy"]["hard_flags"]),
            declined_manual_review_score_min=raw["uncertainty_policy"]["declined_manual_review_score_min"],
            low_confidence_max=raw["uncertainty_policy"]["low_confidence_max"],
            low_signal_confidence_max=raw["uncertainty_policy"]["low_signal_confidence_max"],
            low_coverage_max=raw["uncertainty_policy"]["low_coverage_max"],
            low_quality_completeness_max=raw["uncertainty_policy"]["low_quality_completeness_max"],
            disagreement_max=raw["uncertainty_policy"]["disagreement_max"],
            soft_caution_min=raw["uncertainty_policy"]["soft_caution_min"],
            narrow_margin_max=raw["uncertainty_policy"]["narrow_margin_max"],
            instability_radius_base=raw["uncertainty_policy"]["instability_radius_base"],
            instability_confidence_weight=raw["uncertainty_policy"]["instability_confidence_weight"],
            instability_disagreement_weight=raw["uncertainty_policy"]["instability_disagreement_weight"],
            instability_low_quality_weight=raw["uncertainty_policy"]["instability_low_quality_weight"],
            manual_review_trigger_count=raw["uncertainty_policy"]["manual_review_trigger_count"],
            uncertainty_flag_trigger_count=raw["uncertainty_policy"].get(
                "uncertainty_flag_trigger_count",
                raw["uncertainty_policy"]["manual_review_trigger_count"],
            ),
        ),
        confidence_rules=dict(raw["confidence_rules"]),
        confidence_weights=dict(raw["confidence_weights"]),
        shortlist_eligible_statuses=set(raw["shortlist_eligible_statuses"]),
        modifier_signal_names=set(raw["modifier_signal_names"]),
        critical_data_flags=set(raw["critical_data_flags"]),
        soft_caution_flags=set(raw["soft_caution_flags"]),
        subscore_signal_weights=dict(raw["subscore_signal_weights"]),
        scoring_weights=dict(raw["scoring_weights"]),
        program_catalog=dict(raw.get("program_catalog", {})),
        program_weight_profiles=dict(raw.get("program_weight_profiles", {})),
        status_summary_templates=dict(raw["status_summary_templates"]),
    )


DEFAULT_POLICY_CONFIG = build_policy_config()

SCORING_VERSION = DEFAULT_POLICY_CONFIG.scoring_version
DEFAULT_BLEND_WEIGHT_ML = DEFAULT_POLICY_CONFIG.blend_weight_ml
DEFAULT_MODEL_FAMILY = DEFAULT_POLICY_CONFIG.model_family
DEFAULT_CALIBRATION_MODE = DEFAULT_POLICY_CONFIG.calibration_mode
SUPPORTED_SIGNAL_SCHEMA_VERSIONS = DEFAULT_POLICY_CONFIG.supported_signal_schema_versions
DEFAULT_PROGRAM_ID = DEFAULT_POLICY_CONFIG.default_program_id
TRUSTED_MODEL_ARTIFACT_DIRS = DEFAULT_POLICY_CONFIG.trusted_model_artifact_dirs
TRUSTED_REPORT_DIRS = DEFAULT_POLICY_CONFIG.trusted_report_dirs
SUBSCORE_SIGNAL_WEIGHTS = DEFAULT_POLICY_CONFIG.subscore_signal_weights
SCORING_WEIGHTS = DEFAULT_POLICY_CONFIG.scoring_weights
PROGRAM_CATALOG = DEFAULT_POLICY_CONFIG.program_catalog
PROGRAM_WEIGHT_PROFILES = DEFAULT_POLICY_CONFIG.program_weight_profiles
STATUS_ORDER = DEFAULT_POLICY_CONFIG.status_order
STATUS_THRESHOLDS = {
    "strong_recommend_min": DEFAULT_POLICY_CONFIG.thresholds.strong_recommend_min,
    "recommend_min": DEFAULT_POLICY_CONFIG.thresholds.recommend_min,
    "waitlist_min": DEFAULT_POLICY_CONFIG.thresholds.waitlist_min,
    "declined_completeness_max": DEFAULT_POLICY_CONFIG.thresholds.declined_completeness_max,
}
CONFIDENCE_BAND_THRESHOLDS = {
    "high_min": DEFAULT_POLICY_CONFIG.confidence_bands.high_min,
    "medium_min": DEFAULT_POLICY_CONFIG.confidence_bands.medium_min,
}
CONFIDENCE_RULES = DEFAULT_POLICY_CONFIG.confidence_rules
CONFIDENCE_WEIGHTS = DEFAULT_POLICY_CONFIG.confidence_weights
SHORTLIST_ELIGIBLE_STATUSES = DEFAULT_POLICY_CONFIG.shortlist_eligible_statuses
MODIFIER_SIGNAL_NAMES = DEFAULT_POLICY_CONFIG.modifier_signal_names
CRITICAL_DATA_FLAGS = DEFAULT_POLICY_CONFIG.critical_data_flags
SOFT_CAUTION_FLAGS = DEFAULT_POLICY_CONFIG.soft_caution_flags
STATUS_SUMMARY_TEMPLATES = DEFAULT_POLICY_CONFIG.status_summary_templates


# File summary: m6_scoring_config.py
# Loads the YAML config and exposes typed/default decision policy settings.
