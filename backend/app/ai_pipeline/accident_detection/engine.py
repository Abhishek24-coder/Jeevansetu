from app.ai_pipeline.models.pipeline import AccidentDetectionOutput, FeatureVector


class AccidentDetectionEngine:
    IMPACT_FORCE_THRESHOLD = 4.5
    SPEED_DROP_THRESHOLD = 22.0
    GYROSCOPE_SPIKE_THRESHOLD = 4.0

    @classmethod
    def predict(cls, features: FeatureVector) -> AccidentDetectionOutput:
        score = 0.0
        reasons: list[str] = []

        if features.impact_force >= cls.IMPACT_FORCE_THRESHOLD:
            score += 0.45
            reasons.append("high_impact_force")
        if features.speed_drop >= cls.SPEED_DROP_THRESHOLD:
            score += 0.35
            reasons.append("sudden_speed_drop")
        if features.gyroscope_magnitude >= cls.GYROSCOPE_SPIKE_THRESHOLD:
            score += 0.20
            reasons.append("gyroscope_spike")

        if features.impact_force >= 8.0 and features.speed_drop >= 12.0:
            score += 0.10
            reasons.append("severe_impact_with_deceleration")

        confidence = min(score, 0.99)
        return AccidentDetectionOutput(
            accident=confidence >= 0.60,
            confidence=round(confidence, 2),
            reasons=reasons,
        )
