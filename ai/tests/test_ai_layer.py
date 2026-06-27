from fastapi.testclient import TestClient

from ai.accident_detection import AccidentDetector
from ai.api.main import app
from ai.feature_engineering import FeatureExtractor
from ai.hospital_recommendation import HospitalRecommender
from ai.models.schemas import Location, MotionVector, SensorPayload
from ai.response_builder import AIResponseBuilder
from ai.severity_prediction import SeverityPredictor


def crash_payload() -> SensorPayload:
    return SensorPayload(
        accelerometer=MotionVector(x=8.4, y=2.1, z=1.2),
        gyroscope=MotionVector(x=4.2, y=1.6, z=0.8),
        speed_kmph=12,
        previous_speed_kmph=82,
        previous_orientation=MotionVector(x=0, y=0, z=0),
        current_orientation=MotionVector(x=48, y=12, z=5),
        location=Location(latitude=12.971598, longitude=77.594566),
    )


def test_complete_ai_layer_contract() -> None:
    features = FeatureExtractor.extract(crash_payload(), response_delay=15)
    detection = AccidentDetector().predict(features)
    severity = SeverityPredictor().predict(features)
    hospital = HospitalRecommender().recommend(12.971598, 77.594566, severity.severity)
    response = AIResponseBuilder.build("INC001", detection, severity, hospital)

    assert detection.accident is True
    assert detection.confidence >= 0.9
    assert severity.severity == "critical"
    assert response.model_dump() == {
        "incident_id": "INC001",
        "accident": True,
        "confidence": detection.confidence,
        "severity": "critical",
        "score": severity.score,
        "hospital": "Apollo Trauma Center",
        "eta": "1 min",
    }


def test_fastapi_ai_response_endpoint() -> None:
    client = TestClient(app)
    response = client.post(
        "/ai-response",
        json={
            "incident_id": "INC001",
            "response_delay": 15,
            "sensor_data": crash_payload().model_dump(mode="json"),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["incident_id"] == "INC001"
    assert payload["accident"] is True
    assert payload["severity"] == "critical"
    assert payload["hospital"] == "Apollo Trauma Center"

