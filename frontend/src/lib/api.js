const API_BASE = import.meta.env.VITE_API_BASE || "/api";

async function handleResponse(res) {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch (_) {
      /* ignore parse failure, fall back to statusText */
    }
    throw new Error(detail);
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