# GIDS-Based Shelter Recommendation Dashboard

A full-stack disaster evacuation decision-support application that converts a disaster scenario into a ranked, data-backed shelter recommendation plan.

The system accepts five scenario inputs:

- Disaster type
- Epicenter name
- Epicenter latitude
- Epicenter longitude
- Disaster radius in kilometres

It then executes the existing six-module Python pipeline to identify the affected population, discover and evaluate shelters, apply GIDS-based selection and capacity recovery, rank selected shelters, and generate an application-ready final recommendation.

> **Important:** The web application wraps the existing pipeline. It does not replace, rewrite, or change the evacuation logic, GIDS selection logic, allocation rules, radius expansion, or shelter-ranking rules.

---

## Contents

- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Pipeline Modules](#pipeline-modules)
- [Prerequisites](#prerequisites)
- [Backend Setup](#backend-setup)
- [Frontend Setup](#frontend-setup)
- [How to Use](#how-to-use)
- [API Reference](#api-reference)
- [Scenario Output](#scenario-output)
- [Git Workflow](#git-workflow)
- [Git Ignore Policy](#git-ignore-policy)
- [Troubleshooting](#troubleshooting)

---

## Features

### Disaster analysis

- Supports `Flood`, `Earthquake`, `Fire`, and `Cyclone` scenarios.
- Uses latitude, longitude, and a disaster radius to find affected population nodes.
- Aggregates affected population and locality information from the Excel dataset.

### Shelter intelligence

- Finds candidate shelters within the search radius.
- Evaluates building types using the **Building Type Master** worksheet.
- Applies disaster-specific safety rules such as `FloodSafe`, `EarthquakeSafe`, `FireSafe`, and `CycloneSafe`.
- Uses GIDS geographic-independence selection and capacity-recovery selection.
- Allocates affected population to selected shelters based on coverage and available capacity.
- Expands the shelter search radius dynamically when allocation remains incomplete.
- Produces deterministic multi-criteria shelter rankings.

### Dashboard

- Animated welcome screen.
- Responsive scenario-input form with quick presets.
- Live pipeline progress for Modules 1–6.
- Scenario history, re-run, and delete actions.
- Summary KPI cards.
- Interactive map with epicenter, disaster radius, search radius, and recommended shelters.
- Shelter capacity and allocation charts.
- Tabbed shelter recommendations: top, primary/GIDS, supplementary, and medical-capable.

---

## Architecture

```text
React + Vite Dashboard
        |
        | HTTP requests through /api proxy
        v
FastAPI Wrapper (api_server.py)
        |
        | calls existing Python functions without changing them
        v
main.py
        |
        +--> Module 1: Identify affected population
        +--> Module 2: Find candidate shelters
        +--> Module 3: Evaluate shelter suitability
        +--> Module 4: GIDS selection, allocation, radius expansion
        +--> Module 5: Shelter ranking
        +--> Module 6: Final recommendation payload
        |
        v
Dataset1.xlsx + scenarios/*.json
```

The frontend communicates only with the FastAPI endpoints. The API invokes the existing pipeline in the existing module order.

---

## Project Structure

```text
GIDS-based-shelter/
├── README.md
├── .gitignore
├── backend/
│   ├── README.md
│   ├── api_server.py
│   ├── main.py
│   ├── requirements.txt
│   ├── Dataset1.xlsx                 # Local dataset; normally ignored by Git
│   ├── runtime/
│   │   ├── 1_identify_affected_population.py
│   │   ├── 2_find_candidate_shelters.py
│   │   ├── 3_evaluate_candidate_shelters.py
│   │   ├── 4_select_shelters.py
│   │   ├── 5_rank_shelters.py
│   │   └── 6_generate_recommendation.py
│   └── scenarios/                    # Generated JSON scenario output; ignored by Git
└── frontend/
    ├── README.md
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── index.html
    └── src/
        ├── main.jsx
        ├── index.css
        ├── App.jsx
        ├── lib/
        │   └── api.js
        └── components/
            ├── WelcomePage.jsx
            ├── ScenarioForm.jsx
            ├── PipelineProgress.jsx
            ├── ScenarioHistory.jsx
            ├── SummaryCards.jsx
            ├── ShelterMap.jsx
            ├── ChartsPanel.jsx
            └── RecommendationsTable.jsx
```

---

## Pipeline Modules

| Module | File | Responsibility | Output written to scenario JSON |
|---|---|---|---|
| 1 | `1_identify_affected_population.py` | Finds population nodes and localities inside the disaster radius | `Modules.Module1` |
| 2 | `2_find_candidate_shelters.py` | Finds shelter candidates within the shelter search radius | `Modules.Module2` |
| 3 | `3_evaluate_candidate_shelters.py` | Checks building-type safety for the selected disaster type | `Modules.Module3` |
| 4 | `4_select_shelters.py` | GIDS selection, capacity recovery, allocation, dynamic radius expansion | `Modules.Module4` |
| 5 | `5_rank_shelters.py` | Deterministic hierarchical ranking of selected shelters | `Modules.Module5` |
| 6 | `6_generate_recommendation.py` | Produces a concise dashboard-readable final recommendation | `Modules.Module6` |

Module 4 owns dynamic radius expansion. When required, it updates `ShelterSearchRadius_km` and re-runs Modules 2 and 3 internally.

---

## Prerequisites

Install the following before setup:

- Python 3.11 or later
- Node.js 18 or later
- npm 9 or later
- Git

Verify installation:

```powershell
python --version
node --version
npm --version
git --version
```

---

## Backend Setup

See the detailed backend documentation in [`backend/README.md`](backend/README.md).

### Windows PowerShell quick start

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
```

The API should be available at:

```text
http://localhost:8000
```

Swagger documentation is available at:

```text
http://localhost:8000/docs
```

Health check:

```text
http://localhost:8000/api/health
```

Expected result when files are placed correctly:

```json
{
  "status": "ok",
  "dataset_found": true,
  "runtime_found": true
}
```

---

## Frontend Setup

See the detailed frontend documentation in [`frontend/README.md`](frontend/README.md).

### Windows PowerShell quick start

Open a separate terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the dashboard at:

```text
http://localhost:5173
```

During development, Vite proxies frontend requests beginning with `/api` to:

```text
http://localhost:8000
```

The backend must be running before you submit or load a scenario.

---

## How to Use

1. Start the backend on port `8000`.
2. Start the frontend on port `5173`.
3. Open `http://localhost:5173`.
4. On the welcome screen, select **Open dashboard**.
5. Choose a quick preset or enter:
   - Disaster type
   - Epicenter name
   - Latitude
   - Longitude
   - Disaster radius in km
6. Select **Run evacuation analysis**.
7. The frontend creates an API job and polls its status.
8. The backend runs Modules 1 through 6.
9. After completion, review the dashboard results.
10. Select previous scenarios from **Scenario history** to view them again.

### Existing scenario re-run

The **Re-run** button uses the existing scenario JSON and runs Modules 2–6 again. This is equivalent to:

```powershell
python main.py --scenario scenarios\YOUR_SCENARIO.json
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Confirms that `Dataset1.xlsx` and `runtime/` are available |
| `GET` | `/api/meta/disaster-types` | Returns supported disaster types |
| `POST` | `/api/scenarios` | Creates a new scenario job and runs Modules 1–6 |
| `POST` | `/api/scenarios/rerun` | Re-runs Modules 2–6 for an existing scenario |
| `GET` | `/api/jobs/{job_id}` | Returns job status and progress |
| `GET` | `/api/scenarios` | Lists stored scenarios and lightweight summaries |
| `GET` | `/api/scenarios/{scenario_id}` | Returns the full scenario JSON with all module data |
| `GET` | `/api/scenarios/{scenario_id}/recommendation` | Returns Module 6 final recommendation payload |
| `DELETE` | `/api/scenarios/{scenario_id}` | Deletes a generated scenario JSON file |

### Create scenario request

```json
{
  "disaster_type": "Cyclone",
  "epicenter_name": "Goregaon",
  "epicenter_lat": 19.155148,
  "epicenter_lon": 72.867851,
  "radius_km": 8
}
```

Allowed disaster types:

```text
Flood
Earthquake
Fire
Cyclone
```

---

## Scenario Output

Each completed run creates a JSON file in:

```text
backend/scenarios/
```

Example file name:

```text
Cyclone_Goregaon_8km_20260825_183000.json
```

The final dashboard payload is produced by:

```text
Modules.Module6.final_recommendation
```

It contains:

```text
scenario_summary
recommendation_message
top_recommendations
primary_recommendations
supplementary_recommendations
medical_recommendations
```

---

## Git Workflow

Use separate commits for logical changes. This makes it easy to understand what changed, review work, and revert safely.

### Recommended commit sequence

```powershell
# 1. Repository foundation
git add .gitignore README.md backend/README.md frontend/README.md
git commit -m "docs: add project documentation and Git ignore rules"

# 2. Existing evacuation pipeline
git add backend/main.py backend/runtime/
git commit -m "feat(pipeline): add six-module shelter recommendation pipeline"

# 3. Backend API wrapper
git add backend/api_server.py backend/requirements.txt
git commit -m "feat(api): add FastAPI wrapper for evacuation pipeline"

# 4. Frontend application scaffold
git add frontend/package.json frontend/vite.config.js frontend/tailwind.config.js frontend/postcss.config.js frontend/index.html frontend/src/main.jsx frontend/src/index.css frontend/src/lib/api.js
git commit -m "feat(frontend): add Vite React and Tailwind application scaffold"

# 5. Dashboard components
git add frontend/src/App.jsx frontend/src/components/
git commit -m "feat(dashboard): add responsive GIDS shelter analysis dashboard"

# 6. Optional tracked public sample data only
git add backend/scenarios/.gitkeep
git commit -m "chore: preserve generated scenario directory"
```

### Push a fresh repository

After creating the new GitHub repository, run this from the project root:

```powershell
git init
git branch -M main
git add .gitignore README.md backend frontend
git commit -m "chore: initialize GIDS shelter recommendation dashboard"
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPOSITORY_NAME.git
git push -u origin main
```

If you are using SSH instead of HTTPS:

```powershell
git remote add origin git@github.com:YOUR_GITHUB_USERNAME/YOUR_REPOSITORY_NAME.git
git push -u origin main
```

---

## Git Ignore Policy

Do **not** commit these files unless your team explicitly agrees that they contain only safe, public, non-sensitive data:

- Python virtual environment: `backend/venv/`
- Node dependencies: `frontend/node_modules/`
- Built frontend files: `frontend/dist/`
- Runtime scenario output: `backend/scenarios/*.json`
- Excel dataset: `backend/Dataset1.xlsx`
- Environment files: `.env`
- Python cache and local editor files

The included `.gitignore` reflects this policy.

If the Excel dataset is public and intentionally version-controlled, remove this line from `.gitignore`:

```text
backend/Dataset1.xlsx
```

If you need to share the dataset privately, use a secure storage service and document how authorized users can obtain it.

---

## Troubleshooting

### Backend imports fail

Confirm you are starting Uvicorn from the `backend` folder:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn api_server:app --reload --port 8000
```

### PowerShell does not recognize `source`

Use Windows activation syntax:

```powershell
.\venv\Scripts\Activate.ps1
```

Do not use this Unix/macOS command in PowerShell:

```bash
source venv/bin/activate
```

### Frontend API calls fail

Confirm both services are running:

```text
Frontend: http://localhost:5173
Backend:  http://localhost:8000
```

Then open:

```text
http://localhost:8000/api/health
```

### Tailwind page appears unstyled

Verify you are running commands from the directory that contains:

```text
frontend/package.json
frontend/tailwind.config.js
frontend/postcss.config.js
frontend/src/
```

Then run:

```powershell
cd frontend
npm run build
npm run dev
```

### Do not use forced audit upgrades during development

Avoid this command until the project is stable and dependencies have been tested:

```powershell
npm audit fix --force
```

It can install breaking major-version upgrades.

---

## License

Add an appropriate license before publishing or sharing this repository publicly.