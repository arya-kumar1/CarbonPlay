from __future__ import annotations

import math

TIMEZONE_ORDER = {
    "Pacific": -8,
    "Mountain": -7,
    "Central": -6,
    "Eastern": -5,
}


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_miles = 3958.7613
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_miles * c


def timezone_jump_hours(from_tz: str, to_tz: str) -> int:
    return abs(TIMEZONE_ORDER.get(from_tz, -6) - TIMEZONE_ORDER.get(to_tz, -6))
