from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd

from ai.configs.settings import ACCIDENT_THRESHOLDS, AccidentThresholds
from ai.models.schemas import AccidentDetectionResponse, FeatureVector


class AccidentDetector:
    """Rule-based v1 detector with an ML-ready prediction boundary."""

    def __init__(
        self,
        thresholds: AccidentThresholds = ACCIDENT_THRESHOLDS,
        model_path: Path | None = None,
        use_model: bool = True,
    ) -> None:
        self.thresholds = thresholds
        self.model_path = model_path or Path(__file__).resolve().parents[1] / "models" / "best_accident_detector.joblib"
        self.model = self._load_model() if use_model else None

    def predict(self, features: FeatureVector) -> AccidentDetectionResponse:
        checks = {
            "high_acceleration_magnitude": features.acceleration_magnitude >= self.thresholds.acceleration_magnitude_g,
            "sudden_speed_drop": features.speed_drop >= self.thresholds.speed_drop_kmph,
            "gyro_spike": features.gyro_magnitude >= self.thresholds.gyro_magnitude_dps,
            "orientation_change": features.orientation_change >= self.thresholds.orientation_change_deg,
        }
        reasons = [name for name, passed in checks.items() if passed]

        accident = checks["high_acceleration_magnitude"] and (
            checks["sudden_speed_drop"] or checks["gyro_spike"] or checks["orientation_change"]
        )
        confidence = self._confidence(features, checks)
        if self.model is not None:
            model_accident, model_confidence = self._predict_with_model(features)
            accident = accident or model_accident
            confidence = max(confidence, model_confidence)
            if model_accident:
                reasons.append("ml_model_positive")

        return AccidentDetectionResponse(
            accident=accident,
            confidence=round(confidence, 2),
            reasons=reasons,
        )

    def _confidence(self, features: FeatureVector, checks: dict[str, bool]) -> float:
        score = 0.07
        if checks["high_acceleration_magnitude"]:
            score += min(features.acceleration_magnitude / 10.0, 1.0) * 0.40
        if checks["sudden_speed_drop"]:
            score += min(features.speed_drop / 70.0, 1.0) * 0.30
        if checks["gyro_spike"]:
            score += min(features.gyro_magnitude / 5.0, 1.0) * 0.20
        if checks["orientation_change"]:
            score += min(features.orientation_change / 60.0, 1.0) * 0.05
        return max(0.05, min(score, 0.99))

    def _load_model(self):
        if not self.model_path.exists():
            return None
        return joblib.load(self.model_path)

    def _predict_with_model(self, features: FeatureVector) -> tuple[bool, float]:
        frame = pd.DataFrame(
            [
                {
                    "acceleration_magnitude": features.acceleration_magnitude,
                    "gyro_magnitude": features.gyro_magnitude,
                    "speed_drop": features.speed_drop,
                    "orientation_change": features.orientation_change,
                    "impact_force": features.impact_force,
                    "response_delay": features.response_delay,
                }
            ]
        )
        prediction = int(self.model.predict(frame)[0])
        if hasattr(self.model, "predict_proba"):
            probability = float(self.model.predict_proba(frame)[0][1])
        else:
            probability = 0.75 if prediction == 1 else 0.25
        return prediction == 1, max(0.05, min(probability, 0.99))
