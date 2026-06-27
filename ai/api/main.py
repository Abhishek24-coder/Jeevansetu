from __future__ import annotations

from fastapi import FastAPI, HTTPException

from ai.accident_detection import AccidentDetector
from ai.feature_engineering import FeatureExtractor
from ai.hospital_recommendation import HospitalRecommender
from ai.models.schemas import (
    AIResponse,
    AIResponseRequest,
    AccidentDetectionResponse,
    HospitalRecommendationRequest,
    HospitalRecommendationResponse,
    SensorPayload,
    SeverityPredictionRequest,
    SeverityPredictionResponse,
)
from ai.response_builder import AIResponseBuilder
from ai.severity_prediction import SeverityPredictor
from ai.utils.ids import generate_incident_id


app = FastAPI(
    title="JeevanSetu AI Service",
    version="1.0.0",
    description="Standalone AI layer for accident detection and emergency response decisions.",
)

feature_extractor = FeatureExtractor()
accident_detector = AccidentDetector()
severity_predictor = SeverityPredictor()
hospital_recommender = HospitalRecommender()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "jeevansetu-ai"}


@app.post("/detect-accident", response_model=AccidentDetectionResponse)
def detect_accident(payload: SensorPayload) -> AccidentDetectionResponse:
    features = feature_extractor.extract(payload)
    return accident_detector.predict(features)


@app.post("/predict-severity", response_model=SeverityPredictionResponse)
def predict_severity(payload: SeverityPredictionRequest) -> SeverityPredictionResponse:
    return severity_predictor.predict(payload)


@app.post("/recommend-hospital", response_model=HospitalRecommendationResponse)
def recommend_hospital(payload: HospitalRecommendationRequest) -> HospitalRecommendationResponse:
    try:
        return hospital_recommender.recommend(
            payload.location.latitude,
            payload.location.longitude,
            payload.severity,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/ai-response", response_model=AIResponse)
def ai_response(payload: AIResponseRequest) -> AIResponse:
    if payload.sensor_data.location is None:
        raise HTTPException(status_code=422, detail="sensor_data.location is required for hospital recommendation")

    features = feature_extractor.extract(payload.sensor_data, payload.response_delay)
    detection = accident_detector.predict(features)
    severity = severity_predictor.predict(features)
    try:
        hospital = hospital_recommender.recommend(
            payload.sensor_data.location.latitude,
            payload.sensor_data.location.longitude,
            severity.severity,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    incident_id = payload.incident_id or generate_incident_id()
    return AIResponseBuilder.build(incident_id, detection, severity, hospital)

