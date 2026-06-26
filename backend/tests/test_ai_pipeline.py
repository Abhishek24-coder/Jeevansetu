from datetime import datetime, timezone

import pytest

from app.ai_pipeline.accident_detection import AccidentDetectionEngine
from app.ai_pipeline.feature_extraction import FeatureExtractor
from app.ai_pipeline.hospital_recommendation import HospitalRecommendationEngine
from app.ai_pipeline.models.sensor import GPSPoint, MotionVector, SensorDataInput
from app.ai_pipeline.response_builder import AIResponseBuilder
from app.ai_pipeline.severity_prediction import SeverityPredictionEngine
from app.ai_pipeline.utils.hospital_db import MOCK_HOSPITALS
from app.ai_pipeline.validation import SensorDataValidator


def _sensor_packet() -> SensorDataInput:
    return SensorDataInput(
        accelerometer=MotionVector(x=8.0, y=2.0, z=1.0),
        gyroscope=MotionVector(x=4.0, y=1.5, z=0.5),
        gps=GPSPoint(latitude=12.971598, longitude=77.594566),
        speed=12.0,
        previous_speed=82.0,
        timestamp=datetime.now(timezone.utc),
        previous_orientation=MotionVector(x=0.0, y=0.0, z=0.0),
        current_orientation=MotionVector(x=45.0, y=10.0, z=5.0),
    )


def test_validation_rejects_null_island_coordinates():
    packet = _sensor_packet().model_copy(
        update={"gps": GPSPoint(latitude=0.0, longitude=0.0)}
    )

    with pytest.raises(ValueError):
        SensorDataValidator.clean(packet)


def test_feature_extraction_calculates_required_values():
    features = FeatureExtractor.extract(_sensor_packet(), response_delay=15.0)

    assert features.impact_force > 8.0
    assert features.speed_drop == 70.0
    assert features.gyroscope_spike is True
    assert features.orientation_change > 45.0
    assert features.response_delay == 15.0


def test_accident_detection_returns_high_confidence_for_crash_signature():
    features = FeatureExtractor.extract(_sensor_packet(), response_delay=15.0)
    detection = AccidentDetectionEngine.predict(features)

    assert detection.accident is True
    assert detection.confidence >= 0.9
    assert "sudden_speed_drop" in detection.reasons


def test_severity_prediction_classifies_critical_incident():
    features = FeatureExtractor.extract(_sensor_packet(), response_delay=15.0)
    severity = SeverityPredictionEngine.predict(features)

    assert severity.severity == "critical"
    assert severity.score >= 75


def test_hospital_recommendation_ranks_best_candidate():
    features = FeatureExtractor.extract(_sensor_packet(), response_delay=15.0)
    severity = SeverityPredictionEngine.predict(features)
    recommendations = HospitalRecommendationEngine.rank(
        12.971598,
        77.594566,
        severity.severity,
        MOCK_HOSPITALS,
        limit=1,
    )

    assert recommendations[0].hospital == "Apollo Trauma Center"
    assert recommendations[0].ranking_score > 0


def test_response_builder_matches_contract_shape():
    features = FeatureExtractor.extract(_sensor_packet(), response_delay=15.0)
    detection = AccidentDetectionEngine.predict(features)
    severity = SeverityPredictionEngine.predict(features)
    hospital = HospitalRecommendationEngine.rank(
        12.971598,
        77.594566,
        severity.severity,
        MOCK_HOSPITALS,
        limit=1,
    )[0]

    response = AIResponseBuilder.build("INC001", detection, features, severity, hospital)

    assert response.incident_id == "INC001"
    assert response.accident is True
    assert response.severity == "critical"
    assert response.hospital == "Apollo Trauma Center"
    assert response.eta.endswith("min")
