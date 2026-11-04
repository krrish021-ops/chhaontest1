"use client";

import React, { useEffect, useState } from "react";
import { Flame, Trees, Building2, Droplets, Loader2 } from "lucide-react";

interface CityStatsBarProps {
  cityId: string;
}

interface CityStats {
  meanNightSUHII: string;
  peakHotspot: string;
  builtSurface: string;
  treeCanopy: string;
  waterBodies: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

function computeStatsFromFeatures(features: any[]): CityStats {
  const validNight = features
    .map((f) => f.properties?.suhii_night ?? f.properties?.suhii_night_normalized)
    .filter((v) => v != null && !isNaN(v));

  const validBuilt = features
    .map((f) => f.properties?.frac_built)
    .filter((v) => v != null && !isNaN(v));

  const validTree = features
    .map((f) => f.properties?.frac_tree)
    .filter((v) => v != null && !isNaN(v));

  const validWater = features
    .map((f) => f.properties?.frac_water)
    .filter((v) => v != null && !isNaN(v));

  const mean = (arr: number[]) =>
    arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : null;

  const max = (arr: number[]) => (arr.length ? Math.max(...arr) : null);

  const meanNight = mean(validNight);
  const peakNight = max(validNight);
  const meanBuilt = mean(validBuilt);
  const meanTree = mean(validTree);
  const meanWater = mean(validWater);

  return {
    meanNightSUHII:
      meanNight != null
        ? `${meanNight >= 0 ? "+" : ""}${meanNight.toFixed(2)}°C`
        : "—",
    peakHotspot:
      peakNight != null
        ? `${peakNight >= 0 ? "+" : ""}${peakNight.toFixed(2)}°C`
        : "—",
    builtSurface:
      meanBuilt != null ? `${(meanBuilt * 100).toFixed(1)}%` : "—",
    treeCanopy:
      meanTree != null ? `${(meanTree * 100).toFixed(1)}%` : "—",
    waterBodies:
      meanWater != null ? `${(meanWater * 100).toFixed(1)}%` : "—",
  };
}

export function CityStatsBar({ cityId }: CityStatsBarProps) {
  const [stats, setStats] = useState<CityStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!cityId) return;
    setLoading(true);
    setError(false);
    setStats(null);

    fetch(`${API_BASE}/api/v1/layers/${cityId}`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch layer");
        return res.json();
      })
      .then((geojson) => {
        const features = geojson?.features ?? [];
        if (features.length === 0) throw new Error("No features");
        setStats(computeStatsFromFeatures(features));
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [cityId]);

  if (loading) {
    return (
      <div className="flex items-center space-x-2 bg-slate-950/60 border border-slate-800 px-3.5 py-1.5 rounded-lg text-xs text-slate-400">
        <Loader2 className="w-3.5 h-3.5 animate-spin" />
        <span>Loading city stats...</span>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="flex items-center bg-slate-950/60 border border-slate-800 px-3.5 py-1.5 rounded-lg text-xs text-slate-500">
        City stats unavailable
      </div>
    );
  }

  const statItems = [
    {
      label: "Mean Night SUHII",
      value: stats.meanNightSUHII,
      icon: Flame,
      color: "text-orange-400",
    },
    {
      label: "Peak Hotspot",
      value: stats.peakHotspot,
      icon: Flame,
      color: "text-red-400",
    },
    {
      label: "Built-up Surface",
      value: stats.builtSurface,
      icon: Building2,
      color: "text-slate-300",
    },
    {
      label: "Tree Canopy",
      value: stats.treeCanopy,
      icon: Trees,
      color: "text-green-400",
    },
    {
      label: "Water Bodies",
      value: stats.waterBodies,
      icon: Droplets,
      color: "text-blue-400",
    },
  ];

  return (
    <div className="flex items-center space-x-4 bg-slate-950/60 border border-slate-800 px-3.5 py-1.5 rounded-lg text-xs">
      {statItems.map((s, idx) => {
        const Icon = s.icon;
        return (
          <div key={idx} className="flex items-center space-x-1.5">
            <Icon className={`w-3.5 h-3.5 ${s.color}`} />
            <span className="text-slate-400 text-[11px]">{s.label}:</span>
            <strong className="text-slate-100 text-[11px]">{s.value}</strong>
          </div>
        );
      })}
    </div>
  );
}

export default CityStatsBar;
