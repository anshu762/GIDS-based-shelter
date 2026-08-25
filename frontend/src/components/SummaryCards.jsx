import React from "react";

function formatNumber(value) {
  if (value === null || value === undefined) return "-";
  return Number(value).toLocaleString();
}

function formatPercent(value) {
  if (value === null || value === undefined) return "-";
  return `${Number(value).toFixed(2)}%`;
}

export default function SummaryCards({ summary }) {
  if (!summary) return null;

  const accommodation = summary.PopulationAccommodationPercent ?? 0;
  const accommodationColor =
    accommodation >= 100
      ? "text-emerald-600"
      : accommodation >= 60
      ? "text-amber-600"
      : "text-red-600";

  const cards = [
    {
      label: "Affected population",
      value: formatNumber(summary.AffectedPopulation),
      sub: `${summary.DisasterType} near ${summary.Epicenter}`,
      accent: "border-l-slate-400",
    },
    {
      label: "Allocated population",
      value: formatNumber(summary.AllocatedPopulation),
      sub: `${formatNumber(summary.UnallocatedPopulation)} unallocated`,
      accent: "border-l-brand-500",
    },
    {
      label: "Population accommodation",
      value: formatPercent(accommodation),
      sub: `Best radius: ${Number(summary.BestSolutionRadius_km ?? 0).toFixed(2)} km`,
      valueClass: accommodationColor,
      accent: accommodation >= 100 ? "border-l-emerald-500" : "border-l-amber-500",
    },
    {
      label: "Selected shelters",
      value: formatNumber(summary.SelectedShelters),
      sub: `${formatNumber(summary.PrimaryShelters)} primary · ${formatNumber(summary.SupplementaryShelters)} supplementary`,
      accent: "border-l-indigo-500",
    },
    {
      label: "Medical-capable shelters",
      value: formatNumber(summary.MedicalFacilityShelters),
      sub: `${formatNumber(summary.TotalSelectedCapacity)} total capacity`,
      accent: "border-l-rose-500",
    },
  ];

  return (
    <div className="grid animate-fadeIn grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
      {cards.map((card) => (
        <div
          key={card.label}
          className={`rounded-xl border border-slate-200 border-l-4 ${card.accent} bg-white p-4 shadow-sm transition-shadow hover:shadow-md`}
        >
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            {card.label}
          </p>
          <p className={`mt-2 text-2xl font-bold tabular-nums ${card.valueClass || "text-slate-900"}`}>
            {card.value}
          </p>
          <p className="mt-1 text-xs text-slate-400">{card.sub}</p>
        </div>
      ))}
    </div>
  );
}