# Frontend — GIDS Shelter Recommendation Dashboard

The frontend is a responsive React dashboard built with Vite, Tailwind CSS, Recharts, Leaflet, and React Leaflet.

It does not implement disaster-analysis logic itself. It collects scenario input and displays data returned from the FastAPI backend and the existing Python Modules 1–6.

## Features

- Animated welcome page.
- Dashboard entry action.
- Scenario form with validation.
- Quick scenario presets.
- Disaster type selection.
- Live background-job progress display.
- Scenario history.
- Existing-scenario re-run action.
- Scenario delete action.
- Summary metrics.
- Interactive shelter map.
- Candidate and selected-shelter visualizations.
- Capacity and allocation chart.
- Dynamic radius-expansion chart.
- Tabbed recommendations table.
- Mobile, tablet, and desktop responsive layout.

## Required Structure

```text
frontend/
├── README.md
├── package.json
├── package-lock.json              # Generated after npm install
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

## Prerequisites

- Node.js 18 or later
- npm 9 or later
- Backend API running on `http://localhost:8000` during local development

Check versions:

```powershell
node --version
npm --version
```

## Installation

### Windows PowerShell

```powershell
cd frontend
npm install
```

Start the Vite development server:

```powershell
npm run dev
```

Open:

```text
http://localhost:5173
```

## Vite API Proxy

The development configuration proxies requests beginning with `/api` to the backend:

```text
Frontend URL: http://localhost:5173
Backend URL:  http://localhost:8000
API calls:    /api/*
```

Example frontend request:

```text
GET /api/scenarios
```

Vite forwards it to:

```text
http://localhost:8000/api/scenarios
```

This behavior is configured in `vite.config.js`.

## Build for Production

```powershell
npm run build
```

The static production files are generated in:

```text
frontend/dist/
```

Preview the production build locally:

```powershell
npm run preview
```

Do not commit `dist/`; it is generated output.

## Environment Configuration

The frontend uses this API base setting:

```js
const API_BASE = import.meta.env.VITE_API_BASE || "/api";
```

### Local development

No `.env` file is needed because Vite proxies `/api` to port `8000`.

### Deployed frontend

Create a `.env.production` file only when the deployed frontend uses a separate backend URL:

```text
VITE_API_BASE=https://your-backend-domain.example/api
```

Never put secrets in Vite environment variables. Values starting with `VITE_` are exposed to browser users.

## User Flow

1. The browser opens the animated welcome page.
2. The user selects **Open dashboard**.
3. The user enters a scenario or selects a quick preset.
4. The frontend sends `POST /api/scenarios`.
5. The backend returns a `job_id`.
6. The frontend polls `GET /api/jobs/{job_id}`.
7. After job status becomes `SUCCESS`, the frontend loads `GET /api/scenarios/{scenario_id}`.
8. The dashboard renders scenario summary, map, charts, and final recommendations.

## API Integration

All API calls are centralized in:

```text
src/lib/api.js
```

| Function | Endpoint | Purpose |
|---|---|---|
| `listScenarios()` | `GET /api/scenarios` | Load scenario history |
| `getScenario(id)` | `GET /api/scenarios/{id}` | Load complete scenario data |
| `createScenario(payload)` | `POST /api/scenarios` | Start Modules 1–6 |
| `rerunScenario(id)` | `POST /api/scenarios/rerun` | Start Modules 2–6 for existing scenario |
| `pollJob(jobId)` | `GET /api/jobs/{id}` | Monitor asynchronous job progress |
| `deleteScenario(id)` | `DELETE /api/scenarios/{id}` | Delete scenario data |

## Component Responsibilities

| Component | Responsibility |
|---|---|
| `WelcomePage.jsx` | First-screen onboarding and animated dashboard entry |
| `ScenarioForm.jsx` | Collects and validates the five required scenario fields |
| `PipelineProgress.jsx` | Shows queued/running/success/failed job state |
| `ScenarioHistory.jsx` | Lists historical scenarios and provides re-run/delete actions |
| `SummaryCards.jsx` | Shows key population, accommodation, capacity, and shelter values |
| `ShelterMap.jsx` | Shows epicenter, disaster radius, shelter search radius, and shelter markers |
| `ChartsPanel.jsx` | Visualizes recommendation mix, allocation, capacity, and expansion behavior |
| `RecommendationsTable.jsx` | Displays final shelter recommendations in tabs |
| `App.jsx` | Coordinates API calls, job polling, screen state, and layout |

## Tailwind CSS Setup

The application is configured for Tailwind CSS 3.x.

`tailwind.config.js` must scan JSX source files:

```js
content: [
  "./index.html",
  "./src/**/*.{js,jsx,ts,tsx}",
],
```

The CSS entry file must include:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### Verify Tailwind installation

```powershell
npm ls tailwindcss
```

Expected output includes:

```text
tailwindcss@3.x.x
```

### Verify the production build

```powershell
npm run build
```

If the build succeeds but the page appears as plain HTML, verify:

1. You are running commands from the same `frontend/` folder containing `package.json`.
2. `tailwind.config.js` contains the correct `content` array.
3. `postcss.config.js` contains the Tailwind plugin.
4. `src/main.jsx` imports `./index.css`.
5. You performed a hard browser reload with `Ctrl + Shift + R`.

## Clean Reinstall

Use this only if dependency installation or CSS processing becomes inconsistent:

```powershell
cd frontend
Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue
Remove-Item -Force package-lock.json -ErrorAction SilentlyContinue
npm cache verify
npm install
npm run dev
```

## Do Not Force Dependency Upgrades

Do not run this during normal development:

```powershell
npm audit fix --force
```

It may upgrade Vite, React, Tailwind, or chart libraries across breaking major versions.

The Recharts deprecation warning does not stop the current dashboard from functioning. Upgrade Recharts only as a separately tested future task.

## Browser Extension Console Messages

Messages mentioning `content.js`, screenshots, or capture events often come from browser extensions rather than your React project.

To test without extensions:

- Use an Incognito/InPrivate window with extensions disabled, or
- Use a separate browser profile.

## Git Policy

Do not commit generated dependencies or output:

```text
node_modules/
dist/
.env
.env.*
```

Commit these source files:

```text
package.json
package-lock.json
vite.config.js
tailwind.config.js
postcss.config.js
index.html
src/
```

## Responsive Design

The layout intentionally changes according to screen width:

- Mobile: one-column form, history, and results flow.
- Tablet: expanded cards and controls.
- Desktop: fixed/sticky left control area with full analysis workspace.
- Large screens: map and recommendation brief render side by side.

## Troubleshooting

### Page cannot call backend

Confirm backend is running:

```text
http://localhost:8000/api/health
```

Then restart Vite:

```powershell
npm run dev
```

### `404` in the browser console

Open Browser DevTools → Network → select the failed request. Check its Request URL.

If it starts with `chrome-extension://`, `moz-extension://`, or relates to screenshot/capture software, it is not part of this application.

### Map is blank

Check your internet connection because OpenStreetMap tile images are loaded from the public OpenStreetMap tile service.

### Welcome page does not show again

The application uses session storage. In the browser console, run:

```js
sessionStorage.removeItem("gids-welcome");
location.reload();
```