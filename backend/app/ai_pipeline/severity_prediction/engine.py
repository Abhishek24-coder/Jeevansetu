from app.ai_pipeline.models.pipeline import FeatureVector, SeverityClass, SeverityOutput


class SeverityPredictionEngine:
    @staticmethod
    def predict(features: FeatureVector) -> SeverityOutput:
        score = 0.0
        score += min(features.impact_force / 10.0, 1.0) * 35
        score += min(features.speed_before_crash / 120.0, 1.0) * 20
        score += min(features.speed_drop / 80.0, 1.0) * 20
        score += min(features.orientation_change / 90.0, 1.0) * 15
        score += min(features.response_delay / 15.0, 1.0) * 10

        score_int = max(0, min(round(score), 100))
        if score_int >= 75:
            severity = SeverityClass.CRITICAL
        elif score_int >= 40:
            severity = SeverityClass.MODERATE
        else:
            severity = SeverityClass.MINOR

        return SeverityOutput(severity=severity, score=score_int)
