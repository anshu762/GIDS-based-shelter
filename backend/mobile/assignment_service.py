"""Device-location shelter destination selection for the GIDS mobile API.

This is deliberately separate from Module 4's GIDS/capacity allocation logic.
It reads existing selected/ranked shelters and chooses the nearest one to an
individual device's exact GPS coordinates. It never reserves capacity and
never edits a scenario JSON file.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from mobile.constants import (
    ASSIGNMENT_ASSIGNED,
    ASSIGNMENT_NO_ELIGIBLE_SHELTER,
    ASSIGNMENT_NO_LOCATION,
    ASSIGNMENT_NO_SCENARIO,
    ASSIGNMENT_STALE_LOCATION,
    LOCATION_FRESHNESS,
    MESSAGE_NO_ELIGIBLE_SHELTER,
    MESSAGE_NO_LOCATION,
    MESSAGE_NO_SCENARIO,
    MESSAGE_STALE_LOCATION,
)
from mobile.scenario_reader import (
    extract_ranked_shelters,
    load_completed_scenario,
    scenario_id_from_data,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    """Normalize a database timestamp to timezone-aware UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def haversine_km(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    """Great-circle distance. Matches the existing pipeline's Haversine method."""
    earth_radius_km = 6371.0
    lat_a = math.radians(float(latitude_a))
    lon_a = math.radians(float(longitude_a))
    lat_b = math.radians(float(latitude_b))
    lon_b = math.radians(float(longitude_b))

    delta_lat = lat_b - lat_a
    delta_lon = lon_b - lon_a
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat_a) * math.cos(lat_b) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return earth_radius_km * c


def location_payload(location: dict, freshness_status: str) -> dict:
    return {
        "latitude": float(location["latitude"]),
        "longitude": float(location["longitude"]),
        "accuracy_m": float(location["accuracy_m"]),
        "captured_at": as_utc(location["captured_at"]),
        "freshness_status": freshness_status,
    }


def location_is_fresh(location: dict, now: datetime | None = None) -> bool:
    """Fresh only when age is strictly less than five minutes.

    Exactly five minutes old is stale, as locked in Phase 1.
    Future timestamps are treated as fresh here; this avoids refusing a user
    solely because their device clock is slightly ahead of server time.
    """
    current_time = now or utc_now()
    age = current_time - as_utc(location["captured_at"])
    return age < LOCATION_FRESHNESS


def normalize_shelter(raw: dict, device_lat: float, device_lon: float) -> dict | None:
    """Normalize either Module 5 ranked or Module 6 recommendation fields."""
    try:
        latitude = float(raw.get("Latitude", raw.get("latitude")))
        longitude = float(raw.get("Longitude", raw.get("longitude")))
    except (TypeError, ValueError):
        return None

    shelter_id = raw.get("ShelterID", raw.get("shelter_id"))
    if shelter_id is None or not str(shelter_id).strip():
        return None

    distance_km = haversine_km(device_lat, device_lon, latitude, longitude)
    rank_value = raw.get("RecommendationRank", raw.get("Rank", raw.get("recommendation_rank")))

    try:
        rank = int(rank_value) if rank_value is not None else None
    except (TypeError, ValueError):
        rank = None

    return {
        "shelter_id": str(shelter_id),
        "shelter_name": str(raw.get("ShelterName", raw.get("shelter_name", "Unnamed shelter"))),
        "building_type": raw.get("BuildingType", raw.get("building_type")),
        "locality": raw.get("Locality", raw.get("locality")),
        "latitude": latitude,
        "longitude": longitude,
        "distance_km": round(distance_km, 3),
        "recommendation_tier": raw.get("RecommendationTier", raw.get("recommendation_tier")),
        "recommendation_rank": rank,
        "medical_facility": raw.get("MedicalFacility", raw.get("medical_facility")),
    }


def evaluate_destination(
    *,
    scenarios_dir,
    location: dict | None,
    requested_scenario_id: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Return one assignment/evaluation result using a device's latest GPS point."""
    evaluated_at = now or utc_now()

    if location is None:
        return {
            "scenario_id": None,
            "assignment_status": ASSIGNMENT_NO_LOCATION,
            "location_used": None,
            "shelter": None,
            "evaluated_at": evaluated_at,
            "message": MESSAGE_NO_LOCATION,
        }

    fresh = location_is_fresh(location, evaluated_at)
    if not fresh:
        return {
            "scenario_id": None,
            "assignment_status": ASSIGNMENT_STALE_LOCATION,
            "location_used": location_payload(location, "STALE"),
            "shelter": None,
            "evaluated_at": evaluated_at,
            "message": MESSAGE_STALE_LOCATION,
        }

    scenario_data = load_completed_scenario(scenarios_dir, requested_scenario_id)
    if scenario_data is None:
        return {
            "scenario_id": None,
            "assignment_status": ASSIGNMENT_NO_SCENARIO,
            "location_used": location_payload(location, "FRESH"),
            "shelter": None,
            "evaluated_at": evaluated_at,
            "message": MESSAGE_NO_SCENARIO,
        }

    device_lat = float(location["latitude"])
    device_lon = float(location["longitude"])
    shelters = [
        item
        for raw in extract_ranked_shelters(scenario_data)
        if (item := normalize_shelter(raw, device_lat, device_lon)) is not None
    ]

    scenario_id = scenario_id_from_data(scenario_data)
    if not shelters:
        return {
            "scenario_id": scenario_id,
            "assignment_status": ASSIGNMENT_NO_ELIGIBLE_SHELTER,
            "location_used": location_payload(location, "FRESH"),
            "shelter": None,
            "evaluated_at": evaluated_at,
            "message": MESSAGE_NO_ELIGIBLE_SHELTER,
        }

    # Primary sort criterion is exact distance from the device. Recommendation
    # rank is only a stable tie-breaker; this honors the Phase 1 requirement
    # that individual selection uses exact device coordinates.
    shelters.sort(
        key=lambda item: (
            item["distance_km"],
            item["recommendation_rank"] if item["recommendation_rank"] is not None else 999999,
            item["shelter_id"],
        )
    )

    return {
        "scenario_id": scenario_id,
        "assignment_status": ASSIGNMENT_ASSIGNED,
        "location_used": location_payload(location, "FRESH"),
        "shelter": shelters[0],
        "all_shelters": shelters,
        "evaluated_at": evaluated_at,
        "message": None,
    }