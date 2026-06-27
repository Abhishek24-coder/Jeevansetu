from __future__ import annotations

from math import sqrt

from ai.models.schemas import FeatureVector, MotionVector, SensorPayload


class FeatureExtractor:
    """Transforms raw mobile sensor input into model-ready features."""

    @staticmethod
    def vector_magnitude(vector: MotionVector) -> float:
        return sqrt(vector.x**2 + vector.y**2 + vector.z**2)

    @staticmethod
    def speed_drop(previous_speed_kmph: float, current_speed_kmph: float) -> float:
        return max(previous_speed_kmph - current_speed_kmph, 0.0)

    @staticmethod
    def orientation_change(previous_orientation: MotionVector, current_orientation: MotionVector) -> float:
        return sqrt(
            (current_orientation.x - previous_orientation.x) ** 2
            + (current_orientation.y - previous_orientation.y) ** 2
            + (current_orientation.z - previous_orientation.z) ** 2
        )

    @staticmethod
    def impact_force(acceleration_magnitude: float) -> float:
        return max(acceleration_magnitude, 0.0)

    @classmethod
    def extract(cls, sensor_data: SensorPayload, response_delay: float = 0.0) -> FeatureVector:
        acceleration_magnitude = cls.vector_magnitude(sensor_data.accelerometer)
        gyro_magnitude = cls.vector_magnitude(sensor_data.gyroscope)
        speed_drop = cls.speed_drop(sensor_data.previous_speed_kmph, sensor_data.speed_kmph)
        orientation_change = cls.orientation_change(
            sensor_data.previous_orientation,
            sensor_data.current_orientation,
        )

        return FeatureVector(
            acceleration_magnitude=round(acceleration_magnitude, 4),
            gyro_magnitude=round(gyro_magnitude, 4),
            speed_drop=round(speed_drop, 4),
            orientation_change=round(orientation_change, 4),
            impact_force=round(cls.impact_force(acceleration_magnitude), 4),
            response_delay=round(max(response_delay, 0.0), 4),
        )

