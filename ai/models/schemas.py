from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator


SeverityLabel = Literal["minor", "moderate", "critical"]


class MotionVector(BaseModel):
    x: float
    y: float
    z: float


class Location(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class SensorPayload(BaseModel):
    accelerometer: MotionVector
    gyroscope: MotionVector
    speed_kmph: float = Field(..., ge=0, le=260)
    previous_speed_kmph: float = Field(..., ge=0, le=260)
    previous_orientation: MotionVector = Field(default_factory=lambda: MotionVector(x=0, y=0, z=0))
    current_orientation: MotionVector = Field(default_factory=lambda: MotionVector(x=0, y=0, z=0))
    location: Location | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FeatureVector(BaseModel):
    acceleration_magnitude: float
    gyro_magnitude: float
    speed_drop: float
    orientation_change: float
    impact_force: float
    response_delay: float


class AccidentDetectionResponse(BaseModel):
    accident: bool
    confidence: float = Field(..., ge=0, le=1)
    reasons: list[str] = Field(default_factory=list)


class SeverityPredictionRequest(BaseModel):
    impact_force: float = Field(..., ge=0)
    speed_drop: float = Field(..., ge=0)
    orientation_change: float = Field(..., ge=0)
    response_delay: float = Field(..., ge=0)


class SeverityPredictionResponse(BaseModel):
    severity: SeverityLabel
    score: int = Field(..., ge=0, le=100)


class HospitalRecord(BaseModel):
    hospital_id: str
    hospital_name: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    trauma_capability: int = Field(..., ge=0, le=100)
    icu_available: bool
    beds_available: int = Field(..., ge=0)
    emergency_capacity: int = Field(..., ge=0)
    active: bool = True

    @field_validator("hospital_id", "hospital_name")
    @classmethod
    def require_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value.strip()


class HospitalRecommendationRequest(BaseModel):
    location: Location
    severity: SeverityLabel


class HospitalRecommendationResponse(BaseModel):
    hospital_id: str
    hospital_name: str
    distance_km: float
    eta_minutes: int
    ranking_score: float


class AIResponseRequest(BaseModel):
    incident_id: str
    sensor_data: SensorPayload
    response_delay: float = Field(default=15.0, ge=0)


class AIResponse(BaseModel):
    incident_id: str
    accident: bool
    confidence: float
    severity: SeverityLabel
    score: int
    hospital: str
    eta: str

