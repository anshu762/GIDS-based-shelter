"""Automatic, best-effort scenario update notifications for GIDS.

Called only after an existing pipeline job completed all Modules 1-6
successfully. It reads the final scenario JSON; it never changes it.

A database failure here is intentionally logged and swallowed by the caller:
notification delivery must never turn a successful pipeline job into FAILED.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from mobile.notification_repository import create_scenario_update_once

logger = logging.getLogger(__name__)


def _safe_int(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _safe_float(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def create_completed_scenario_notification(scenario_file: str | Path) -> int | None:
    """Create one in-app SCENARIO_UPDATE alert from completed Module 6 data.

    Returns an ID when newly created, None when an identical scenario update
    was already created. Raises for invalid/unfinished scenario data; caller
    handles that safely as best-effort post-processing.
    """
    scenario_path = Path(scenario_file)

    with scenario_path.open("r", encoding="utf-8") as file:
        scenario_data = json.load(file)

    scenario = scenario_data.get("Scenario", {})
    module4 = scenario_data.get("Modules", {}).get("Module4", {})
    module6 = scenario_data.get("Modules", {}).get("Module6", {})
    final_recommendation = module6.get("final_recommendation", {})
    summary = final_recommendation.get("scenario_summary", {})

    scenario_id = str(scenario.get("ScenarioID") or "").strip()
    disaster_type = str(scenario.get("DisasterType") or "Disaster").strip()
    epicenter = str(scenario.get("Epicenter") or "the affected area").strip()

    if not scenario_id:
        raise ValueError("Completed scenario notification requires Scenario.ScenarioID")

    if not final_recommendation:
        raise ValueError("Module 6 final_recommendation is required before notification")

    affected_population = _safe_int(summary.get("AffectedPopulation"))
    accommodation_percent = _safe_float(
        summary.get("PopulationAccommodationPercent")
    )
    module4_status = str(module4.get("status") or "").strip()

    title = "New evacuation update available"

    if module4_status == "CAPACITY_INSUFFICIENT":
        body = (
            f"{disaster_type} guidance for {epicenter} is available, but "
            "available shelter capacity may be insufficient. Follow official "
            "instructions and open GIDS Evacuation for your nearest shelter."
        )
    elif affected_population > 0:
        body = (
            f"{disaster_type} guidance for {epicenter} is ready. Shelter "
            f"recommendations are available for {affected_population:,} affected people."
        )
    else:
        body = (
            f"{disaster_type} guidance for {epicenter} is ready. Open GIDS "
            "Evacuation to check your nearest suitable shelter."
        )

    metadata = {
        "scenario_id": scenario_id,
        "disaster_type": disaster_type,
        "epicenter": epicenter,
        "module4_status": module4_status,
        "affected_population": affected_population,
        "population_accommodation_percent": accommodation_percent,
        "notification_data_type": "scenario_update",
    }

    notification_id = create_scenario_update_once(
        title=title,
        body=body,
        scenario_id=scenario_id,
        metadata=metadata,
    )

    if notification_id is not None:
        logger.info(
            "Created automatic scenario update notification id=%s scenario_id=%s",
            notification_id,
            scenario_id,
        )

    return notification_id