from __future__ import annotations

from ai.configs.settings import SEVERITY_WEIGHTS, SeverityWeights
from ai.models.schemas import FeatureVector, SeverityPredictionRequest, SeverityPredictionResponse


class SeverityPredictor:
    """Converts crash features into a 0-100 emergency risk score."""

    def __init__(self, weights: SeverityWeights = SEVERITY_WEIGHTS) -> None:
        self.weights = weights

    def predict(self, data: FeatureVector | SeverityPredictionRequest) -> SeverityPredictionResponse:
        score = self.score(data)
        if score <= 30:
            severity = "minor"
        elif score <= 70:
            severity = "moderate"
        else:
            severity = "critical"
        return SeverityPredictionResponse(severity=severity, score=score)

    def score(self, data: FeatureVector | SeverityPredictionRequest) -> int:
        impact_component = self._normalize(data.impact_force, 0, 10) * self.weights.impact_force
        speed_component = self._normalize(data.speed_drop, 0, 70) * self.weights.speed_drop
        orientation_component = self._normalize(data.orientation_change, 0, 55) * self.weights.orientation_change
        delay_component = self._normalize(data.response_delay, 0, 16) * self.weights.response_delay
        return round((impact_component + speed_component + orientation_component + delay_component) * 100)

    @staticmethod
    def _normalize(value: float, minimum: float, maximum: float) -> float:
        if maximum <= minimum:
            raise ValueError("maximum must be greater than minimum")
        return max(0.0, min((value - minimum) / (maximum - minimum), 1.0))
