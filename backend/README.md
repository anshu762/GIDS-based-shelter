
# Backend — GIDS Shelter Recommendation API

This backend exposes the existing disaster evacuation pipeline through a FastAPI application.

It is a wrapper around the current pipeline. The pipeline files are not rewritten or replaced.

## Responsibilities

The backend:

- Validates scenario input from the dashboard.
- Starts a background pipeline job.
- Executes the existing Modules 1–6 in the required order.
- Returns job progress for frontend polling.
- Stores scenario JSON files in `scenarios/`.
- Serves full scenario data and final Module 6 recommendations.
- Supports re-running Modules 2–6 for an existing scenario.

## Required Structure

```text
backend/
├── api_server.py
├── main.py
├── requirements.txt
├── Dataset1.xlsx
├── runtime/
│   ├── 1_identify_affected_population.py
│   ├── 2_find_candidate_shelters.py
│   ├── 3_evaluate_candidate_shelters.py
│   ├── 4_select_shelters.py
│   ├── 5_rank_shelters.py
│   └── 6_generate_recommendation.py
└── scenarios/
```

### File placement is important

Your pipeline uses relative paths such as:

```python
EXCEL_FILE = "Dataset1.xlsx"
```

Therefore, start Uvicorn from the `backend/` directory. Do not start it from the repository root unless you first modify the path handling intentionally.

## Installation

### Windows PowerShell

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

When activation succeeds, the prompt starts with `(venv)`:

```text
(venv) PS ...\backend>
```

### Linux/macOS

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run the API

```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
```

Available URLs:

| URL | Purpose |
|---|---|
| `http://localhost:8000/docs` | Swagger UI API documentation |
| `http://localhost:8000/openapi.json` | OpenAPI schema |
| `http://localhost:8000/api/health` | Dataset/runtime health check |

## Health Check

Open:

```text
http://localhost:8000/api/health
```

Expected response:

```json
{
  "status": "ok",
  "dataset_found": true,
  "runtime_found": true
}
```

If `dataset_found` is false, place `Dataset1.xlsx` directly in the `backend/` folder.

If `runtime_found` is false, create the `runtime/` folder and place all six module files in it.

## Execution Model

### New scenario

The API receives input:

```json
{
  "disaster_type": "Flood",
  "epicenter_name": "Dharavi",
  "epicenter_lat": 19.050751,
  "epicenter_lon": 72.862396,
  "radius_km": 5
}
```

Then it executes:

```text
Module 1 → Module 2 → Module 3 → Module 4 → Module 5 → Module 6
```

The API returns a job ID immediately because Module 4 can perform dynamic radius expansion and may re-run Modules 2 and 3.

### Existing scenario re-run

The API receives:

```json
{
  "scenario_id": "Flood_Dharavi_5km_20260825_183000"
}
```

Then it executes:

```text
Module 2 → Module 3 → Module 4 → Module 5 → Module 6
```

This matches the existing CLI behavior:

```powershell
python main.py --scenario scenarios\Flood_Dharavi_5km_20260825_183000.json
```

## API Endpoints

### `GET /api/health`

Checks whether the dataset and runtime folder are available.

### `GET /api/meta/disaster-types`

Returns supported input values:

```json
{
  "disaster_types": [
    "Cyclone",
    "Earthquake",
    "Fire",
    "Flood"
  ]
}
```

### `POST /api/scenarios`

Creates a scenario and starts the full six-module pipeline.

Request body:

```json
{
  "disaster_type": "Cyclone",
  "epicenter_name": "Goregaon",
  "epicenter_lat": 19.155148,
  "epicenter_lon": 72.867851,
  "radius_km": 8
}
```

Response:

```json
{
  "job_id": "uuid-value",
  "status": "QUEUED",
  "scenario_id": null,
  "error": null,
  "progress": null
}
```

### `GET /api/jobs/{job_id}`

Polls a running job.

Possible values:

```text
QUEUED
RUNNING
SUCCESS
FAILED
```

When successful, the response includes `scenario_id`.

### `GET /api/scenarios`

Lists saved scenarios with lightweight summary information.

### `GET /api/scenarios/{scenario_id}`

Returns the complete scenario JSON, including all modules.

### `GET /api/scenarios/{scenario_id}/recommendation`

Returns Module 6 only. This is the primary payload used by the dashboard.

### `POST /api/scenarios/rerun`

Re-runs Modules 2–6 for an existing scenario.

### `DELETE /api/scenarios/{scenario_id}`

Deletes a generated scenario JSON file.

## Disaster-Type Validation

The API permits only:

```text
Flood
Earthquake
Fire
Cyclone
```

This protects Module 3 because it maps the input to one of:

```text
FloodSafe
EarthquakeSafe
FireSafe
CycloneSafe
```

An unsupported type is rejected at the API layer before the pipeline begins.

## Scenario Files

Scenario files are generated under:

```text
backend/scenarios/
```

They contain the original scenario details and all module results.

Generated scenario files are normally excluded from Git because they can be large and are runtime output. Keep an empty directory in Git with:

```text
backend/scenarios/.gitkeep
```

## Concurrency

The wrapper runs one pipeline execution at a time using a lock.

This is intentional because the existing pipeline uses mutable module-level values from `main.py` and writes JSON files to the shared `scenarios/` folder. The lock avoids overlap between simultaneous dashboard submissions without changing the original decision logic.

## Troubleshooting

### `source` is not recognized in PowerShell

Use:

```powershell
.\venv\Scripts\Activate.ps1
```

### Script execution is blocked

Run once in PowerShell as the current user:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then reopen PowerShell and run:

```powershell
.\venv\Scripts\Activate.ps1
```

### `Module 1 not found`

Confirm all module file names exactly match the names configured in `main.py`.

### `Master dataset not found`

Confirm the file is exactly named:

```text
Dataset1.xlsx
```

and is placed directly inside `backend/`.

### A job fails

Check:

1. The backend Uvicorn terminal output.
2. The API response from `GET /api/jobs/{job_id}`.
3. The module file names in `runtime/`.
4. The Excel sheet names required by the pipeline.

## Git Policy

Normally do not commit:

```text
venv/
scenarios/*.json
Dataset1.xlsx
.env
__pycache__/
```

Only commit the dataset if you have permission and it contains no restricted, private, or sensitive information.