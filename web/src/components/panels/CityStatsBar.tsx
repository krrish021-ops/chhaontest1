"use client";

import React from "react";
import { Flame, Trees, Building2, Droplets } from "lucide-react";

interface CityStatsBarProps {
  cityId: string;
}

export function CityStatsBar({ cityId }: CityStatsBarProps) {
  const isNagpur = cityId.toLowerCase() === "nagpur";

  const stats = [
    { label: "Mean Night SUHII", value: isNagpur ? "+1.92°C" : "+1.74°C", icon: Flame, color: "text-orange-400" },
    { label: "Peak Hotspot", value: isNagpur ? "+4.31°C" : "+3.88°C", icon: Flame, color: "text-red-400" },
    { label: "Built-up Surface", value: isNagpur ? "51.8%" : "58.4%", icon: Building2, color: "text-slate-300" },
    { label: "Tree Canopy", value: isNagpur ? "14.5%" : "12.2%", icon: Trees, color: "text-green-400" },
    { label: "Water Bodies", value: isNagpur ? "1.3%" : "1.8%", icon: Droplets, color: "text-blue-400" },
  ];

  return (
    <div className="flex items-center space-x-4 bg-slate-950/60 border border-slate-800 px-3.5 py-1.5 rounded-lg text-xs">
      {stats.map((s, idx) => {
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
