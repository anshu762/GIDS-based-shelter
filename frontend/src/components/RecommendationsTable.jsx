import React, { useState } from "react";

const TABS = [
  { key: "top_recommendations", label: "Top recommendations" },
  { key: "primary_recommendations", label: "Primary (GIDS)" },
  { key: "supplementary_recommendations", label: "Supplementary" },
  { key: "medical_recommendations", label: "Medical-capable" },
];

function tierBadge(tier) {
  if (!tier) return "bg-slate-100 text-slate-600";
  if (tier.startsWith("Primary")) return "bg-emerald-100 text-emerald-700";
  if (tier.startsWith("Supplementary")) return "bg-amber-100 text-amber-700";
  return "bg-slate-100 text-slate-600";
}

function utilizationBar(percent) {
  const clamped = Math.max(0, Math.min(100, percent || 0));
  const color = clamped >= 90 ? "bg-red-500" : clamped >= 60 ? "bg-amber-500" : "bg-emerald-500";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-slate-100">
        <div className={`h-full ${color}`} style={{ width: `${clamped}%` }} />
      </div>
      <span className="tabular-nums text-xs text-slate-500">{clamped.toFixed(0)}%</span>
    </div>
  );
}

export default function RecommendationsTable({ recommendation }) {
  const [activeTab, setActiveTab] = useState(TABS[0].key);

  if (!recommendation) return null;

  const rows = recommendation[activeTab] || [];

  return (
    <div className="animate-fadeIn rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex flex-wrap gap-1 border-b border-slate-200 p-2">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`rounded-lg px-3 py-2 text-xs font-semibold transition-all ${
              activeTab === tab.key
                ? "bg-brand-600 text-white shadow-sm"
                : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            {tab.label}
            <span
              className={`ml-1.5 rounded-full px-1.5 py-0.5 text-[10px] ${
                activeTab === tab.key ? "bg-white/20" : "bg-slate-200"
              }`}
            >
              {(recommendation[tab.key] || []).length}
            </span>
          </button>
        ))}
      </div>

      <div className="scroll-thin overflow-x-auto">
        <table className="w-full min-w-[920px] text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">Rank</th>
              <th className="px-4 py-3">Shelter</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Locality</th>
              <th className="px-4 py-3">Tier</th>
              <th className="px-4 py-3 text-right">Capacity</th>
              <th className="px-4 py-3 text-right">Assigned</th>
              <th className="px-4 py-3">Utilization</th>
              <th className="px-4 py-3 text-right">Distance (km)</th>
              <th className="px-4 py-3">Medical</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.length === 0 && (
              <tr>
                <td colSpan={10} className="px-4 py-8 text-center text-slate-400">
                  No shelters in this category.
                </td>
              </tr>
            )}
            {rows.map((shelter) => (
              <tr key={`${activeTab}-${shelter.ShelterID}`} className="transition-colors hover:bg-slate-50">
                <td className="px-4 py-3 font-semibold text-slate-700">{shelter.Rank}</td>
                <td className="px-4 py-3">
                  <p className="font-medium text-slate-800">{shelter.ShelterName || "Unnamed"}</p>
                  <p className="text-xs text-slate-400">{shelter.ShelterID}</p>
                </td>
                <td className="px-4 py-3 text-slate-600">{shelter.BuildingType}</td>
                <td className="px-4 py-3 text-slate-600">{shelter.Locality}</td>
                <td className="px-4 py-3">
                  <span className={`rounded-full px-2 py-1 text-xs font-medium ${tierBadge(shelter.RecommendationTier)}`}>
                    {shelter.RecommendationTier}
                  </span>
                </td>
                <td className="px-4 py-3 text-right tabular-nums text-slate-700">
                  {shelter.Capacity?.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-right tabular-nums text-slate-700">
                  {shelter.AssignedPopulation?.toLocaleString()}
                </td>
                <td className="px-4 py-3">{utilizationBar(shelter.UtilizationPercent)}</td>
                <td className="px-4 py-3 text-right tabular-nums text-slate-700">
                  {shelter.Distance_km?.toFixed(2)}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`rounded-full px-2 py-1 text-xs font-medium ${
                      shelter.MedicalFacility === "Yes"
                        ? "bg-rose-100 text-rose-700"
                        : "bg-slate-100 text-slate-500"
                    }`}
                  >
                    {shelter.MedicalFacility}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}