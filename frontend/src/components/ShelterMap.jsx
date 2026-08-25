import React from "react";
import { MapContainer, TileLayer, Marker, Popup, Circle } from "react-leaflet";
import L from "leaflet";

// Leaflet's default marker icons reference image paths that Vite does not
// resolve automatically; rebuild them from the CDN so pins render correctly.
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const epicenterIcon = new L.Icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [30, 48],
  iconAnchor: [15, 48],
});

export default function ShelterMap({ scenario, shelters }) {
  if (!scenario) return null;

  const center = [scenario.Latitude, scenario.Longitude];
  const disasterRadiusM = (scenario.DisasterRadius_km || 0) * 1000;
  const searchRadiusM = (scenario.ShelterSearchRadius_km || 0) * 1000;

  return (
    <div className="animate-fadeIn overflow-hidden rounded-xl border border-slate-200 shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-2.5">
        <h4 className="text-sm font-semibold text-slate-700">Shelter map</h4>
        <div className="flex items-center gap-3 text-[11px] text-slate-500">
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-full bg-red-500" /> Disaster zone
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-full border border-brand-500" /> Search radius
          </span>
        </div>
      </div>
      <div className="h-[420px] w-full">
        <MapContainer center={center} zoom={12} scrollWheelZoom className="h-full w-full">
          <TileLayer
            attribution='&copy; OpenStreetMap contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <Circle
            center={center}
            radius={disasterRadiusM}
            pathOptions={{ color: "#dc2626", weight: 1.5, fillOpacity: 0.08 }}
          />
          <Circle
            center={center}
            radius={searchRadiusM}
            pathOptions={{ color: "#2563eb", weight: 1.5, fillOpacity: 0.03, dashArray: "6 6" }}
          />

          <Marker position={center} icon={epicenterIcon}>
            <Popup>
              <strong>{scenario.Epicenter}</strong>
              <br />
              {scenario.DisasterType} epicenter
              <br />
              Disaster radius: {scenario.DisasterRadius_km} km
            </Popup>
          </Marker>

          {shelters.map((shelter) => (
            <Marker
              key={shelter.ShelterID}
              position={[shelter.Latitude, shelter.Longitude]}
            >
              <Popup>
                <strong>{shelter.ShelterName || "Unnamed shelter"}</strong>
                <br />
                {shelter.BuildingType} - {shelter.Locality}
                <br />
                Rank #{shelter.Rank} | {shelter.RecommendationTier}
                <br />
                Capacity: {shelter.Capacity?.toLocaleString()} | Assigned:{" "}
                {shelter.AssignedPopulation?.toLocaleString()}
                <br />
                Distance: {shelter.Distance_km?.toFixed(2)} km
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}