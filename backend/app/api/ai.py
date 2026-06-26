from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.ai_pipeline.api_routes import router as pipeline_router
from app.api import deps
from app.models.user import User
from app.ai.model_service import AISeverityService

router = APIRouter(prefix="/ai", tags=["ai"])
router.include_router(pipeline_router)


class SeverityPredictionInput(BaseModel):
    impact_force: float
    speed: float
    orientation_change: float
    response_delay: float


class SeverityPredictionOutput(BaseModel):
    severity: str
    score: int


@router.post("/severity", response_model=SeverityPredictionOutput)
async def predict_severity(
    input_in: SeverityPredictionInput,
    current_user: User = Depends(deps.get_current_user),
):
    prediction = AISeverityService.predict_severity(
        impact_force=input_in.impact_force,
        speed=input_in.speed,
        orientation_change=input_in.orientation_change,
        response_delay=input_in.response_delay,
    )
    return prediction
