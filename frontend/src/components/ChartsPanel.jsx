import React from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
  Legend,
  LineChart,
  Line,
} from "recharts";

const TIER_COLORS = ["#059669", "#d97706", "#64748b"];

function buildTierData(recommendation) {
  const primary = (recommendation.primary_recommendations || []).length;
  const supplementary = (recommendation.supplementary_recommendations || []).length;
  const others = Math.max(
    (recommendation.top_recommendations || []).length - primary - supplementary,
    0
  );
  return [
    { name: "Primary (GIDS)", value: primary },
    { name: "Supplementary", value: supplementary },
    { name: "Other", value: others },
  ].filter((d) => d.value > 0);
}

function buildCapacityData(recommendation) {
  return (recommendation.top_recommendations || []).slice(0, 10).map((s) => ({
    name: s.ShelterID,
    Capacity: s.Capacity,
    Assigned: s.AssignedPopulation,
  }));
}

function buildExpansionData(module4) {
  const history = module4?.expansion_history || [];
  return history.map((step) => ({
    radius: `${step.SearchRadius_km} km`,
    Accommodation: step.PopulationAccommodationPercent,
    Allocated: step.AllocatedPopulation,
  }));
}

export default function ChartsPanel({ recommendation, module4 }) {
  if (!recommendation) return null;

  const tierData = buildTierData(recommendation);
  const capacityData = buildCapacityData(recommendation);
  const expansionData = buildExpansionData(module4);

  return (
    <div className="grid animate-fadeIn grid-cols-1 gap-4 lg:grid-cols-3">
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <h4 className="mb-3 text-sm font-semibold text-slate-700">Shelter tier mix</h4>
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie
              data={tierData}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={80}
              label={({ name, value }) => `${name}: ${value}`}
            >
              {tierData.map((entry, index) => (
                <Cell key={entry.name} fill={TIER_COLORS[index % TIER_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend wrapperStyle={{ fontSize: 11 }} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <h4 className="mb-3 text-sm font-semibold text-slate-700">
          Top 10 shelters · capacity vs assigned
        </h4>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={capacityData}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="name" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip />
            <Bar dataKey="Capacity" fill="#93c5fd" radius={[3, 3, 0, 0]} />
            <Bar dataKey="Assigned" fill="#2563eb" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <h4 className="mb-3 text-sm font-semibold text-slate-700">
          Radius expansion vs accommodation %
        </h4>
        {expansionData.length === 0 ? (
          <p className="flex h-[220px] items-center justify-center px-4 text-center text-xs text-slate-400">
            No expansion was required \u2014 the initial search radius already met demand.
          </p>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={expansionData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="radius" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip />
              <Line type="monotone" dataKey="Accommodation" stroke="#2563eb" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}