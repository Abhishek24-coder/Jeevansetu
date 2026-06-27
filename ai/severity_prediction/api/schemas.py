from pydantic import BaseModel, Field
from typing import Optional

class SeverityPredictionRequest(BaseModel):
    # Location
    latitude: float = Field(..., description="Latitude of the accident")
    longitude: float = Field(..., description="Longitude of the accident")
    
    # Time/Lighting
    hour: Optional[int] = Field(default=-1, description="Hour of the day (0-23)")
    lgt_cond: Optional[int] = Field(default=-1, description="Lighting condition code (1=Daylight, 2=Dark, etc.)")
    
    # Weather/Road
    weather: Optional[int] = Field(default=-1, description="Weather condition code (1=Clear, 2=Rain, etc.)")
    vsurcond: Optional[int] = Field(default=-1, description="Vehicle surface condition (1=Dry, 2=Wet, etc.)")
    
    # Collision Info
    man_coll: Optional[int] = Field(default=-1, description="Manner of collision (0=Not collision, 1=Front-to-rear, etc.)")
    harm_ev: Optional[int] = Field(default=-1, description="First harmful event")
    ve_total: Optional[int] = Field(default=1, description="Total vehicles involved")
    
    # Vehicle Info
    body_typ: Optional[int] = Field(default=-1, description="Vehicle body type")
    impact1: Optional[int] = Field(default=-1, description="Initial point of impact")
    rollover: Optional[int] = Field(default=0, description="Rollover indicator (0=No, 1=Yes)")
    
    # Person Info
    age: Optional[int] = Field(default=30, description="Age of the occupant")
    seat_pos: Optional[int] = Field(default=-1, description="Seat position")
    rest_use: Optional[int] = Field(default=-1, description="Restraint use (3=Shoulder and Lap belt, etc.)")

class HospitalRecommendationInfo(BaseModel):
    hospital_id: str
    hospital_name: str
    distance_km: float
    eta_minutes: int
    ranking_score: float

class SeverityPredictionResponse(BaseModel):
    severity: str = Field(..., description="Predicted severity: minor, moderate, critical")
    score: int = Field(..., description="Confidence score or risk score (0-100)")
    recommended_hospitals: list[HospitalRecommendationInfo] = Field(..., description="List of recommended hospitals")
