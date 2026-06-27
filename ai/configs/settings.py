from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


AI_ROOT = Path(__file__).resolve().parents[1]
DATASETS_DIR = AI_ROOT / "datasets"
MODELS_DIR = AI_ROOT / "models"


@dataclass(frozen=True)
class AccidentThresholds:
    acceleration_magnitude_g: float = 6.5
    speed_drop_kmph: float = 35.0
    gyro_magnitude_dps: float = 3.2
    orientation_change_deg: float = 35.0


@dataclass(frozen=True)
class SeverityWeights:
    impact_force: float = 0.35
    speed_drop: float = 0.25
    orientation_change: float = 0.20
    response_delay: float = 0.20


@dataclass(frozen=True)
class HospitalWeights:
    trauma_capability: float = 0.40
    eta: float = 0.30
    distance: float = 0.20
    availability: float = 0.10


ACCIDENT_THRESHOLDS = AccidentThresholds()
SEVERITY_WEIGHTS = SeverityWeights()
HOSPITAL_WEIGHTS = HospitalWeights()

