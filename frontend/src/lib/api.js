// Normalize VITE_API_BASE so it always ends with exactly one "/api",
// regardless of whether the Railway variable was set to:
//   https://backend.up.railway.app
//   https://backend.up.railway.app/
//   https://backend.up.railway.app/api
//   https://backend.up.railway.app/api/
// This prevents requests silently hitting the wrong path (which returns
// Railway/FastAPI's HTML fallback instead of JSON) if the env var is ever
// misconfigured again.
function resolveApiBase() {
  const raw = (import.meta.env.VITE_API_BASE || "/api").trim();
  const withoutTrailingSlash = raw.replace(/\/+$/, "");
  return withoutTrailingSlash.endsWith("/api")
    ? withoutTrailingSlash
    : `${withoutTrailingSlash}/api`;
}

const API_BASE = resolveApiBase();

async function handleResponse(res) {
  const contentType = res.headers.get("content-type") || "";
  const isJson = contentType.toLowerCase().includes("application/json");

  if (!res.ok) {
    let detail = res.statusText;
    if (isJson) {
      try {
        const body = await res.json();
        detail = body.detail || JSON.stringify(body);
      } catch (_) {
        /* ignore parse failure, fall back to statusText */
      }
    }
    throw new Error(`${detail} (requested ${res.url})`);
  }

  if (!isJson) {
    // The server responded 200 OK but did not send JSON. This almost
    // always means the request hit a static file / SPA fallback route
    // instead of the FastAPI backend - i.e. API_BASE is misconfigured.
    const text = await res.text();
    const preview = text.replace(/\s+/g, " ").slice(0, 160);
    throw new Error(
      `Expected JSON from ${res.url} but got "${contentType || "unknown"}". ` +
      `Check VITE_API_BASE - it must point at the backend's /api path. Response preview: ${preview}`
    );
  }

  return res.json();
}

export async function fetchDisasterTypes() {
  const res = await fetch(`${API_BASE}/meta/disaster-types`);
  return handleResponse(res);
}

export async function createScenario(payload) {
  const res = await fetch(`${API_BASE}/scenarios`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse(res);
}

export async function rerunScenario(scenarioId) {
  const res = await fetch(`${API_BASE}/scenarios/rerun`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scenario_id: scenarioId }),
  });
  return handleResponse(res);
}

export async function getJob(jobId) {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`);
  return handleResponse(res);
}

export async function listScenarios() {
  const res = await fetch(`${API_BASE}/scenarios`);
  return handleResponse(res);
}

export async function getScenario(scenarioId) {
  const res = await fetch(`${API_BASE}/scenarios/${scenarioId}`);
  return handleResponse(res);
}

export async function getRecommendation(scenarioId) {
  const res = await fetch(`${API_BASE}/scenarios/${scenarioId}/recommendation`);
  return handleResponse(res);
}

export async function deleteScenario(scenarioId) {
  const res = await fetch(`${API_BASE}/scenarios/${scenarioId}`, {
    method: "DELETE",
  });
  return handleResponse(res);
}

export async function pollJob(jobId, { intervalMs = 1500, onTick, maxAttempts = 240 } = {}) {
  let attempts = 0;
  while (attempts < maxAttempts) {
    const job = await getJob(jobId);
    if (onTick) onTick(job);
    if (job.status === "SUCCESS" || job.status === "FAILED") {
      return job;
    }
    attempts += 1;
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
  throw new Error("Timed out waiting for the pipeline to finish. Check backend logs.");
}





























// const API_BASE = import.meta.env.VITE_API_BASE || "/api";

// async function handleResponse(res) {
//   if (!res.ok) {
//     let detail = res.statusText;
//     try {
//       const body = await res.json();
//       detail = body.detail || JSON.stringify(body);
//     } catch (_) {
//       /* ignore parse failure, fall back to statusText */
//     }
//     throw new Error(detail);
//   }
//   return res.json();
// }

// export async function fetchDisasterTypes() {
//   const res = await fetch(`${API_BASE}/meta/disaster-types`);
//   return handleResponse(res);
// }

// export async function createScenario(payload) {
//   const res = await fetch(`${API_BASE}/scenarios`, {
//     method: "POST",
//     headers: { "Content-Type": "application/json" },
//     body: JSON.stringify(payload),
//   });
//   return handleResponse(res);
// }

// export async function rerunScenario(scenarioId) {
//   const res = await fetch(`${API_BASE}/scenarios/rerun`, {
//     method: "POST",
//     headers: { "Content-Type": "application/json" },
//     body: JSON.stringify({ scenario_id: scenarioId }),
//   });
//   return handleResponse(res);
// }

// export async function getJob(jobId) {
//   const res = await fetch(`${API_BASE}/jobs/${jobId}`);
//   return handleResponse(res);
// }

// export async function listScenarios() {
//   const res = await fetch(`${API_BASE}/scenarios`);
//   return handleResponse(res);
// }

// export async function getScenario(scenarioId) {
//   const res = await fetch(`${API_BASE}/scenarios/${scenarioId}`);
//   return handleResponse(res);
// }

// export async function getRecommendation(scenarioId) {
//   const res = await fetch(`${API_BASE}/scenarios/${scenarioId}/recommendation`);
//   return handleResponse(res);
// }

// export async function deleteScenario(scenarioId) {
//   const res = await fetch(`${API_BASE}/scenarios/${scenarioId}`, {
//     method: "DELETE",
//   });
//   return handleResponse(res);
// }

// export async function pollJob(jobId, { intervalMs = 1500, onTick, maxAttempts = 240 } = {}) {
//   let attempts = 0;
//   while (attempts < maxAttempts) {
//     const job = await getJob(jobId);
//     if (onTick) onTick(job);
//     if (job.status === "SUCCESS" || job.status === "FAILED") {
//       return job;
//     }
//     attempts += 1;
//     await new Promise((resolve) => setTimeout(resolve, intervalMs));
//   }
//   throw new Error("Timed out waiting for the pipeline to finish. Check backend logs.");
// }