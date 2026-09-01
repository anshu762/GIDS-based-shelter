"""Read-only access to completed Module 6 recommendation scenario files.

This service never changes scenario JSON and never re-runs pipeline modules.
It only reads Module 6 data already produced by the existing pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path


def _load_json(path: Path) -> dict | None:
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return None


def _has_completed_module6(data: dict | None) -> bool:
    return bool(
        data
        and data.get("Modules", {})
        .get("Module6", {})
        .get("final_recommendation")
    )


def load_completed_scenario(
    scenarios_dir: Path,
    scenario_id: str | None = None,
) -> dict | None:
    """Load one completed scenario, or the newest completed one by mtime.

    `scenario_id` is strictly treated as a filename stem. A malicious path
    (e.g. ../../file) is rejected before any file access.
    """
    if scenario_id is not None:
        if (
            not scenario_id
            or Path(scenario_id).name != scenario_id
            or "/" in scenario_id
            or "\\" in scenario_id
        ):
            return None

        path = scenarios_dir / f"{scenario_id}.json"
        data = _load_json(path)
        return data if _has_completed_module6(data) else None

    candidates: list[tuple[float, dict]] = []
    for path in scenarios_dir.glob("*.json"):
        data = _load_json(path)
        if _has_completed_module6(data):
            try:
                candidates.append((path.stat().st_mtime, data))
            except OSError:
                continue

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def extract_ranked_shelters(scenario_data: dict) -> list[dict]:
    """Return Module 6's normalized recommendations, preferring all ranked data.

    Module 6's `top_recommendations` intentionally contains only 20 shelters.
    For a device-specific nearest calculation, use Module 5's `ranked_shelters`
    when available so the nearest valid selected shelter is not accidentally
    excluded merely because it is outside the dashboard top-20 list.
    """
    modules = scenario_data.get("Modules", {})
    module5 = modules.get("Module5", {})
    ranked = module5.get("ranked_shelters", [])

    if isinstance(ranked, list) and ranked:
        return ranked

    module6 = modules.get("Module6", {})
    recommendation = module6.get("final_recommendation", {})
    top = recommendation.get("top_recommendations", [])
    return top if isinstance(top, list) else []


def scenario_id_from_data(scenario_data: dict) -> str | None:
    value = scenario_data.get("Scenario", {}).get("ScenarioID")
    return str(value) if value else None