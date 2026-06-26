from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_pipeline.accident_detection import AccidentDetectionEngine
from app.ai_pipeline.feature_extraction import FeatureExtractor
from app.ai_pipeline.hospital_recommendation import HospitalRecommendationEngine
from app.ai_pipeline.models.pipeline import (
    AIPipelineResponse,
    EmergencyIntegrationResult,
    HospitalCandidate,
    PipelineProcessRequest,
    PipelineProcessResponse,
    SeverityOutput,
    UserVerificationResponse,
)
from app.ai_pipeline.response_builder import AIResponseBuilder
from app.ai_pipeline.severity_prediction import SeverityPredictionEngine
from app.ai_pipeline.user_verification import VerificationService
from app.ai_pipeline.utils.hospital_db import MOCK_HOSPITALS
from app.ai_pipeline.validation import SensorDataValidator
from app.api import deps
from app.db.session import get_db
from app.models.user import User
from app.repositories.hospital import HospitalRepository
from app.schemas.accident import AccidentCreate
from app.schemas.sos_request import SOSRequestCreate
from app.services.accident import AccidentService
from app.services.location import LocationService
from app.services.sos import SOSService
from app.services.volunteers import VolunteerService

router = APIRouter(prefix="/pipeline", tags=["ai-pipeline"])

_INCIDENT_COUNTER = 0
_PENDING_INCIDENTS: dict[str, PipelineProcessResponse] = {}
_INCIDENT_USERS: dict[str, str] = {}


def _next_incident_id() -> str:
    global _INCIDENT_COUNTER
    _INCIDENT_COUNTER += 1
    return f"INC{_INCIDENT_COUNTER:03d}"


async def _load_hospitals(db: AsyncSession) -> list[HospitalCandidate]:
    hospitals = await HospitalRepository(db).get_multi(limit=100)
    if not hospitals:
        return MOCK_HOSPITALS

    return [
        HospitalCandidate(
            id=hospital.id,
            name=hospital.name,
            latitude=hospital.latitude,
            longitude=hospital.longitude,
            trauma_level=hospital.trauma_level,
            available_beds=hospital.available_beds,
            ventilators=hospital.ventilators,
        )
        for hospital in hospitals
    ]


async def _run_emergency_workflow(
    db: AsyncSession,
    current_user: User,
    pipeline_response: PipelineProcessResponse,
) -> EmergencyIntegrationResult:
    sensor_data = pipeline_response.cleaned_sensor_data
    features = pipeline_response.response.features

    location_service = LocationService(db)
    await location_service.update_location(
        str(current_user.id),
        sensor_data.gps.latitude,
        sensor_data.gps.longitude,
    )

    accident = await AccidentService(db).report_accident(
        str(current_user.id),
        AccidentCreate(
            latitude=sensor_data.gps.latitude,
            longitude=sensor_data.gps.longitude,
            impact_force=features.impact_force,
            speed=features.speed_before_crash,
            orientation_change=features.orientation_change,
        ),
    )

    sos = await SOSService(db).create_sos(
        str(current_user.id),
        SOSRequestCreate(accident_id=accident.id),
    )

    volunteers = await VolunteerService(db).get_nearby_volunteers(
        sensor_data.gps.latitude,
        sensor_data.gps.longitude,
        max_radius_km=5.0,
        limit=5,
    )

    return EmergencyIntegrationResult(
        accident_id=accident.id,
        sos_id=sos.id,
        notifications_dispatched=True,
        live_tracking_updated=True,
        dashboard_updated=True,
        nearby_volunteers=len(volunteers),
    )


@router.post("/process", response_model=PipelineProcessResponse)
async def process_sensor_data(
    request: PipelineProcessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    try:
        cleaned_data = SensorDataValidator.clean(request.sensor_data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    features = FeatureExtractor.extract(cleaned_data, request.response_delay)
    detection = AccidentDetectionEngine.predict(features)
    incident_id = _next_incident_id()

    severity: SeverityOutput | None = None
    hospital = None
    verification = None
    integration = None

    if detection.accident:
        severity = SeverityPredictionEngine.predict(features)
        hospitals = await _load_hospitals(db)
        hospital_recommendations = HospitalRecommendationEngine.rank(
            cleaned_data.gps.latitude,
            cleaned_data.gps.longitude,
            severity.severity,
            hospitals,
            limit=1,
        )
        hospital = hospital_recommendations[0] if hospital_recommendations else None

        if request.auto_escalate:
            preliminary_response = AIResponseBuilder.build(
                incident_id=incident_id,
                detection=detection,
                features=features,
                severity=severity,
                hospital=hospital,
            )
            preliminary = PipelineProcessResponse(
                cleaned_sensor_data=cleaned_data,
                detection=detection,
                severity=severity,
                hospital_recommendation=hospital,
                response=preliminary_response,
            )
            integration = await _run_emergency_workflow(db, current_user, preliminary)
        else:
            verification = VerificationService.create_request(incident_id)

    response = AIResponseBuilder.build(
        incident_id=incident_id,
        detection=detection,
        features=features,
        severity=severity,
        hospital=hospital,
        verification=verification,
        integration=integration,
    )
    pipeline_response = PipelineProcessResponse(
        cleaned_sensor_data=cleaned_data,
        detection=detection,
        severity=severity,
        hospital_recommendation=hospital,
        response=response,
    )

    if detection.accident and verification:
        _PENDING_INCIDENTS[incident_id] = pipeline_response
        _INCIDENT_USERS[incident_id] = str(current_user.id)

    return pipeline_response


@router.post("/{incident_id}/verify", response_model=AIPipelineResponse)
async def verify_incident(
    incident_id: str,
    verification_response: UserVerificationResponse,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    pipeline_response = _PENDING_INCIDENTS.get(incident_id)
    if not pipeline_response or _INCIDENT_USERS.get(incident_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending incident not found")

    if verification_response.safe:
        _PENDING_INCIDENTS.pop(incident_id, None)
        _INCIDENT_USERS.pop(incident_id, None)
        return pipeline_response.response.model_copy(
            update={
                "accident": False,
                "confidence": 0.0,
                "verification": None,
                "integration": EmergencyIntegrationResult(),
            }
        )

    if verification_response.response_delay is not None:
        pipeline_response.response.features.response_delay = verification_response.response_delay
        updated_severity = SeverityPredictionEngine.predict(pipeline_response.response.features)
        pipeline_response.severity = updated_severity
        pipeline_response.response.severity = updated_severity.severity
        pipeline_response.response.score = updated_severity.score

    integration = await _run_emergency_workflow(db, current_user, pipeline_response)
    _PENDING_INCIDENTS.pop(incident_id, None)
    _INCIDENT_USERS.pop(incident_id, None)
    return pipeline_response.response.model_copy(update={"verification": None, "integration": integration})


@router.post("/{incident_id}/escalate", response_model=AIPipelineResponse)
async def escalate_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    pipeline_response = _PENDING_INCIDENTS.get(incident_id)
    if not pipeline_response or _INCIDENT_USERS.get(incident_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending incident not found")

    verification = pipeline_response.response.verification
    if verification and verification.expires_at > datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Verification timer is still active",
        )

    integration = await _run_emergency_workflow(db, current_user, pipeline_response)
    _PENDING_INCIDENTS.pop(incident_id, None)
    _INCIDENT_USERS.pop(incident_id, None)
    return pipeline_response.response.model_copy(update={"verification": None, "integration": integration})


@router.get("/{incident_id}", response_model=AIPipelineResponse)
async def get_pending_incident(
    incident_id: str,
    current_user: User = Depends(deps.get_current_user),
):
    pipeline_response = _PENDING_INCIDENTS.get(incident_id)
    if not pipeline_response or _INCIDENT_USERS.get(incident_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending incident not found")
    return pipeline_response.response
