import React from "react";

export default function ScenarioHistory({ scenarios, activeScenarioId, onSelect, onRerun, onDelete, loading }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-4 py-3">
        <h3 className="text-sm font-semibold text-slate-700">Scenario history</h3>
      </div>
      <div className="scroll-thin max-h-[420px] overflow-y-auto">
        {loading && (
          <div className="space-y-2 p-4">
            {[0, 1, 2].map((i) => (
              <div key={i} className="h-16 animate-pulse rounded-lg bg-slate-100" />
            ))}
          </div>
        )}
        {!loading && scenarios.length === 0 && (
          <p className="px-4 py-6 text-center text-xs text-slate-400">
            No scenarios yet. Run your first analysis.
          </p>
        )}
        {scenarios.map((scenario) => {
          const isActive = scenario.scenario_id === activeScenarioId;
          return (
            <div
              key={scenario.scenario_id}
              className={`cursor-pointer border-b border-slate-100 px-4 py-3 transition-colors hover:bg-slate-50 ${
                isActive ? "bg-brand-50" : ""
              }`}
              onClick={() => onSelect(scenario.scenario_id)}
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-sm font-medium text-slate-800">
                    {scenario.disaster_type} · {scenario.epicenter}
                  </p>
                  <p className="mt-0.5 truncate text-xs text-slate-400">{scenario.scenario_id}</p>
                </div>
                {scenario.has_final_recommendation ? (
                  <span className="shrink-0 rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-semibold text-emerald-700">
                    Ready
                  </span>
                ) : (
                  <span className="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-500">
                    Incomplete
                  </span>
                )}
              </div>
              <div className="mt-2 flex items-center justify-between text-xs text-slate-500">
                <span>
                  Affected: {scenario.affected_population?.toLocaleString() ?? "-"}
                </span>
                <span>
                  Accommodation: {scenario.accommodation_percent != null ? `${scenario.accommodation_percent.toFixed(1)}%` : "-"}
                </span>
              </div>
              <div className="mt-2 flex gap-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onRerun(scenario.scenario_id);
                  }}
                  className="rounded-md border border-slate-200 px-2 py-1 text-[11px] font-medium text-slate-600 transition hover:border-brand-500 hover:text-brand-700"
                >
                  Re-run
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(scenario.scenario_id);
                  }}
                  className="rounded-md border border-slate-200 px-2 py-1 text-[11px] font-medium text-slate-600 transition hover:border-red-400 hover:text-red-600"
                >
                  Delete
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}