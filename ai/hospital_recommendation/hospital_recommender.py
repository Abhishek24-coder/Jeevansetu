from __future__ import annotations

import csv
from pathlib import Path

from ai.configs.settings import DATASETS_DIR, HOSPITAL_WEIGHTS, HospitalWeights
from ai.models.schemas import HospitalRecommendationResponse, HospitalRecord, SeverityLabel
from ai.utils.geo import estimate_eta_minutes, haversine_distance_km


class HospitalRecommender:
    """Ranks hospitals using trauma capability, ETA, distance, and availability."""

    def __init__(self, hospitals: list[HospitalRecord] | None = None, weights: HospitalWeights = HOSPITAL_WEIGHTS) -> None:
        self.weights = weights
        self.hospitals = hospitals if hospitals is not None else self.load_hospitals()

    @staticmethod
    def load_hospitals(path: Path = DATASETS_DIR / "hospitals.csv") -> list[HospitalRecord]:
        if not path.exists():
            return []
        with path.open("r", newline="", encoding="utf-8") as handle:
            rows = csv.DictReader(handle)
            return [
                HospitalRecord(
                    hospital_id=row["hospital_id"],
                    hospital_name=row["hospital_name"],
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    trauma_capability=int(row["trauma_capability"]),
                    icu_available=row["icu_available"].strip().lower() in {"true", "1", "yes"},
                    beds_available=int(row["beds_available"]),
                    emergency_capacity=int(row["emergency_capacity"]),
                    active=row.get("active", "true").strip().lower() in {"true", "1", "yes"},
                )
                for row in rows
            ]

    def recommend(self, latitude: float, longitude: float, severity: SeverityLabel) -> HospitalRecommendationResponse:
        ranked = self.rank(latitude, longitude, severity)
        if not ranked:
            raise ValueError("no active hospitals are available for recommendation")
        return ranked[0]

    def rank(self, latitude: float, longitude: float, severity: SeverityLabel) -> list[HospitalRecommendationResponse]:
        candidates: list[HospitalRecommendationResponse] = []
        for hospital in self.hospitals:
            if not hospital.active:
                continue
            if severity == "critical" and hospital.trauma_capability < 70:
                continue
            distance_km = haversine_distance_km(latitude, longitude, hospital.latitude, hospital.longitude)
            eta_minutes = estimate_eta_minutes(distance_km)
            score = self._hospital_score(hospital, distance_km, eta_minutes)
            candidates.append(
                HospitalRecommendationResponse(
                    hospital_id=hospital.hospital_id,
                    hospital_name=hospital.hospital_name,
                    distance_km=round(distance_km, 2),
                    eta_minutes=eta_minutes,
                    ranking_score=round(score, 4),
                )
            )
        return sorted(candidates, key=lambda item: item.ranking_score, reverse=True)

    def _hospital_score(self, hospital: HospitalRecord, distance_km: float, eta_minutes: int) -> float:
        trauma_score = hospital.trauma_capability / 100.0
        eta_score = 1.0 - min(eta_minutes, 60) / 60.0
        distance_score = 1.0 - min(distance_km, 50) / 50.0
        availability_score = self._availability_score(hospital)
        return (
            self.weights.trauma_capability * trauma_score
            + self.weights.eta * eta_score
            + self.weights.distance * distance_score
            + self.weights.availability * availability_score
        )

    @staticmethod
    def _availability_score(hospital: HospitalRecord) -> float:
        bed_ratio = min(hospital.beds_available / max(hospital.emergency_capacity, 1), 1.0)
        icu_bonus = 0.25 if hospital.icu_available else 0.0
        return min((bed_ratio * 0.75) + icu_bonus, 1.0)

