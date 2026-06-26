from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, Field, field_validator


Latitude = Annotated[float, Field(ge=-90.0, le=90.0)]
Longitude = Annotated[float, Field(ge=-180.0, le=180.0)]


class MotionVector(BaseModel):
    x: float
    y: float
    z: float


class GPSPoint(BaseModel):
    latitude: Latitude
    longitude: Longitude
    accuracy_m: float | None = Field(default=None, ge=0.0)


class SensorDataInput(BaseModel):
    accelerometer: MotionVector
    gyroscope: MotionVector
    gps: GPSPoint
    speed: float = Field(ge=0.0, le=320.0, description="Current speed in km/h")
    previous_speed: float | None = Field(default=None, ge=0.0, le=320.0)
    timestamp: datetime
    previous_timestamp: datetime | None = None
    previous_orientation: MotionVector | None = None
    current_orientation: MotionVector | None = None
    device_id: str | None = None

    @field_validator("timestamp", "previous_timestamp")
    @classmethod
    def normalize_timestamp(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
