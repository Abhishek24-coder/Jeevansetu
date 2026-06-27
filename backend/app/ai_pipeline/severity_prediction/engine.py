from app.ai_pipeline.models.pipeline import FeatureVector, SeverityClass, SeverityOutput
from ai.models.schemas import FeatureVector as CoreFeatureVector
from ai.severity_prediction import SeverityPredictor


class SeverityPredictionEngine:
    @staticmethod
    def predict(features: FeatureVector) -> SeverityOutput:
        core_output = SeverityPredictor().predict(
            CoreFeatureVector(
                acceleration_magnitude=features.acceleration_magnitude,
                gyro_magnitude=features.gyroscope_magnitude,
                speed_drop=features.speed_drop,
                orientation_change=features.orientation_change,
                impact_force=features.impact_force,
                response_delay=features.response_delay,
            )
        )
        return SeverityOutput(
            severity=SeverityClass(core_output.severity),
            score=core_output.score,
        )
