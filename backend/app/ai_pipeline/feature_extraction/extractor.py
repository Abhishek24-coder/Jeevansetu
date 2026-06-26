import math
from datetime import datetime, timezone

from app.ai_pipeline.models.pipeline import FeatureVector
from app.ai_pipeline.models.sensor import MotionVector, SensorDataInput


class FeatureExtractor:
    @staticmethod
    def magnitude(vector: MotionVector) -> float:
        return math.sqrt(vector.x**2 + vector.y**2 + vector.z**2)

    @staticmethod
    def orientation_delta(previous: MotionVector | None, current: MotionVector | None) -> float:
        if previous is None or current is None:
            return 0.0
        return math.sqrt(
            (current.x - previous.x) ** 2
            + (current.y - previous.y) ** 2
            + (current.z - previous.z) ** 2
        )

    @classmethod
    def extract(cls, sensor_data: SensorDataInput, response_delay: float | None = None) -> FeatureVector:
        acceleration_magnitude = cls.magnitude(sensor_data.accelerometer)
        gyroscope_magnitude = cls.magnitude(sensor_data.gyroscope)
        speed_before = sensor_data.previous_speed if sensor_data.previous_speed is not None else sensor_data.speed
        speed_after = sensor_data.speed
        speed_drop = max(speed_before - speed_after, 0.0)

        if response_delay is not None:
            delay = response_delay
        else:
            now = datetime.now(timezone.utc)
            delay = max((now - sensor_data.timestamp).total_seconds(), 0.0)

        # Treat acceleration magnitude as G-force when device SDK provides normalized g values.
        impact_force = acceleration_magnitude

        return FeatureVector(
            impact_force=round(impact_force, 3),
            speed_before_crash=round(speed_before, 2),
            speed_after_crash=round(speed_after, 2),
            speed_drop=round(speed_drop, 2),
            acceleration_magnitude=round(acceleration_magnitude, 3),
            gyroscope_magnitude=round(gyroscope_magnitude, 3),
            gyroscope_spike=gyroscope_magnitude >= 4.0,
            orientation_change=round(
                cls.orientation_delta(sensor_data.previous_orientation, sensor_data.current_orientation),
                3,
            ),
            response_delay=round(delay, 2),
        )
