"""Pydantic request and response models for /api/mobile endpoints.

These models are isolated from the existing ScenarioRequest, RerunRequest,
and JobStatus models in api_server.py. They do not alter dashboard APIs.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from mobile.constants import ACKNOWLEDGMENT_ACTIONS, ANDROID_PLATFORM


class DeviceRegistrationRequest(BaseModel):
    device_id: UUID
    platform: str = Field(..., min_length=1, max_length=30)
    app_version: str = Field(..., min_length=1, max_length=50)
    fcm_token: str | None = Field(default=None, max_length=4096)

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized != ANDROID_PLATFORM:
            raise ValueError("platform must be 'android' for this release")
        return normalized

    @field_validator("app_version")
    @classmethod
    def normalize_app_version(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("app_version must not be empty")
        return value

    @field_validator("fcm_token")
    @classmethod
    def normalize_optional_token(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class DeviceRegistrationResponse(BaseModel):
    device_id: UUID
    registered_at: datetime
    status: Literal["REGISTERED"]


class LocationUpdateRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy_m: float = Field(..., ge=0, le=100000)
    captured_at: datetime


class LocationUpdateResponse(BaseModel):
    device_id: UUID
    accepted: bool
    accuracy_status: Literal["OK", "LOW_ACCURACY"]
    stored_at: datetime


class LocationUsedResponse(BaseModel):
    latitude: float
    longitude: float
    accuracy_m: float
    captured_at: datetime
    freshness_status: Literal["FRESH", "STALE"]


class ShelterResponse(BaseModel):
    shelter_id: str
    shelter_name: str
    building_type: str | None = None
    locality: str | None = None
    latitude: float
    longitude: float
    distance_km: float
    recommendation_tier: str | None = None
    recommendation_rank: int | None = None
    medical_facility: str | None = None


class AssignmentResponse(BaseModel):
    device_id: UUID
    scenario_id: str | None = None
    assignment_status: Literal[
        "ASSIGNED",
        "NO_LOCATION",
        "STALE_LOCATION",
        "NO_SCENARIO",
        "NO_ELIGIBLE_SHELTER",
        "OUTSIDE_DISASTER_AREA",
    ]
    location_used: LocationUsedResponse | None = None
    shelter: ShelterResponse | None = None
    evaluated_at: datetime
    message: str | None = None


class AssignmentAcknowledgeRequest(BaseModel):
    scenario_id: str = Field(..., min_length=1, max_length=255)
    shelter_id: str = Field(..., min_length=1, max_length=255)
    action: str = Field(..., min_length=1, max_length=30)

    @field_validator("scenario_id", "shelter_id")
    @classmethod
    def normalize_required_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be empty")
        return value

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in ACKNOWLEDGMENT_ACTIONS:
            allowed = ", ".join(sorted(ACKNOWLEDGMENT_ACTIONS))
            raise ValueError(f"action must be one of {allowed}")
        return normalized


class AssignmentAcknowledgeResponse(BaseModel):
    device_id: UUID
    recorded: bool
    action: Literal["ACKNOWLEDGED", "DISMISSED", "NAVIGATING"]
    recorded_at: datetime


class NearestSheltersResponse(BaseModel):
    device_id: UUID
    scenario_id: str | None = None
    assignment_status: Literal[
        "ASSIGNED",
        "NO_LOCATION",
        "STALE_LOCATION",
        "NO_SCENARIO",
        "NO_ELIGIBLE_SHELTER",
        "OUTSIDE_DISASTER_AREA",
    ]
    location_used: LocationUsedResponse | None = None
    shelters: list[ShelterResponse]
    evaluated_at: datetime
    message: str | None = None


class NotificationTokenRequest(BaseModel):
    fcm_token: str = Field(..., min_length=1, max_length=4096)

    @field_validator("fcm_token")
    @classmethod
    def validate_token(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("fcm_token must not be empty")
        return value


class NotificationTokenResponse(BaseModel):
    device_id: UUID
    token_updated: bool
    updated_at: datetime