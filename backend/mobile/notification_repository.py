"""PostgreSQL repository for the additive GIDS in-app notification inbox.

This file touches only mobile.notifications and mobile.device_notifications.
It never writes to scenario JSON, Dataset1.xlsx, or any Module 1-6 result.
"""

from __future__ import annotations

import json
from datetime import datetime
from uuid import UUID

from database.connection import get_connection


def create_scenario_update_once(
    *,
    title: str,
    body: str,
    scenario_id: str,
    metadata: dict,
) -> int | None:
    """Create one automatic SCENARIO_UPDATE notification per scenario.

    Returns the new notification ID when inserted.
    Returns None when this scenario already has an automatic update.
    """

    sql = """
        INSERT INTO mobile.notifications
            (notification_type, title, body, scenario_id, metadata)
        VALUES
            ('SCENARIO_UPDATE', %s, %s, %s, %s::jsonb)
        ON CONFLICT (scenario_id)
        WHERE notification_type = 'SCENARIO_UPDATE'
          AND scenario_id IS NOT NULL
        DO NOTHING
        RETURNING id;
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                sql,
                (title, body, scenario_id, json.dumps(metadata)),
            )

            row = cursor.fetchone()

            return int(row["id"]) if row else None


def materialize_device_inbox(device_id: UUID) -> None:
    """Make every global notification visible to a device exactly once.

    A device sees notifications created before and after its registration.
    `ON CONFLICT DO NOTHING` makes repeated inbox reads safe and idempotent.
    """
    sql = """
        INSERT INTO mobile.device_notifications
            (device_id, notification_id, delivered_at)
        SELECT %s, notification.id, now()
        FROM mobile.notifications AS notification
        ON CONFLICT (device_id, notification_id) DO NOTHING;
    """
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, (device_id,))


def list_device_notifications(
    *,
    device_id: UUID,
    limit: int,
    offset: int,
    unread_only: bool,
) -> list[dict]:
    clauses = ["device_notification.device_id = %s"]
    values: list[object] = [device_id]

    if unread_only:
        clauses.append("device_notification.is_read = FALSE")

    where_sql = " AND ".join(clauses)
    sql = f"""
        SELECT
            notification.id,
            notification.notification_type,
            notification.title,
            notification.body,
            notification.scenario_id,
            notification.metadata,
            notification.created_at,
            device_notification.is_read,
            device_notification.delivered_at,
            device_notification.read_at
        FROM mobile.device_notifications AS device_notification
        INNER JOIN mobile.notifications AS notification
            ON notification.id = device_notification.notification_id
        WHERE {where_sql}
        ORDER BY notification.created_at DESC, notification.id DESC
        LIMIT %s OFFSET %s;
    """
    values.extend([limit, offset])

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, values)
            return list(cursor.fetchall())


def unread_count(device_id: UUID) -> int:
    sql = """
        SELECT COUNT(*) AS count
        FROM mobile.device_notifications
        WHERE device_id = %s AND is_read = FALSE;
    """
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, (device_id,))
            return int(cursor.fetchone()["count"])


def mark_notification_read(*, device_id: UUID, notification_id: int) -> datetime | None:
    sql = """
        UPDATE mobile.device_notifications
        SET is_read = TRUE,
            read_at = COALESCE(read_at, now())
        WHERE device_id = %s
          AND notification_id = %s
        RETURNING read_at;
    """
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, (device_id, notification_id))
            row = cursor.fetchone()
            return row["read_at"] if row else None


def mark_all_notifications_read(*, device_id: UUID) -> int:
    sql = """
        UPDATE mobile.device_notifications
        SET is_read = TRUE,
            read_at = COALESCE(read_at, now())
        WHERE device_id = %s
          AND is_read = FALSE;
    """
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, (device_id,))
            return cursor.rowcount