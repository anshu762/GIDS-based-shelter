-- ============================================================
-- GIDS Mobile API - Phase 2 additive PostgreSQL migration
-- ============================================================
-- This migration creates a separate `mobile` schema only.
-- It does not change Dataset1.xlsx, scenario JSON files, main.py,
-- or any of the six existing pipeline modules.
-- Safe to execute repeatedly.

CREATE SCHEMA IF NOT EXISTS mobile;

CREATE TABLE IF NOT EXISTS mobile.devices (
    device_id UUID PRIMARY KEY,
    platform TEXT NOT NULL CHECK (platform = 'android'),
    app_version TEXT NOT NULL,
    fcm_token TEXT NULL,
    registered_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS mobile.device_locations (
    device_id UUID PRIMARY KEY
        REFERENCES mobile.devices(device_id) ON DELETE CASCADE,
    latitude DOUBLE PRECISION NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude DOUBLE PRECISION NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    accuracy_m DOUBLE PRECISION NOT NULL CHECK (accuracy_m >= 0),
    captured_at TIMESTAMPTZ NOT NULL,
    stored_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- This stores only the latest destination-selection result for each device.
-- It is NOT a capacity reservation and never changes Module 4 values.
CREATE TABLE IF NOT EXISTS mobile.device_assignments (
    device_id UUID PRIMARY KEY
        REFERENCES mobile.devices(device_id) ON DELETE CASCADE,
    scenario_id TEXT NULL,
    assignment_status TEXT NOT NULL CHECK (
        assignment_status IN (
            'ASSIGNED',
            'NO_LOCATION',
            'STALE_LOCATION',
            'NO_SCENARIO',
            'NO_ELIGIBLE_SHELTER'
        )
    ),
    shelter_id TEXT NULL,
    shelter_name TEXT NULL,
    shelter_latitude DOUBLE PRECISION NULL,
    shelter_longitude DOUBLE PRECISION NULL,
    distance_km DOUBLE PRECISION NULL,
    recommendation_tier TEXT NULL,
    recommendation_rank INTEGER NULL,
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Acknowledgments are intentionally append-only because they are discrete
-- user actions, not high-frequency location history.
CREATE TABLE IF NOT EXISTS mobile.assignment_acknowledgments (
    id BIGSERIAL PRIMARY KEY,
    device_id UUID NOT NULL
        REFERENCES mobile.devices(device_id) ON DELETE CASCADE,
    scenario_id TEXT NOT NULL,
    shelter_id TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('ACKNOWLEDGED', 'DISMISSED', 'NAVIGATING')),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_mobile_acknowledgments_device
    ON mobile.assignment_acknowledgments (device_id);

CREATE INDEX IF NOT EXISTS idx_mobile_acknowledgments_scenario
    ON mobile.assignment_acknowledgments (scenario_id);

CREATE OR REPLACE FUNCTION mobile.set_device_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_mobile_devices_updated_at ON mobile.devices;

CREATE TRIGGER trg_mobile_devices_updated_at
    BEFORE UPDATE ON mobile.devices
    FOR EACH ROW
    EXECUTE FUNCTION mobile.set_device_updated_at();

-- ============================================================
-- GIDS In-App Notification Inbox
-- ============================================================

CREATE TABLE IF NOT EXISTS mobile.notifications (
    id BIGSERIAL PRIMARY KEY,
    notification_type TEXT NOT NULL CHECK (
        notification_type IN (
            'ASSIGNMENT_READY',
            'NO_SHELTER_ALERT',
            'LOCATION_STALE_REMINDER',
            'SCENARIO_UPDATE',
            'GENERAL_ALERT'
        )
    ),
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    scenario_id TEXT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Exactly one automatic SCENARIO_UPDATE per scenario ID.
CREATE UNIQUE INDEX IF NOT EXISTS uq_mobile_scenario_update_once
    ON mobile.notifications (scenario_id)
    WHERE notification_type = 'SCENARIO_UPDATE'
      AND scenario_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_mobile_notifications_created_at
    ON mobile.notifications (created_at DESC);

CREATE TABLE IF NOT EXISTS mobile.device_notifications (
    device_id UUID NOT NULL
        REFERENCES mobile.devices(device_id) ON DELETE CASCADE,
    notification_id BIGINT NOT NULL
        REFERENCES mobile.notifications(id) ON DELETE CASCADE,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    delivered_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    read_at TIMESTAMPTZ NULL,
    PRIMARY KEY (device_id, notification_id)
);

CREATE INDEX IF NOT EXISTS idx_mobile_device_notifications_unread
    ON mobile.device_notifications (device_id, is_read);