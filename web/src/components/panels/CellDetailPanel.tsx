'use client';

import { useState, useEffect } from 'react';
import {
  X, Info, Brain, TrendingUp, Paintbrush,
  Building2, Trees, Droplets, ThermometerSun,
} from 'lucide-react';
import { fetchCellExplanation } from '@/lib/api';
import type { CellProperties, CellExplanation } from '@/lib/types';

interface CellDetailPanelProps {
  cell: CellProperties;
  onClose: () => void;
  onStartScenario: () => void;
}

type Tab = 'overview' | 'diagnosis' | 'forecast';

/** Safely convert any value to a number (MapLibre often returns strings) */
function num(v: unknown, fallback = 0): number {
  if (v === null || v === undefined) return fallback;
  const n = typeof v === 'number' ? v : parseFloat(String(v));
  return Number.isFinite(n) ? n : fallback;
}

function fmt(v: unknown, digits = 1, fallback = '—'): string {
  const n = num(v, NaN);
  return Number.isFinite(n) ? n.toFixed(digits) : fallback;
}

export default function CellDetailPanel({
  cell,
  onClose,
  onStartScenario,
}: CellDetailPanelProps) {
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [explanation, setExplanation] = useState<CellExplanation | null>(null);
  const [loading, setLoading] = useState(false);

  // Coerce all numeric fields once
  const lat = num(cell.lat);
  const lon = num(cell.lon);
  const suhiiNight = num(cell.suhii_night);
  const suhiiDay = num(cell.suhii_day);
  const lstNight = num(cell.lst_night);
  const lstDay = num(cell.lst_day);
  const fracBuilt = num(cell.frac_built);
  const fracTree = num(cell.frac_tree);
  const fracWater = num(cell.frac_water);
  const suhiiNight2031 = num(cell.suhii_night_2031, suhiiNight + 0.4);
  const suhiiNight2041 = num(cell.suhii_night_2041, suhiiNight + 1.2);
  const cellId = String(cell.cell_id || 'Unknown');

  useEffect(() => {
    setExplanation(null);
    setActiveTab('overview');
  }, [cellId]);

  useEffect(() => {
    if (activeTab === 'diagnosis' && !explanation) {
      setLoading(true);
      fetchCellExplanation(cellId)
        .then(setExplanation)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [activeTab, cellId, explanation]);

  const heatColor = getHeatColor(suhiiNight);

  return (
    <div className="w-[380px] h-full flex flex-col bg-slate-900/95 backdrop-blur-md rounded-2xl shadow-2xl border border-slate-700 overflow-hidden">
      {/* Header */}
      <div className="p-4 pb-3 border-b border-slate-800 shrink-0">
        <div className="flex items-start justify-between">
          <div>
            <div className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
              Zone Inspector
            </div>
            <h2 className="text-xl font-bold text-white mt-0.5">
              Zone {cellId}
            </h2>
            <div className="text-[11px] text-slate-500 mt-0.5">
              {lat !== 0 || lon !== 0
                ? `${fmt(lat, 4)}°N, ${fmt(lon, 4)}°E`
                : 'Coordinates unavailable'}
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-all"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 shrink-0">
        <TabButton
          active={activeTab === 'overview'}
          onClick={() => setActiveTab('overview')}
          icon={<Info className="w-3.5 h-3.5" />}
          label="Current"
        />
        <TabButton
          active={activeTab === 'diagnosis'}
          onClick={() => setActiveTab('diagnosis')}
          icon={<Brain className="w-3.5 h-3.5" />}
          label="AI Diagnosis"
        />
        <TabButton
          active={activeTab === 'forecast'}
          onClick={() => setActiveTab('forecast')}
          icon={<TrendingUp className="w-3.5 h-3.5" />}
          label="Future"
        />
      </div>

      {/* Scrollable body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {activeTab === 'overview' && (
          <div className="space-y-4">
            <div className={`rounded-lg p-4 border-2 ${heatColor}`}>
              <div className="flex items-center gap-1.5 text-xs uppercase tracking-wider font-semibold opacity-80 mb-1">
                <ThermometerSun className="w-4 h-4" /> Nighttime Heat Anomaly
              </div>
              <div className="text-3xl font-bold font-mono">
                {suhiiNight >= 0 ? '+' : ''}
                {fmt(suhiiNight, 1)}°C
              </div>
              <div className="text-[11px] opacity-80 mt-1 leading-relaxed">
                This zone is {fmt(Math.abs(suhiiNight), 1)}°C{' '}
                {suhiiNight >= 0 ? 'hotter' : 'cooler'} than the rural
                countryside at night.
              </div>
            </div>

            {/* Day / Night LST */}
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-slate-800/50 rounded-lg p-3">
                <div className="text-[10px] text-slate-500 uppercase">Day LST</div>
                <div className="text-lg font-bold font-mono text-amber-400">
                  {fmt(lstDay, 1)}°C
                </div>
                <div className="text-[10px] text-slate-500">
                  SUHII {suhiiDay >= 0 ? '+' : ''}{fmt(suhiiDay, 1)}°C
                </div>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-3">
                <div className="text-[10px] text-slate-500 uppercase">Night LST</div>
                <div className="text-lg font-bold font-mono text-indigo-400">
                  {fmt(lstNight, 1)}°C
                </div>
                <div className="text-[10px] text-slate-500">
                  SUHII {suhiiNight >= 0 ? '+' : ''}{fmt(suhiiNight, 1)}°C
                </div>
              </div>
            </div>

            <div className="bg-slate-800/50 rounded-lg p-4 space-y-3">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                What is on the ground here?
              </div>
              <LandCoverBar
                icon={<Building2 className="w-3.5 h-3.5" />}
                label="Concrete / Asphalt"
                pct={fracBuilt * 100}
                color="bg-slate-500"
              />
              <LandCoverBar
                icon={<Trees className="w-3.5 h-3.5" />}
                label="Tree Canopy"
                pct={fracTree * 100}
                color="bg-emerald-500"
              />
              <LandCoverBar
                icon={<Droplets className="w-3.5 h-3.5" />}
                label="Water Bodies"
                pct={fracWater * 100}
                color="bg-blue-500"
              />
            </div>

            <button
              onClick={onStartScenario}
              className="w-full bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white font-semibold py-3 px-4 rounded-xl shadow-lg transition-all flex items-center justify-center gap-2"
            >
              <Paintbrush className="w-4 h-4" />
              Test AI Interventions
            </button>
          </div>
        )}

        {activeTab === 'diagnosis' && (
          <div className="space-y-4">
            <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-3 text-xs text-purple-200 leading-relaxed">
              <strong>How does the AI know this?</strong>
              <br />
              The model calculates exactly how much each feature (concrete,
              trees, water) contributes to heating or cooling this zone.
            </div>

            {loading && (
              <div className="text-center py-8 text-slate-500 text-sm animate-pulse">
                Running AI analysis...
              </div>
            )}

            {explanation && (
              <div className="space-y-3">
                {(explanation.drivers || []).map((driver, i) => {
                  const contrib = num(driver.shap_contribution_degC);
                  return (
                    <div key={i} className="p-3 bg-slate-800/50 rounded-lg">
                      <div className="text-xs text-slate-300 mb-1 leading-relaxed">
                        {driver.text || driver.feature}
                      </div>
                      <div
                        className={`text-lg font-bold font-mono ${
                          contrib > 0 ? 'text-red-400' : 'text-emerald-400'
                        }`}
                      >
                        {contrib > 0 ? 'Heats by +' : 'Cools by '}
                        {Math.abs(contrib).toFixed(2)}°C
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {activeTab === 'forecast' && (
          <div className="space-y-4">
            <div className="text-xs text-slate-300 leading-relaxed bg-slate-800/50 p-3 rounded-lg border-l-2 border-orange-500">
              If the city keeps building at the historical rate, the AI projects
              this zone&apos;s nighttime heat will intensify over the next 17 years.
            </div>
            <TrendBars
              today={suhiiNight}
              y2031={suhiiNight2031}
              y2041={suhiiNight2041}
            />
          </div>
        )}
      </div>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex-1 flex items-center justify-center gap-1.5 py-3 text-[11px] font-bold uppercase tracking-wider transition-all ${
        active
          ? 'text-white border-b-2 border-cyan-400 bg-slate-800/50'
          : 'text-slate-500 hover:text-slate-300 border-b-2 border-transparent'
      }`}
    >
      {icon}
      {label}
    </button>
  );
}

function LandCoverBar({
  icon,
  label,
  pct,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  pct: number;
  color: string;
}) {
  const safe = Number.isFinite(pct) ? Math.max(0, Math.min(pct, 100)) : 0;
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-1.5 text-xs text-slate-300">
          {icon}
          <span>{label}</span>
        </div>
        <span className="text-xs font-mono text-slate-400">
          {safe.toFixed(0)}%
        </span>
      </div>
      <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
        <div
          className={`h-full ${color} rounded-full transition-all`}
          style={{ width: `${safe}%` }}
        />
      </div>
    </div>
  );
}

function TrendBars({
  today,
  y2031,
  y2041,
}: {
  today: number;
  y2031: number;
  y2041: number;
}) {
  const values = [
    { year: 'Today', value: today, color: 'bg-blue-500' },
    { year: '2031', value: y2031, color: 'bg-orange-500' },
    { year: '2041', value: y2041, color: 'bg-red-500' },
  ];
  const maxVal = Math.max(...values.map((v) => v.value), 5);
  const minVal = Math.min(...values.map((v) => v.value), -1);
  const range = maxVal - minVal || 1;

  return (
    <div className="bg-slate-800/50 rounded-lg p-4">
      <div className="flex items-end justify-between gap-3 h-36">
        {values.map((v, i) => (
          <div key={i} className="flex-1 flex flex-col items-center gap-1">
            <div className="text-xs font-mono text-slate-300">
              {v.value >= 0 ? '+' : ''}
              {v.value.toFixed(1)}°C
            </div>
            <div
              className="w-full bg-slate-700/50 rounded relative flex flex-col justify-end"
              style={{ height: '90px' }}
            >
              <div
                className={`w-full rounded ${v.color} transition-all duration-700`}
                style={{
                  height: `${Math.max(((v.value - minVal) / range) * 100, 8)}%`,
                }}
              />
            </div>
            <div className="text-[10px] uppercase tracking-wider text-slate-500">
              {v.year}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function getHeatColor(suhii: number): string {
  if (suhii >= 4) return 'bg-red-500/10 text-red-400 border-red-500/30';
  if (suhii >= 2) return 'bg-orange-500/10 text-orange-400 border-orange-500/30';
  if (suhii >= 0) return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30';
  return 'bg-blue-500/10 text-blue-400 border-blue-500/30';
}
