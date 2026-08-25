"""
api_server.py - FastAPI wrapper around the existing disaster evacuation pipeline.

This file does NOT modify main.py or any of the numbered pipeline modules
(1_identify_affected_population.py ... 6_generate_recommendation.py).

It imports main.py's functions directly and calls them with the 5 inputs
that the web dashboard collects from the user:

    DISASTER_TYPE, EPICENTER_NAME, EPICENTER_LAT, EPICENTER_LON, RADIUS_KM

Flow per request:
    1. Validate input payload.
    2. Set the 5 module-level constants on the imported main module for
       this run (main.py already reads these as globals -> Module 1
       receives them as function arguments exactly like the CLI script).
    3. Call main.run_module1() then main.run_module(2..6) exactly as
       `python main.py` does via run_pipeline().
    4. Read back the scenario JSON that Module 6 wrote and return it.

Existing-scenario re-run (Modules 2-6 only) is also exposed, matching
`python main.py --scenario <file>`.
"""

from __future__ import annotations

import glob
import importlib
import json
import os
import sys
import threading
import traceback
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator

# ----------------------------------------------------------------------
# PATHS
# ----------------------------------------------------------------------

BACKEND_ROOT = Path(__file__).resolve().parent
SCENARIOS_DIR = BACKEND_ROOT / "scenarios"
SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(BACKEND_ROOT))

# ----------------------------------------------------------------------
# IN-MEMORY JOB STORE
# ----------------------------------------------------------------------
# The pipeline (especially Module 4's radius expansion loop, which can
# re-run Modules 2/3 up to 5 times over a growing candidate set) can take
# a while on a large dataset. We run it in a background thread and let
# the frontend poll job status, so the UI never blocks or times out.

JOBS: dict[str, dict] = {}
JOBS_LOCK = threading.Lock()

VALID_DISASTER_TYPES = {"Flood", "Earthquake", "Fire", "Cyclone"}


def _set_job(job_id: str, **fields):
    with JOBS_LOCK:
        JOBS[job_id].update(fields)


# ----------------------------------------------------------------------
# REQUEST / RESPONSE MODELS
# ----------------------------------------------------------------------

class ScenarioRequest(BaseModel):
    disaster_type: str = Field(..., description="Flood, Earthquake, Fire, or Cyclone")
    epicenter_name: str = Field(..., min_length=1, max_length=120)
    epicenter_lat: float = Field(..., ge=-90, le=90)
    epicenter_lon: float = Field(..., ge=-180, le=180)
    radius_km: float = Field(..., gt=0, le=100)

    @validator("disaster_type")
    def check_disaster_type(cls, value):
        if value not in VALID_DISASTER_TYPES:
            raise ValueError(
                f"disaster_type must be one of {sorted(VALID_DISASTER_TYPES)}"
            )
        return value

    @validator("epicenter_name")
    def strip_name(cls, value):
        return value.strip()


class RerunRequest(BaseModel):
    scenario_id: str


class JobStatus(BaseModel):
    job_id: str
    status: str  # QUEUED | RUNNING | SUCCESS | FAILED
    scenario_id: Optional[str] = None
    error: Optional[str] = None
    progress: Optional[str] = None


# ----------------------------------------------------------------------
# PIPELINE EXECUTION
# ----------------------------------------------------------------------

_pipeline_lock = threading.Lock()
# The existing pipeline uses module-level constants (DISASTER_TYPE, etc.)
# and writes/reads a single Dataset1.xlsx + scenario files on disk.
# openpyxl reads are safe concurrently, but to avoid two runs colliding
# on main.py's globals we serialize pipeline execution with a lock.
# This matches how the original CLI script was designed to be run: once
# at a time, per scenario. It does NOT change any pipeline logic.


def _run_new_scenario(job_id: str, payload: ScenarioRequest):
    try:
        _set_job(job_id, status="RUNNING", progress="Starting pipeline")

        with _pipeline_lock:
            import main as pipeline_main
            importlib.reload(pipeline_main)

            # These are the exact 5 values main.py exposes as constants
            # and forwards into Module 1's run() signature unchanged.
            pipeline_main.DISASTER_TYPE = payload.disaster_type
            pipeline_main.EPICENTER_NAME = payload.epicenter_name
            pipeline_main.EPICENTER_LAT = payload.epicenter_lat
            pipeline_main.EPICENTER_LON = payload.epicenter_lon
            pipeline_main.RADIUS_KM = payload.radius_km

            _set_job(job_id, progress="Running Module 1")
            scenario_file = pipeline_main.run_module1()

            for number in range(2, 7):
                _set_job(job_id, progress=f"Running Module {number}")
                pipeline_main.run_module(number, scenario_file)

        scenario_id = Path(scenario_file).stem
        _set_job(job_id, status="SUCCESS", scenario_id=scenario_id, progress="Completed")

    except Exception as exc:  # noqa: BLE001
        _set_job(
            job_id,
            status="FAILED",
            error=f"{type(exc).__name__}: {exc}",
            progress=traceback.format_exc(),
        )


def _run_existing_scenario(job_id: str, scenario_id: str):
    try:
        _set_job(job_id, status="RUNNING", progress="Loading existing scenario")

        scenario_file = SCENARIOS_DIR / f"{scenario_id}.json"
        if not scenario_file.exists():
            raise FileNotFoundError(f"Scenario not found: {scenario_id}")

        with _pipeline_lock:
            import main as pipeline_main
            importlib.reload(pipeline_main)

            for number in range(2, 7):
                _set_job(job_id, progress=f"Running Module {number}")
                pipeline_main.run_module(number, scenario_file)

        _set_job(job_id, status="SUCCESS", scenario_id=scenario_id, progress="Completed")

    except Exception as exc:  # noqa: BLE001
        _set_job(
            job_id,
            status="FAILED",
            error=f"{type(exc).__name__}: {exc}",
            progress=traceback.format_exc(),
        )


# ----------------------------------------------------------------------
# FASTAPI APP
# ----------------------------------------------------------------------

app = FastAPI(
    title="GIDS Shelter Recommendation API",
    description=(
        "Wraps the existing 6-module disaster evacuation pipeline "
        "(Module 1: affected population -> Module 6: final recommendation) "
        "for the shelter dashboard frontend."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the deployed frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    dataset_ok = (BACKEND_ROOT / "Dataset1.xlsx").exists()
    runtime_ok = (BACKEND_ROOT / "runtime").exists()
    return {
        "status": "ok" if dataset_ok and runtime_ok else "degraded",
        "dataset_found": dataset_ok,
        "runtime_found": runtime_ok,
    }


@app.get("/api/meta/disaster-types")
def disaster_types():
    return {"disaster_types": sorted(VALID_DISASTER_TYPES)}


@app.post("/api/scenarios", response_model=JobStatus)
def create_scenario(payload: ScenarioRequest):
    """
    Kicks off Module 1 -> 6 for a brand-new scenario.
    Equivalent to: python main.py
    (with DISASTER_TYPE/EPICENTER_NAME/EPICENTER_LAT/EPICENTER_LON/RADIUS_KM
     taken from the request body instead of the hardcoded constants.)
    """
    job_id = str(uuid.uuid4())
    with JOBS_LOCK:
        JOBS[job_id] = {"job_id": job_id, "status": "QUEUED"}

    thread = threading.Thread(target=_run_new_scenario, args=(job_id, payload), daemon=True)
    thread.start()

    return JobStatus(job_id=job_id, status="QUEUED")


@app.post("/api/scenarios/rerun", response_model=JobStatus)
def rerun_scenario(payload: RerunRequest):
    """
    Re-runs Modules 2 -> 6 against an existing scenario JSON.
    Equivalent to: python main.py --scenario scenarios/<id>.json
    """
    job_id = str(uuid.uuid4())
    with JOBS_LOCK:
        JOBS[job_id] = {"job_id": job_id, "status": "QUEUED"}

    thread = threading.Thread(
        target=_run_existing_scenario, args=(job_id, payload.scenario_id), daemon=True
    )
    thread.start()

    return JobStatus(job_id=job_id, status="QUEUED")


@app.get("/api/jobs/{job_id}", response_model=JobStatus)
def get_job(job_id: str):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatus(**job)


@app.get("/api/scenarios")
def list_scenarios():
    """Lists all scenario JSON files, newest first, with lightweight summaries."""
    files = sorted(
        glob.glob(str(SCENARIOS_DIR / "*.json")),
        key=os.path.getmtime,
        reverse=True,
    )
    summaries = []
    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            scenario = data.get("Scenario", {})
            module6 = data.get("Modules", {}).get("Module6", {})
            summary = module6.get("final_recommendation", {}).get("scenario_summary", {})
            summaries.append(
                {
                    "scenario_id": scenario.get("ScenarioID", Path(file_path).stem),
                    "disaster_type": scenario.get("DisasterType"),
                    "epicenter": scenario.get("Epicenter"),
                    "disaster_radius_km": scenario.get("DisasterRadius_km"),
                    "has_final_recommendation": bool(module6),
                    "affected_population": summary.get("AffectedPopulation"),
                    "accommodation_percent": summary.get("PopulationAccommodationPercent"),
                }
            )
        except Exception:  # noqa: BLE001
            continue
    return {"scenarios": summaries}


@app.get("/api/scenarios/{scenario_id}")
def get_scenario(scenario_id: str):
    """Returns the full scenario JSON (all modules) for detailed drill-down."""
    scenario_file = SCENARIOS_DIR / f"{scenario_id}.json"
    if not scenario_file.exists():
        raise HTTPException(status_code=404, detail="Scenario not found")
    with open(scenario_file, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/scenarios/{scenario_id}/recommendation")
def get_recommendation(scenario_id: str):
    """Returns only Module 6's final_recommendation block - the dashboard's main payload."""
    scenario_file = SCENARIOS_DIR / f"{scenario_id}.json"
    if not scenario_file.exists():
        raise HTTPException(status_code=404, detail="Scenario not found")
    with open(scenario_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    module6 = data.get("Modules", {}).get("Module6")
    if not module6:
        raise HTTPException(
            status_code=409,
            detail="Module 6 has not completed for this scenario yet",
        )
    return module6


@app.delete("/api/scenarios/{scenario_id}")
def delete_scenario(scenario_id: str):
    scenario_file = SCENARIOS_DIR / f"{scenario_id}.json"
    if not scenario_file.exists():
        raise HTTPException(status_code=404, detail="Scenario not found")
    scenario_file.unlink()
    return {"deleted": scenario_id}