from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from app.ai_pipeline.models.sensor import SensorDataInput


class SeverityClass(str, Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    CRITICAL = "critical"


class FeatureVector(BaseModel):
    impact_force: float
    speed_before_crash: float
    speed_after_crash: float
    speed_drop: float
    acceleration_magnitude: float
    gyroscope_magnitude: float
    gyroscope_spike: bool
    orientation_change: float
    response_delay: float


class AccidentDetectionOutput(BaseModel):
    accident: bool
    confidence: float = Field(ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)


class SeverityOutput(BaseModel):
    severity: SeverityClass
    score: int = Field(ge=0, le=100)


class HospitalCandidate(BaseModel):
    id: UUID | str
    name: str
    latitude: float
    longitude: float
    trauma_level: int = Field(ge=1, le=3)
    available_beds: int = Field(ge=0)
    ventilators: int = Field(ge=0)


class HospitalRecommendation(BaseModel):
    hospital_id: UUID | str
    hospital: str
    eta: str
    eta_minutes: float
    distance_km: float
    trauma_capability_score: float
    availability_score: float
    ranking_score: float


class UserVerificationRequest(BaseModel):
    incident_id: str
    message: str
    expires_at: datetime
    timeout_seconds: int = 15


class EmergencyIntegrationResult(BaseModel):
    accident_id: UUID | None = None
    sos_id: UUID | None = None
    notifications_dispatched: bool = False
    live_tracking_updated: bool = False
    dashboard_updated: bool = False
    nearby_volunteers: int = 0


class AIPipelineResponse(BaseModel):
    incident_id: str
    accident: bool
    confidence: float
    severity: SeverityClass | None = None
    score: int | None = None
    hospital: str | None = None
    eta: str | None = None
    verification: UserVerificationRequest | None = None
    features: FeatureVector
    integration: EmergencyIntegrationResult | None = None


class PipelineProcessRequest(BaseModel):
    sensor_data: SensorDataInput
    response_delay: float | None = Field(default=None, ge=0.0)
    auto_escalate: bool = False


class PipelineProcessResponse(BaseModel):
    cleaned_sensor_data: SensorDataInput
    detection: AccidentDetectionOutput
    severity: SeverityOutput | None
    hospital_recommendation: HospitalRecommendation | None
    response: AIPipelineResponse


class UserVerificationResponse(BaseModel):
    safe: bool
    response_delay: float | None = Field(default=None, ge=0.0)
