import React from "react";

const STEPS = [
  { key: "Module 1", label: "Identify affected population" },
  { key: "Module 2", label: "Find candidate shelters" },
  { key: "Module 3", label: "Evaluate candidate shelters" },
  { key: "Module 4", label: "Select shelters (GIDS + allocation)" },
  { key: "Module 5", label: "Rank shelters" },
  { key: "Module 6", label: "Generate final recommendation" },
];

function currentStepIndex(progress) {
  if (!progress) return -1;
  for (let i = STEPS.length - 1; i >= 0; i -= 1) {
    if (progress.includes(STEPS[i].key)) return i;
  }
  return -1;
}

export default function PipelineProgress({ status, progress, error }) {
  const activeIndex = currentStepIndex(progress);

  return (
    <div className="animate-fadeIn rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-700">Pipeline status</h3>
        <span
          className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
            status === "SUCCESS"
              ? "bg-emerald-100 text-emerald-700"
              : status === "FAILED"
              ? "bg-red-100 text-red-700"
              : "bg-brand-100 text-brand-700"
          }`}
        >
          {status || "IDLE"}
        </span>
      </div>

      <ol className="space-y-2.5">
        {STEPS.map((step, index) => {
          const done = status === "SUCCESS" || index < activeIndex;
          const active = index === activeIndex && status === "RUNNING";
          return (
            <li key={step.key} className="flex items-center gap-3 text-sm">
              <span
                className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold transition-colors ${
                  done
                    ? "bg-emerald-500 text-white"
                    : active
                    ? "animate-pulse bg-brand-500 text-white"
                    : "bg-slate-200 text-slate-500"
                }`}
              >
                {done ? "\u2713" : index + 1}
              </span>
              <span className={done || active ? "font-medium text-slate-800" : "text-slate-400"}>
                {step.label}
              </span>
            </li>
          );
        })}
      </ol>

      {status === "FAILED" && error && (
        <div className="mt-4 rounded-lg bg-red-50 p-3 text-xs text-red-700">
          <p className="font-semibold">Pipeline error</p>
          <p className="mt-1 wrap-break-word font-mono">{error}</p>
        </div>
      )}
    </div>
  );
}