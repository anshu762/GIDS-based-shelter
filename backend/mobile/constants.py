"""Constants for the additive GIDS mobile API layer.

These values implement the Phase 1 decisions. They are intentionally kept
outside main.py and runtime/ so the existing Modules 1-6 stay untouched.
"""

from datetime import timedelta

# A location is FRESH only when age is strictly less than this threshold.
# At exactly 5 minutes, it is considered STALE_LOCATION.
LOCATION_FRESHNESS = timedelta(minutes=5)

# GPS readings less than or equal to this value are considered accurate.
# Readings above it are stored but returned as LOW_ACCURACY.
LOCATION_ACCURACY_THRESHOLD_M = 100.0

# Endpoint /api/mobile/shelters/nearest clamps user input into this range.
NEAREST_SHELTER_MIN_LIMIT = 1
NEAREST_SHELTER_MAX_LIMIT = 20

ANDROID_PLATFORM = "android"

ASSIGNMENT_ASSIGNED = "ASSIGNED"
ASSIGNMENT_NO_LOCATION = "NO_LOCATION"
ASSIGNMENT_STALE_LOCATION = "STALE_LOCATION"
ASSIGNMENT_NO_SCENARIO = "NO_SCENARIO"
ASSIGNMENT_NO_ELIGIBLE_SHELTER = "NO_ELIGIBLE_SHELTER"
ASSIGNMENT_OUTSIDE_DISASTER_AREA = "OUTSIDE_DISASTER_AREA"

ASSIGNMENT_STATUSES = {
    ASSIGNMENT_ASSIGNED,
    ASSIGNMENT_NO_LOCATION,
    ASSIGNMENT_STALE_LOCATION,
    ASSIGNMENT_NO_SCENARIO,
    ASSIGNMENT_NO_ELIGIBLE_SHELTER,
    ASSIGNMENT_OUTSIDE_DISASTER_AREA,
}

ACKNOWLEDGMENT_ACTIONS = {
    "ACKNOWLEDGED",
    "DISMISSED",
    "NAVIGATING",
}

MESSAGE_NO_LOCATION = (
    "We don't have your location yet. Please allow location access and try again."
)
MESSAGE_STALE_LOCATION = (
    "Your last known location is more than 5 minutes old. "
    "Please reopen the app to refresh your location."
)
MESSAGE_NO_SCENARIO = (
    "No active evacuation scenario is available right now. Please check back shortly."
)
MESSAGE_NO_ELIGIBLE_SHELTER = (
    "No suitable shelter was found near your current location for this event. "
    "Please follow official evacuation broadcasts."
)

MESSAGE_OUTSIDE_DISASTER_AREA = (
    "That disaster does not affect your current area. No action is required."
)