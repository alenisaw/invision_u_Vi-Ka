"""
File: ml_model.py
Purpose: Compact ML refinement layer for M6 scoring.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import numpy as np

from .confidence import calculate_mean_signal_confidence, calculate_signal_coverage
from .io_utils import ensure_trusted_artifact_path
from .program_policy import normalize_program_id
from .rules import MODIFIER_SIGNAL_NAMES, get_scoring_signal_names, get_signal_confidence, get_signal_value
from .schemas import LabeledEnvelope, SignalEnvelope
from .m6_scoring_config import PROGRAM_CATALOG

try:
    import joblib
    from sklearn.ensemble import GradientBoostingRegressor
except ImportError:  # pragma: no cover
    joblib = None
    GradientBoostingRegressor = None


def build_feature_names() -> list[str]:
    """Lock the feature vector layout so training and inference stay aligned."""

    feature_names = [
        "baseline_rpi",
        "completeness",
        "mean_signal_confidence",
        "signal_coverage",
    ]
    feature_names.extend(
        [
            "leadership_potential",
            "growth_trajectory",
            "motivation_clarity",
            "initiative_agency",
            "learning_agility",
            "communication_clarity",
            "ethical_reasoning",
            "program_fit",
        ]
    )
    for program_id in sorted(PROGRAM_CATALOG):
        feature_names.append(f"program__{program_id}")

    for signal_name in sorted(get_scoring_signal_names() | MODIFIER_SIGNAL_NAMES):
        feature_names.append(f"{signal_name}__value")
        feature_names.append(f"{signal_name}__confidence")

    return feature_names


def build_feature_vector(envelope: SignalEnvelope, sub_scores: dict[str, float], baseline_rpi: float) -> np.ndarray:
    """Convert one envelope into a stable numeric vector."""

    feature_values: dict[str, float] = {
        "baseline_rpi": baseline_rpi,
        "completeness": envelope.completeness,
        "mean_signal_confidence": calculate_mean_signal_confidence(envelope),
        "signal_coverage": calculate_signal_coverage(envelope),
    }
    feature_values.update(sub_scores)
    active_program_id = normalize_program_id(envelope.program_id or envelope.selected_program)
    for program_id in sorted(PROGRAM_CATALOG):
        feature_values[f"program__{program_id}"] = 1.0 if active_program_id == program_id else 0.0

    for signal_name in sorted(get_scoring_signal_names() | MODIFIER_SIGNAL_NAMES):
        feature_values[f"{signal_name}__value"] = get_signal_value(envelope, signal_name, 0.0) or 0.0
        feature_values[f"{signal_name}__confidence"] = get_signal_confidence(envelope, signal_name, 0.0) or 0.0

    ordered_values = [feature_values[name] for name in build_feature_names()]
    return np.asarray(ordered_values, dtype=float)


class HybridScoringModel:
    """Thin wrapper around the regression model used by M6."""

    def __init__(self, model_family: str = "gbr") -> None:
        self.feature_names = build_feature_names()
        self.model_family = model_family
        self.model = self._build_model(model_family)
        self.is_trained = False

    def _build_model(self, model_family: str):
        """Create the configured regression model."""

        if model_family == "gbr":
            return GradientBoostingRegressor(random_state=42) if GradientBoostingRegressor else None
        raise ValueError(f"unsupported model_family: {model_family}")

    def fit(self, labeled_samples: Iterable[LabeledEnvelope], feature_builder) -> None:
        """Train the model on labeled envelopes."""

        if self.model is None:
            raise RuntimeError(f"{self.model_family} dependencies are not available in the current environment")

        sample_list = list(labeled_samples)
        if not sample_list:
            raise ValueError("labeled_samples must not be empty")

        feature_rows = []
        targets = []
        for labeled_sample in sample_list:
            sub_scores, baseline_rpi = feature_builder(labeled_sample.envelope)
            feature_rows.append(build_feature_vector(labeled_sample.envelope, sub_scores, baseline_rpi))
            targets.append(labeled_sample.target_rpi)

        self.model.fit(np.vstack(feature_rows), np.asarray(targets, dtype=float))
        self.is_trained = True

    def predict(self, envelope: SignalEnvelope, sub_scores: dict[str, float], baseline_rpi: float) -> float:
        """Predict a refinement score; fall back to the baseline if not trained."""

        if self.model is None or not self.is_trained:
            return baseline_rpi

        feature_vector = build_feature_vector(envelope, sub_scores, baseline_rpi).reshape(1, -1)
        prediction = float(self.model.predict(feature_vector)[0])
        return max(0.0, min(1.0, round(prediction, 4)))

    def save(self, path: str | Path) -> None:
        """Persist the trained model and feature layout."""

        if joblib is None:
            raise RuntimeError("joblib is not available in the current environment")
        if not self.is_trained:
            raise RuntimeError("cannot save an untrained model")
        artifact_path = ensure_trusted_artifact_path(path)
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path = artifact_path.with_suffix(f"{artifact_path.suffix}.meta.json")

        joblib.dump(
            {
                "model": self.model,
                "feature_names": self.feature_names,
                "model_family": self.model_family,
            },
            artifact_path,
        )
        metadata_path.write_text(
            json.dumps(
                {
                    "artifact_type": "m6_scoring_model",
                    "model_family": self.model_family,
                    "feature_count": len(self.feature_names),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: str | Path) -> "HybridScoringModel":
        """Load a previously trained scoring model."""

        if joblib is None:
            raise RuntimeError("joblib is not available in the current environment")
        artifact_path = ensure_trusted_artifact_path(path)
        if artifact_path.suffix != ".joblib":
            raise ValueError("model artifact must use the .joblib suffix")
        metadata_path = artifact_path.with_suffix(f"{artifact_path.suffix}.meta.json")
        if not metadata_path.exists():
            raise RuntimeError(f"model metadata is missing for artifact: {artifact_path}")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("artifact_type") != "m6_scoring_model":
            raise RuntimeError(f"invalid model artifact metadata: {metadata_path}")

        payload = joblib.load(artifact_path)
        if not isinstance(payload, dict) or "model" not in payload or "feature_names" not in payload:
            raise RuntimeError(f"invalid M6 model artifact payload: {artifact_path}")
        model_family = payload.get("model_family", "gbr")
        if metadata.get("model_family") != model_family:
            raise RuntimeError(f"model metadata mismatch for artifact: {artifact_path}")
        loaded = cls(model_family=model_family)
        loaded.model = payload["model"]
        loaded.feature_names = list(payload["feature_names"])
        if metadata.get("feature_count") != len(loaded.feature_names):
            raise RuntimeError(f"feature layout metadata mismatch for artifact: {artifact_path}")
        loaded.is_trained = True
        return loaded


# File summary: ml_model.py
# Implements a compact GBR refinement layer with safe baseline fallback.
