from __future__ import annotations

from ai.models.schemas import (
    AIResponse,
    AccidentDetectionResponse,
    HospitalRecommendationResponse,
    SeverityPredictionResponse,
)


class AIResponseBuilder:
    """Combines detector, severity, and hospital outputs into backend contract JSON."""

    @staticmethod
    def build(
        incident_id: str,
        detection: AccidentDetectionResponse,
        severity: SeverityPredictionResponse,
        hospital: HospitalRecommendationResponse,
    ) -> AIResponse:
        return AIResponse(
            incident_id=incident_id,
            accident=detection.accident,
            confidence=detection.confidence,
            severity=severity.severity,
            score=severity.score,
            hospital=hospital.hospital_name,
            eta=f"{hospital.eta_minutes} min",
        )

