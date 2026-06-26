from app.ai_pipeline.models.pipeline import HospitalCandidate, HospitalRecommendation, SeverityClass
from app.ai_pipeline.utils.geo import haversine_distance_km


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
        recommendations: list[HospitalRecommendation] = []

        for hospital in hospitals:
            distance_km = haversine_distance_km(
                user_latitude,
                user_longitude,
                hospital.latitude,
                hospital.longitude,
            )
            eta_minutes = max((distance_km / 45.0) * 60.0, 1.0)
            trauma = cls._trauma_score(hospital.trauma_level, severity)
            eta_score = cls._normalise_inverse(eta_minutes, worst_value=45.0)
            distance_score = cls._normalise_inverse(distance_km, worst_value=30.0)
            availability = cls._availability_score(hospital)

            ranking_score = (
                0.40 * trauma
                + 0.30 * eta_score
                + 0.20 * distance_score
                + 0.10 * availability
            ) * 100

            recommendations.append(
                HospitalRecommendation(
                    hospital_id=hospital.id,
                    hospital=hospital.name,
                    eta=f"{round(eta_minutes)} min",
                    eta_minutes=round(eta_minutes, 1),
                    distance_km=round(distance_km, 2),
                    trauma_capability_score=round(trauma * 100, 2),
                    availability_score=round(availability * 100, 2),
                    ranking_score=round(ranking_score, 2),
                )
            )

        recommendations.sort(key=lambda item: item.ranking_score, reverse=True)
        return recommendations[:limit]
