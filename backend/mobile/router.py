"""FastAPI router for the additive GIDS Mobile API.

Mount this router in api_server.py with:
    from mobile.router import router as mobile_router
    app.include_router(mobile_router)

No route in this file overlaps with existing dashboard routes.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID
from mobile import notification_repository
from mobile.notification_schemas import (
    MarkAllNotificationsReadResponse,
    MarkNotificationReadResponse,
    NotificationListResponse,
    UnreadNotificationCountResponse,
)

from fastapi import APIRouter, Header, HTTPException, Query, Request, status

from database.connection import database_is_configured
from mobile import repository
from mobile.assignment_service import evaluate_destination
from mobile.constants import (
    ASSIGNMENT_ASSIGNED,
    LOCATION_ACCURACY_THRESHOLD_M,
    NEAREST_SHELTER_MAX_LIMIT,
    NEAREST_SHELTER_MIN_LIMIT,
)
from mobile.schemas import (
    AssignmentAcknowledgeRequest,
    AssignmentAcknowledgeResponse,
    AssignmentResponse,
    DeviceRegistrationRequest,
    DeviceRegistrationResponse,
    LocationUpdateRequest,
    LocationUpdateResponse,
    NearestSheltersResponse,
    NotificationTokenRequest,
    NotificationTokenResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mobile", tags=["mobile"])


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def require_database() -> None:
    if not database_is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Mobile services are not configured yet. DATABASE_URL is required "
                "for /api/mobile endpoints."
            ),
        )


def require_device_id(x_device_id: str | None) -> UUID:
    if not x_device_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Device-Id header is required.",
        )
    try:
        return UUID(x_device_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Device-Id must be a valid UUID.",
        ) from exc


def require_registered_device(device_id: UUID) -> None:
    if not repository.device_exists(device_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not registered. Call /api/mobile/devices/register first.",
        )


def scenarios_dir_from_request(request: Request) -> Path:
    """Read the exact SCENARIOS_DIR selected by api_server.py.

    This avoids duplicating a filesystem setting. The mobile service sees the
    same scenario volume/directory as existing dashboard endpoints.
    """
    value = getattr(request.app.state, "scenarios_dir", None)
    if value is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Scenario storage is not configured on the application.",
        )
    return Path(value)


@router.get("/health")
def mobile_health() -> dict:
    """Mobile/PostgreSQL readiness check; does not affect /api/health."""
    if not database_is_configured():
        return {"status": "degraded", "database_configured": False}

    try:
        # A tiny repository-independent connectivity query.
        from database.connection import get_connection

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 AS ok;")
                cursor.fetchone()
        return {"status": "ok", "database_configured": True}
    except Exception as exc:  # noqa: BLE001
        logger.exception("Mobile database health check failed")
        return {
            "status": "degraded",
            "database_configured": True,
            "detail": f"Database connection failed: {type(exc).__name__}",
        }


@router.post(
    "/devices/register",
    response_model=DeviceRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_device(payload: DeviceRegistrationRequest) -> DeviceRegistrationResponse:
    require_database()
    try:
        registered_at = repository.register_device(
            device_id=payload.device_id,
            platform=payload.platform,
            app_version=payload.app_version,
            fcm_token=payload.fcm_token,
        )
        return DeviceRegistrationResponse(
            device_id=payload.device_id,
            registered_at=registered_at,
            status="REGISTERED",
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Device registration failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not register device: {type(exc).__name__}",
        ) from exc


@router.post("/location", response_model=LocationUpdateResponse)
def update_location(
    payload: LocationUpdateRequest,
    x_device_id: str | None = Header(default=None, alias="X-Device-Id"),
) -> LocationUpdateResponse:
    require_database()
    device_id = require_device_id(x_device_id)
    require_registered_device(device_id)

    try:
        stored_at = repository.upsert_location(
            device_id=device_id,
            latitude=payload.latitude,
            longitude=payload.longitude,
            accuracy_m=payload.accuracy_m,
            captured_at=payload.captured_at,
        )
        accuracy_status = (
            "OK"
            if payload.accuracy_m <= LOCATION_ACCURACY_THRESHOLD_M
            else "LOW_ACCURACY"
        )
        return LocationUpdateResponse(
            device_id=device_id,
            accepted=True,
            accuracy_status=accuracy_status,
            stored_at=stored_at,
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Location update failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not store location: {type(exc).__name__}",
        ) from exc


@router.get("/assignment", response_model=AssignmentResponse)
def get_assignment(
    request: Request,
    scenario_id: str | None = Query(default=None, max_length=255),
    x_device_id: str | None = Header(default=None, alias="X-Device-Id"),
) -> AssignmentResponse:
    require_database()
    device_id = require_device_id(x_device_id)
    require_registered_device(device_id)

    try:
        location = repository.get_latest_location(device_id)
        result = evaluate_destination(
            scenarios_dir=scenarios_dir_from_request(request),
            location=location,
            requested_scenario_id=scenario_id,
        )

        # If a caller explicitly names a scenario but it cannot be loaded,
        # distinguish this protocol error from the valid NO_SCENARIO state.
        if scenario_id is not None and result["assignment_status"] == "NO_SCENARIO":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scenario not found or it has not completed Module 6.",
            )

        repository.save_assignment(
            device_id=device_id,
            scenario_id=result["scenario_id"],
            assignment_status=result["assignment_status"],
            shelter=result["shelter"],
            evaluated_at=result["evaluated_at"],
        )

        return AssignmentResponse(device_id=device_id, **result)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Assignment evaluation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not evaluate shelter destination: {type(exc).__name__}",
        ) from exc


@router.post("/assignment/acknowledge", response_model=AssignmentAcknowledgeResponse)
def acknowledge_assignment(
    payload: AssignmentAcknowledgeRequest,
    x_device_id: str | None = Header(default=None, alias="X-Device-Id"),
) -> AssignmentAcknowledgeResponse:
    require_database()
    device_id = require_device_id(x_device_id)
    require_registered_device(device_id)

    try:
        recorded_at = repository.record_acknowledgment(
            device_id=device_id,
            scenario_id=payload.scenario_id,
            shelter_id=payload.shelter_id,
            action=payload.action,
        )
        return AssignmentAcknowledgeResponse(
            device_id=device_id,
            recorded=True,
            action=payload.action,
            recorded_at=recorded_at,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Assignment acknowledgment failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not record assignment action: {type(exc).__name__}",
        ) from exc


@router.get("/shelters/nearest", response_model=NearestSheltersResponse)
def get_nearest_shelters(
    request: Request,
    limit: int = Query(default=5),
    scenario_id: str | None = Query(default=None, max_length=255),
    x_device_id: str | None = Header(default=None, alias="X-Device-Id"),
) -> NearestSheltersResponse:
    require_database()
    device_id = require_device_id(x_device_id)
    require_registered_device(device_id)

    # Locked Phase 1 behavior: silently clamp invalid/small values to 1,
    # and protect mobile/API resources by clamping large values to 20.
    limit = max(NEAREST_SHELTER_MIN_LIMIT, min(limit, NEAREST_SHELTER_MAX_LIMIT))

    try:
        location = repository.get_latest_location(device_id)
        result = evaluate_destination(
            scenarios_dir=scenarios_dir_from_request(request),
            location=location,
            requested_scenario_id=scenario_id,
        )

        if scenario_id is not None and result["assignment_status"] == "NO_SCENARIO":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scenario not found or it has not completed Module 6.",
            )

        shelters = (
            result.get("all_shelters", [])[:limit]
            if result["assignment_status"] == ASSIGNMENT_ASSIGNED
            else []
        )

        # This endpoint is explicitly read-only: no assignment cache writes
        # and no acknowledgment writes occur here.
        return NearestSheltersResponse(
            device_id=device_id,
            scenario_id=result["scenario_id"],
            assignment_status=result["assignment_status"],
            location_used=result["location_used"],
            shelters=shelters,
            evaluated_at=result["evaluated_at"],
            message=result["message"],
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Nearest shelters evaluation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not find nearest shelters: {type(exc).__name__}",
        ) from exc


@router.post("/notifications/token", response_model=NotificationTokenResponse)
def update_notification_token(
    payload: NotificationTokenRequest,
    x_device_id: str | None = Header(default=None, alias="X-Device-Id"),
) -> NotificationTokenResponse:
    require_database()
    device_id = require_device_id(x_device_id)
    require_registered_device(device_id)

    try:
        updated_at = repository.update_fcm_token(
            device_id=device_id,
            fcm_token=payload.fcm_token,
        )
        if updated_at is None:
            # Defensive fallback: device_exists already passed, but preserve a
            # correct client-level response if a concurrent deletion occurred.
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not registered. Call /api/mobile/devices/register first.",
            )
        return NotificationTokenResponse(
            device_id=device_id,
            token_updated=True,
            updated_at=updated_at,
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("FCM token update failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not update notification token: {type(exc).__name__}",
        ) from exc

@router.get("/notifications", response_model=NotificationListResponse)
def get_in_app_notifications(
    limit: int = Query(default=20),
    offset: int = Query(default=0, ge=0),
    unread_only: bool = Query(default=False),
    x_device_id: str | None = Header(default=None, alias="X-Device-Id"),
) -> NotificationListResponse:
    """Return this device's notification inbox, newest first.

    Per-device rows are materialized lazily, so registered devices receive
    notifications created before their first inbox request as well.
    """
    require_database()
    device_id = require_device_id(x_device_id)
    require_registered_device(device_id)

    # Keep list requests bounded. Unlike nearby shelters, a zero/negative
    # notification list limit is treated as the normal default (20), because
    # an empty inbox fetch is not useful to the UI.
    limit = max(1, min(limit, 50))

    try:
        notification_repository.materialize_device_inbox(device_id)
        notifications = notification_repository.list_device_notifications(
            device_id=device_id,
            limit=limit,
            offset=offset,
            unread_only=unread_only,
        )
        count = notification_repository.unread_count(device_id)

        return NotificationListResponse(
            notifications=notifications,
            unread_count=count,
            limit=limit,
            offset=offset,
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Could not load device notification inbox")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not load notifications: {type(exc).__name__}",
        ) from exc


@router.get(
    "/notifications/unread-count",
    response_model=UnreadNotificationCountResponse,
)
def get_unread_notification_count(
    x_device_id: str | None = Header(default=None, alias="X-Device-Id"),
) -> UnreadNotificationCountResponse:
    """Return unread count for a compact AppBar notification badge."""
    require_database()
    device_id = require_device_id(x_device_id)
    require_registered_device(device_id)

    try:
        notification_repository.materialize_device_inbox(device_id)
        return UnreadNotificationCountResponse(
            unread_count=notification_repository.unread_count(device_id)
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Could not load unread notification count")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not load unread notification count: {type(exc).__name__}",
        ) from exc


@router.post(
    "/notifications/{notification_id}/read",
    response_model=MarkNotificationReadResponse,
)
def mark_in_app_notification_read(
    notification_id: int,
    x_device_id: str | None = Header(default=None, alias="X-Device-Id"),
) -> MarkNotificationReadResponse:
    """Mark one notification as read for only the requesting device."""
    require_database()
    device_id = require_device_id(x_device_id)
    require_registered_device(device_id)

    if notification_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="notification_id must be a positive integer.",
        )

    try:
        # This first makes global alerts visible to the device; then it is
        # safe to mark the requested known inbox record as read.
        notification_repository.materialize_device_inbox(device_id)
        read_at = notification_repository.mark_notification_read(
            device_id=device_id,
            notification_id=notification_id,
        )

        if read_at is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found for this device.",
            )

        return MarkNotificationReadResponse(
            notification_id=notification_id,
            is_read=True,
            read_at=read_at,
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Could not mark notification as read")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not mark notification as read: {type(exc).__name__}",
        ) from exc


@router.post(
    "/notifications/read-all",
    response_model=MarkAllNotificationsReadResponse,
)
def mark_all_in_app_notifications_read(
    x_device_id: str | None = Header(default=None, alias="X-Device-Id"),
) -> MarkAllNotificationsReadResponse:
    """Mark all currently visible unread messages as read for this device."""
    require_database()
    device_id = require_device_id(x_device_id)
    require_registered_device(device_id)

    try:
        notification_repository.materialize_device_inbox(device_id)
        marked_read_count = notification_repository.mark_all_notifications_read(
            device_id=device_id
        )
        return MarkAllNotificationsReadResponse(
            marked_read_count=marked_read_count
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Could not mark all notifications as read")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not mark all notifications as read: {type(exc).__name__}",
        ) from exc