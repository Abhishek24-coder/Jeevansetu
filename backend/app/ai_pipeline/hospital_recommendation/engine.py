from app.ai_pipeline.models.pipeline import HospitalCandidate, HospitalRecommendation, SeverityClass
from ai.hospital_recommendation import HospitalRecommender
from ai.models.schemas import HospitalRecord


class HospitalRecommendationEngine:
    @staticmethod
    def _normalise_inverse(value: float, worst_value: float) -> float:
        return max(0.0, min(1.0, 1.0 - (value / worst_value)))

    @staticmethod
    def _trauma_score(trauma_level: int, severity: SeverityClass) -> float:
        base = {1: 1.0, 2: 0.72, 3: 0.45}.get(trauma_level, 0.3)
        if severity == SeverityClass.CRITICAL and trauma_level > 1:
            return base * 0.75
        return base

    @staticmethod
    def _availability_score(hospital: HospitalCandidate) -> float:
        bed_score = min(hospital.available_beds / 20.0, 1.0)
        ventilator_score = min(hospital.ventilators / 10.0, 1.0)
        return (bed_score * 0.6) + (ventilator_score * 0.4)

    @classmethod
    def rank(
        cls,
        user_latitude: float,
        user_longitude: float,
        severity: SeverityClass,
        hospitals: list[HospitalCandidate],
        limit: int = 5,
    ) -> list[HospitalRecommendation]:
        core_hospitals = [
            HospitalRecord(
                hospital_id=str(hospital.id),
                hospital_name=hospital.name,
                latitude=hospital.latitude,
                longitude=hospital.longitude,
                trauma_capability={1: 100, 2: 72, 3: 45}.get(hospital.trauma_level, 30),
                icu_available=hospital.ventilators > 0,
                beds_available=hospital.available_beds,
                emergency_capacity=max(hospital.available_beds + hospital.ventilators, 1),
                active=True,
            )
            for hospital in hospitals
        ]
        core_recommendations = HospitalRecommender(core_hospitals).rank(
            user_latitude,
            user_longitude,
            severity.value,
        )

        recommendations = [
            HospitalRecommendation(
                hospital_id=recommendation.hospital_id,
                hospital=recommendation.hospital_name,
                eta=f"{recommendation.eta_minutes} min",
                eta_minutes=float(recommendation.eta_minutes),
                distance_km=recommendation.distance_km,
                trauma_capability_score=next(
                    hospital.trauma_capability
                    for hospital in core_hospitals
                    if hospital.hospital_id == recommendation.hospital_id
                ),
                availability_score=round(
                    HospitalRecommender._availability_score(
                        next(hospital for hospital in core_hospitals if hospital.hospital_id == recommendation.hospital_id)
                    )
                    * 100,
                    2,
                ),
                ranking_score=round(recommendation.ranking_score * 100, 2),
            )
            for recommendation in core_recommendations[:limit]
        ]
        return recommendations
