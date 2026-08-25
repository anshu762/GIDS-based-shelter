import React, { useState } from "react";

const DISASTER_TYPES = ["Flood", "Earthquake", "Fire", "Cyclone"];

const DISASTER_ICONS = {
  Flood: "\u{1F30A}",
  Earthquake: "\u{1F3D4}\uFE0F",
  Fire: "\u{1F525}",
  Cyclone: "\u{1F32A}\uFE0F",
};

const PRESETS = [
  { label: "Cyclone · Goregaon (8 km)", disaster_type: "Cyclone", epicenter_name: "Goregaon", epicenter_lat: 19.155148, epicenter_lon: 72.867851, radius_km: 8 },
  { label: "Flood · Dharavi (5 km)", disaster_type: "Flood", epicenter_name: "Dharavi", epicenter_lat: 19.050751, epicenter_lon: 72.862396, radius_km: 5 },
  { label: "Earthquake · Trombay (2 km)", disaster_type: "Earthquake", epicenter_name: "Trombay", epicenter_lat: 19.020387, epicenter_lon: 72.909885, radius_km: 2 },
];

const initialForm = {
  disaster_type: "Flood",
  epicenter_name: "",
  epicenter_lat: "",
  epicenter_lon: "",
  radius_km: "",
};

function validate(form) {
  const errors = {};

  if (!DISASTER_TYPES.includes(form.disaster_type)) {
    errors.disaster_type = "Choose a supported disaster type.";
  }

  if (!form.epicenter_name || !form.epicenter_name.trim()) {
    errors.epicenter_name = "Epicenter name is required.";
  }

  const lat = parseFloat(form.epicenter_lat);
  if (Number.isNaN(lat) || lat < -90 || lat > 90) {
    errors.epicenter_lat = "Latitude must be a number between -90 and 90.";
  }

  const lon = parseFloat(form.epicenter_lon);
  if (Number.isNaN(lon) || lon < -180 || lon > 180) {
    errors.epicenter_lon = "Longitude must be a number between -180 and 180.";
  }

  const radius = parseFloat(form.radius_km);
  if (Number.isNaN(radius) || radius <= 0 || radius > 100) {
    errors.radius_km = "Radius must be a positive number (max 100 km).";
  }

  return errors;
}

export default function ScenarioForm({ onSubmit, submitting }) {
  const [form, setForm] = useState(initialForm);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (touched[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  }

  function markTouched(field) {
    setTouched((prev) => ({ ...prev, [field]: true }));
  }

  function applyPreset(preset) {
    setForm({
      disaster_type: preset.disaster_type,
      epicenter_name: preset.epicenter_name,
      epicenter_lat: String(preset.epicenter_lat),
      epicenter_lon: String(preset.epicenter_lon),
      radius_km: String(preset.radius_km),
    });
    setErrors({});
  }

  function handleSubmit(e) {
    e.preventDefault();
    const validation = validate(form);
    setErrors(validation);
    setTouched({
      disaster_type: true,
      epicenter_name: true,
      epicenter_lat: true,
      epicenter_lon: true,
      radius_km: true,
    });
    if (Object.keys(validation).length > 0) return;

    onSubmit({
      disaster_type: form.disaster_type,
      epicenter_name: form.epicenter_name.trim(),
      epicenter_lat: parseFloat(form.epicenter_lat),
      epicenter_lon: parseFloat(form.epicenter_lon),
      radius_km: parseFloat(form.radius_km),
    });
  }

  const fieldClass = (hasError) =>
    `w-full rounded-lg border px-3 py-2.5 text-sm outline-none transition-all duration-150 focus:ring-2 focus:ring-brand-500/60 focus:border-brand-500 ${
      hasError ? "border-red-400 bg-red-50" : "border-slate-300 bg-white hover:border-slate-400"
    }`;

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Quick presets
        </p>
        <div className="flex flex-wrap gap-2">
          {PRESETS.map((preset) => (
            <button
              key={preset.label}
              type="button"
              onClick={() => applyPreset(preset)}
              className="rounded-full border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:border-brand-500 hover:bg-brand-50 hover:text-brand-700 active:scale-95"
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="mb-1.5 block text-sm font-semibold text-slate-700">
          Disaster type
        </label>
        <div className="grid grid-cols-2 gap-2">
          {DISASTER_TYPES.map((type) => (
            <button
              key={type}
              type="button"
              onClick={() => update("disaster_type", type)}
              className={`flex items-center justify-center gap-2 rounded-lg border px-3 py-2.5 text-sm font-medium transition-all ${
                form.disaster_type === type
                  ? "border-brand-500 bg-brand-50 text-brand-700 shadow-sm ring-1 ring-brand-500/30"
                  : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"
              }`}
            >
              <span aria-hidden="true">{DISASTER_ICONS[type]}</span>
              {type}
            </button>
          ))}
        </div>
        <p className="mt-1.5 text-xs text-slate-400">
          Matches the FloodSafe / EarthquakeSafe / FireSafe / CycloneSafe columns
          in the Building Type Master sheet.
        </p>
      </div>

      <div>
        <label className="mb-1.5 block text-sm font-semibold text-slate-700">
          Epicenter name
        </label>
        <input
          type="text"
          placeholder="e.g. Goregaon"
          value={form.epicenter_name}
          onBlur={() => markTouched("epicenter_name")}
          onChange={(e) => update("epicenter_name", e.target.value)}
          className={fieldClass(touched.epicenter_name && errors.epicenter_name)}
        />
        {touched.epicenter_name && errors.epicenter_name && (
          <p className="mt-1 text-xs text-red-600">{errors.epicenter_name}</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="mb-1.5 block text-sm font-semibold text-slate-700">
            Latitude
          </label>
          <input
            type="number"
            step="0.000001"
            placeholder="19.155148"
            value={form.epicenter_lat}
            onBlur={() => markTouched("epicenter_lat")}
            onChange={(e) => update("epicenter_lat", e.target.value)}
            className={fieldClass(touched.epicenter_lat && errors.epicenter_lat)}
          />
          {touched.epicenter_lat && errors.epicenter_lat && (
            <p className="mt-1 text-xs text-red-600">{errors.epicenter_lat}</p>
          )}
        </div>
        <div>
          <label className="mb-1.5 block text-sm font-semibold text-slate-700">
            Longitude
          </label>
          <input
            type="number"
            step="0.000001"
            placeholder="72.867851"
            value={form.epicenter_lon}
            onBlur={() => markTouched("epicenter_lon")}
            onChange={(e) => update("epicenter_lon", e.target.value)}
            className={fieldClass(touched.epicenter_lon && errors.epicenter_lon)}
          />
          {touched.epicenter_lon && errors.epicenter_lon && (
            <p className="mt-1 text-xs text-red-600">{errors.epicenter_lon}</p>
          )}
        </div>
      </div>

      <div>
        <label className="mb-1.5 block text-sm font-semibold text-slate-700">
          Disaster radius (km)
        </label>
        <input
          type="number"
          step="0.1"
          placeholder="8.0"
          value={form.radius_km}
          onBlur={() => markTouched("radius_km")}
          onChange={(e) => update("radius_km", e.target.value)}
          className={fieldClass(touched.radius_km && errors.radius_km)}
        />
        {touched.radius_km && errors.radius_km && (
          <p className="mt-1 text-xs text-red-600">{errors.radius_km}</p>
        )}
        <p className="mt-1.5 text-xs text-slate-400">
          Shelter search radius is computed automatically as 1.4x this value
          by Module 1, then expanded dynamically by Module 4 if needed.
        </p>
      </div>

      <button
        type="submit"
        disabled={submitting}
        className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-3 text-sm font-semibold text-white shadow-sm transition-all hover:bg-brand-700 hover:shadow-md active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60"
      >
        {submitting && (
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
        )}
        {submitting ? "Running pipeline..." : "Run evacuation analysis"}
      </button>
    </form>
  );
}