from app.ai_pipeline.models.pipeline import (
    AccidentDetectionOutput,
    AIPipelineResponse,
    EmergencyIntegrationResult,
    FeatureVector,
    HospitalRecommendation,
    SeverityOutput,
    UserVerificationRequest,
)


class AIResponseBuilder:
    @staticmethod
    def build(
        incident_id: str,
        detection: AccidentDetectionOutput,
        features: FeatureVector,
        severity: SeverityOutput | None = None,
        hospital: HospitalRecommendation | None = None,
        verification: UserVerificationRequest | None = None,
        integration: EmergencyIntegrationResult | None = None,
    ) -> AIPipelineResponse:
        return AIPipelineResponse(
            incident_id=incident_id,
            accident=detection.accident,
            confidence=detection.confidence,
            severity=severity.severity if severity else None,
            score=severity.score if severity else None,
            hospital=hospital.hospital if hospital else None,
            eta=hospital.eta if hospital else None,
            verification=verification,
            features=features,
            integration=integration,
        )
