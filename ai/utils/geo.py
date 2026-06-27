from __future__ import annotations

from math import atan2, cos, radians, sin, sqrt


EARTH_RADIUS_KM = 6371.0088
DEFAULT_AMBULANCE_SPEED_KMPH = 35.0


def haversine_distance_km(
    origin_latitude: float,
    origin_longitude: float,
    destination_latitude: float,
    destination_longitude: float,
) -> float:
    lat1 = radians(origin_latitude)
    lon1 = radians(origin_longitude)
    lat2 = radians(destination_latitude)
    lon2 = radians(destination_longitude)

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return EARTH_RADIUS_KM * c


def estimate_eta_minutes(distance_km: float, speed_kmph: float = DEFAULT_AMBULANCE_SPEED_KMPH) -> int:
    if speed_kmph <= 0:
        raise ValueError("speed_kmph must be positive")
    return max(1, round((distance_km / speed_kmph) * 60))

