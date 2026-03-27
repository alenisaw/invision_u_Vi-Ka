"""
File: calibration.py
Purpose: Optional post-hoc score calibration for M6.

Notes:
- Keep calibration monotonic and explainable.
- Support a no-op mode so the decision layer can stay explicit.
"""

from __future__ import annotations

from dataclasses import dataclass

try:
    from sklearn.isotonic import IsotonicRegression
except ImportError:  # pragma: no cover
    IsotonicRegression = None


@dataclass
class ScoreCalibrator:
    """Thin wrapper around optional score calibration strategies."""

    mode: str = "none"

    def __post_init__(self) -> None:
        self.model = None
        self.is_fitted = self.mode == "none"
        if self.mode == "isotonic" and IsotonicRegression is not None:
            self.model = IsotonicRegression(out_of_bounds="clip")

    def fit(self, raw_scores: list[float], targets: list[float]) -> None:
        """Fit the selected calibration mode on raw scores and regression targets."""

        if self.mode == "none":
            self.is_fitted = True
            return
        if self.model is None:
            raise RuntimeError(f"calibration mode '{self.mode}' is not available")
        self.model.fit(raw_scores, targets)
        self.is_fitted = True

    def transform(self, score: float) -> float:
        """Transform one raw score using the fitted calibrator."""

        if self.mode == "none" or self.model is None or not self.is_fitted:
            return max(0.0, min(1.0, round(score, 4)))
        calibrated = float(self.model.predict([score])[0])
        return max(0.0, min(1.0, round(calibrated, 4)))


# File summary: calibration.py
# Provides an optional monotonic calibration layer for the M6 score.
