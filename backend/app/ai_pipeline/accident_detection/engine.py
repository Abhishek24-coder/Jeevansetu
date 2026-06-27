from app.ai_pipeline.models.pipeline import AccidentDetectionOutput, FeatureVector
from ai.accident_detection import AccidentDetector
from ai.models.schemas import FeatureVector as CoreFeatureVector


class AccidentDetectionEngine:
    IMPACT_FORCE_THRESHOLD = 4.5
    SPEED_DROP_THRESHOLD = 22.0
    GYROSCOPE_SPIKE_THRESHOLD = 4.0

    @classmethod
    def predict(cls, features: FeatureVector) -> AccidentDetectionOutput:
        core_output = AccidentDetector().predict(
            CoreFeatureVector(
                acceleration_magnitude=features.acceleration_magnitude,
                gyro_magnitude=features.gyroscope_magnitude,
                speed_drop=features.speed_drop,
                orientation_change=features.orientation_change,
                impact_force=features.impact_force,
                response_delay=features.response_delay,
            )
        )
        return AccidentDetectionOutput(
            accident=core_output.accident,
            confidence=core_output.confidence,
            reasons=core_output.reasons,
        )
