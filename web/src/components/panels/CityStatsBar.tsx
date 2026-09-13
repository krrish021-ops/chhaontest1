'use client';

import { useMemo } from 'react';
import { ThermometerSun, Building2, Trees, Flame } from 'lucide-react';
import type { HeatmapGeoJSON } from '@/lib/types';

interface CityStatsBarProps {
  data: HeatmapGeoJSON | null;
}

export default function CityStatsBar({ data }: CityStatsBarProps) {
  const stats = useMemo(() => {
    if (!data || !data.features || data.features.length === 0) return null;

    const feats = data.features.map((f) => f.properties);
    const n = feats.length;

    const meanSuhiiNight = feats.reduce((s, f) => s + (f.suhii_night || 0), 0) / n;
    const maxSuhiiNight = Math.max(...feats.map((f) => f.suhii_night || 0));
    const meanBuilt = feats.reduce((s, f) => s + (f.frac_built || 0), 0) / n;
    const meanTree = feats.reduce((s, f) => s + (f.frac_tree || 0), 0) / n;
    const hotspotCount = feats.filter((f) => (f.suhii_night || 0) >= 3).length;

    return {
      meanSuhiiNight,
      maxSuhiiNight,
      meanBuilt: meanBuilt * 100,
      meanTree: meanTree * 100,
      hotspotCount,
      totalCells: n,
    };
  }, [data]);

  if (!stats) return null;

  return (
    <div className="bg-slate-900/95 backdrop-blur-md rounded-xl shadow-2xl border border-slate-700 px-4 py-2.5 flex items-center gap-4">
      <StatItem
        icon={<ThermometerSun className="w-3.5 h-3.5 text-orange-400" />}
        label="Mean SUHII"
        value={`${stats.meanSuhiiNight >= 0 ? '+' : ''}${stats.meanSuhiiNight.toFixed(1)}°C`}
      />
      <div className="w-px h-6 bg-slate-700" />
      <StatItem
        icon={<Flame className="w-3.5 h-3.5 text-red-400" />}
        label="Peak"
        value={`+${stats.maxSuhiiNight.toFixed(1)}°C`}
      />
      <div className="w-px h-6 bg-slate-700" />
      <StatItem
        icon={<Building2 className="w-3.5 h-3.5 text-slate-400" />}
        label="Built"
        value={`${stats.meanBuilt.toFixed(0)}%`}
      />
      <div className="w-px h-6 bg-slate-700" />
      <StatItem
        icon={<Trees className="w-3.5 h-3.5 text-emerald-400" />}
        label="Canopy"
        value={`${stats.meanTree.toFixed(0)}%`}
      />
      <div className="w-px h-6 bg-slate-700" />
      <div className="text-center">
        <div className="text-lg font-bold text-red-400 leading-none">
          {stats.hotspotCount}
        </div>
        <div className="text-[9px] uppercase tracking-wider text-slate-500 mt-0.5">
          Hotspots
        </div>
      </div>
    </div>
  );
}

function StatItem({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div>
      <div className="flex items-center gap-1 text-[9px] uppercase tracking-wider text-slate-500">
        {icon}
        {label}
      </div>
      <div className="text-sm font-bold text-white leading-tight mt-0.5">
        {value}
      </div>
    </div>
  );
}
