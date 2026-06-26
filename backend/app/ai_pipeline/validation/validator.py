from datetime import datetime

from app.ai_pipeline.models.sensor import SensorDataInput


class SensorDataValidator:
    """Performs domain checks after Pydantic type and range validation."""

    @staticmethod
    def clean(sensor_data: SensorDataInput) -> SensorDataInput:
        if sensor_data.gps.latitude == 0 and sensor_data.gps.longitude == 0:
            raise ValueError("GPS coordinates cannot both be zero for emergency routing")

        if sensor_data.previous_timestamp and sensor_data.previous_timestamp > sensor_data.timestamp:
            raise ValueError("previous_timestamp cannot be later than timestamp")

        if sensor_data.timestamp > datetime.now(sensor_data.timestamp.tzinfo):
            raise ValueError("timestamp cannot be in the future")

        return sensor_data
