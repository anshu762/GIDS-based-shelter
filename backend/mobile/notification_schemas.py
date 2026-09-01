"""Pydantic response models for the GIDS in-app notification inbox."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel


NotificationType = Literal[
    "ASSIGNMENT_READY",
    "NO_SHELTER_ALERT",
    "LOCATION_STALE_REMINDER",
    "SCENARIO_UPDATE",
    "GENERAL_ALERT",
]


class InAppNotificationResponse(BaseModel):
    id: int
    notification_type: NotificationType
    title: str
    body: str
    scenario_id: str | None = None
    metadata: dict[str, Any]
    created_at: datetime
    is_read: bool
    delivered_at: datetime | None = None
    read_at: datetime | None = None


class NotificationListResponse(BaseModel):
    notifications: list[InAppNotificationResponse]
    unread_count: int
    limit: int
    offset: int


class UnreadNotificationCountResponse(BaseModel):
    unread_count: int


class MarkNotificationReadResponse(BaseModel):
    notification_id: int
    is_read: bool
    read_at: datetime


class MarkAllNotificationsReadResponse(BaseModel):
    marked_read_count: int