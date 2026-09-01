"""PostgreSQL repository functions for the additive GIDS mobile API.

Every function here touches only the `mobile.*` PostgreSQL schema. This file
never writes scenario JSON, never reads/writes Dataset1.xlsx, and never calls
or mutates Modules 1-6.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from database.connection import get_connection


def register_device(
    *,
    device_id: UUID,
    platform: str,
    app_version: str,
    fcm_token: str | None,
) -> datetime:
    """Create or refresh a device registration; return original registered_at."""
    sql = """
        INSERT INTO mobile.devices (device_id, platform, app_version, fcm_token)
        VALUES (%(device_id)s, %(platform)s, %(app_version)s, %(fcm_token)s)
        ON CONFLICT (device_id) DO UPDATE
        SET
            platform = EXCLUDED.platform,
            app_version = EXCLUDED.app_version,
            fcm_token = COALESCE(EXCLUDED.fcm_token, mobile.devices.fcm_token),
            updated_at = now()
        RETURNING registered_at;
    """
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                sql,
                {
                    "device_id": device_id,
                    "platform": platform,
                    "app_version": app_version,
                    "fcm_token": fcm_token,
                },
            )
            row = cursor.fetchone()
            return row["registered_at"]


def device_exists(device_id: UUID) -> bool:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM mobile.devices WHERE device_id = %s) AS present;",
                (device_id,),
            )
            return bool(cursor.fetchone()["present"])


def upsert_location(
    *,
    device_id: UUID,
    latitude: float,
    longitude: float,
    accuracy_m: float,
    captured_at: datetime,
) -> datetime:
    sql = """
        INSERT INTO mobile.device_locations
            (device_id, latitude, longitude, accuracy_m, captured_at, stored_at)
        VALUES
            (%(device_id)s, %(latitude)s, %(longitude)s, %(accuracy_m)s,
             %(captured_at)s, now())
        ON CONFLICT (device_id) DO UPDATE
        SET
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            accuracy_m = EXCLUDED.accuracy_m,
            captured_at = EXCLUDED.captured_at,
            stored_at = now()
        RETURNING stored_at;
    """
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                sql,
                {
                    "device_id": device_id,
                    "latitude": latitude,
                    "longitude": longitude,
                    "accuracy_m": accuracy_m,
                    "captured_at": captured_at,
                },
            )
            return cursor.fetchone()["stored_at"]


def get_latest_location(device_id: UUID) -> dict | None:
    sql = """
        SELECT latitude, longitude, accuracy_m, captured_at, stored_at
        FROM mobile.device_locations
        WHERE device_id = %s;
    """
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, (device_id,))
            return cursor.fetchone()


def save_assignment(
    *,
    device_id: UUID,
    scenario_id: str | None,
    assignment_status: str,
    shelter: dict | None,
    evaluated_at: datetime,
) -> None:
    sql = """
        INSERT INTO mobile.device_assignments (
            device_id, scenario_id, assignment_status,
            shelter_id, shelter_name, shelter_latitude, shelter_longitude,
            distance_km, recommendation_tier, recommendation_rank, evaluated_at
        ) VALUES (
            %(device_id)s, %(scenario_id)s, %(assignment_status)s,
            %(shelter_id)s, %(shelter_name)s, %(shelter_latitude)s,
            %(shelter_longitude)s, %(distance_km)s, %(recommendation_tier)s,
            %(recommendation_rank)s, %(evaluated_at)s
        )
        ON CONFLICT (device_id) DO UPDATE
        SET
            scenario_id = EXCLUDED.scenario_id,
            assignment_status = EXCLUDED.assignment_status,
            shelter_id = EXCLUDED.shelter_id,
            shelter_name = EXCLUDED.shelter_name,
            shelter_latitude = EXCLUDED.shelter_latitude,
            shelter_longitude = EXCLUDED.shelter_longitude,
            distance_km = EXCLUDED.distance_km,
            recommendation_tier = EXCLUDED.recommendation_tier,
            recommendation_rank = EXCLUDED.recommendation_rank,
            evaluated_at = EXCLUDED.evaluated_at;
    """
    values = {
        "device_id": device_id,
        "scenario_id": scenario_id,
        "assignment_status": assignment_status,
        "shelter_id": shelter.get("shelter_id") if shelter else None,
        "shelter_name": shelter.get("shelter_name") if shelter else None,
        "shelter_latitude": shelter.get("latitude") if shelter else None,
        "shelter_longitude": shelter.get("longitude") if shelter else None,
        "distance_km": shelter.get("distance_km") if shelter else None,
        "recommendation_tier": shelter.get("recommendation_tier") if shelter else None,
        "recommendation_rank": shelter.get("recommendation_rank") if shelter else None,
        "evaluated_at": evaluated_at,
    }
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, values)


def record_acknowledgment(
    *,
    device_id: UUID,
    scenario_id: str,
    shelter_id: str,
    action: str,
) -> datetime:
    sql = """
        INSERT INTO mobile.assignment_acknowledgments
            (device_id, scenario_id, shelter_id, action, recorded_at)
        VALUES (%s, %s, %s, %s, now())
        RETURNING recorded_at;
    """
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, (device_id, scenario_id, shelter_id, action))
            return cursor.fetchone()["recorded_at"]


def update_fcm_token(*, device_id: UUID, fcm_token: str) -> datetime | None:
    sql = """
        UPDATE mobile.devices
        SET fcm_token = %s, updated_at = now()
        WHERE device_id = %s
        RETURNING updated_at;
    """
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, (fcm_token, device_id))
            row = cursor.fetchone()
            return row["updated_at"] if row else None