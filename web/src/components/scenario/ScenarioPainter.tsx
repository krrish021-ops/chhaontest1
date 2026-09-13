'use client';

import { useState } from 'react';
import {
  X, Trees, Droplets, Building2, Play,
  AlertTriangle, TrendingDown, TrendingUp, Cpu, Activity, ArrowLeft
} from 'lucide-react';
import { evaluateScenario } from '@/lib/api';
import type { CellProperties, ScenarioResponse } from '@/lib/types';

interface ScenarioPainterProps {
  cell: CellProperties;
  onClose: () => void;
}

type Action = 'add_trees' | 'restore_water' | 'add_concrete';

const ACTIONS: {
  id: Action;
  label: string;
  icon: any;
  color: string;
  description: string;
}[] = [
  {
    id: 'add_trees',
    label: 'Plant Trees',
    icon: Trees,
    color: 'from-emerald-500 to-teal-500',
    description: 'Replaces concrete with tree canopy',
  },
  {
    id: 'restore_water',
    label: 'Restore Water',
    icon: Droplets,
    color: 'from-blue-500 to-cyan-500',
    description: 'Creates a lake or pond area',
  },
  {
    id: 'add_concrete',
    label: 'Build Concrete',
    icon: Building2,
    color: 'from-slate-500 to-slate-700',
    description: 'Simulates new urban development',
  },
];

export default function ScenarioPainter({ cell, onClose }: ScenarioPainterProps) {
  const [action, setAction] = useState<Action>('add_trees');
  const [coverage, setCoverage] = useState(20);
  const [result, setResult] = useState<ScenarioResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [aiTrace, setAiTrace] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleEvaluate = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    setAiTrace(['Initializing LightGBM model...']);

    try {
      setTimeout(() => setAiTrace((p) => [...p, 'Extracting local geographic features...']), 300);
      setTimeout(() => setAiTrace((p) => [...p, 'Applying monotone physics constraints...']), 600);
      setTimeout(() => setAiTrace((p) => [...p, 'Running 3 quantile models (P10/P50/P90)...']), 900);

      const res = await evaluateScenario({
        cell_id: cell.cell_id,
        action,
        area_pct_change: coverage,
      });

      setTimeout(() => {
        setAiTrace((p) => [...p, 'Inference complete.']);
        setResult(res);
        setLoading(false);
      }, 1200);
    } catch (err: any) {
      setError(err.message || 'Failed to evaluate scenario');
      setLoading(false);
    }
  };

  const selectedAction = ACTIONS.find((a) => a.id === action)!;

  return (
    /* NO absolute positioning — parent wrapper in page.tsx handles placement */
    <div className="w-[400px] h-full flex flex-col bg-slate-900/95 backdrop-blur-md rounded-2xl shadow-2xl border border-slate-700 overflow-hidden">
      {/* Header */}
      <div className="p-4 pb-3 border-b border-slate-800 bg-gradient-to-r from-emerald-900/40 to-teal-900/40 shrink-0">
        <div className="flex items-start justify-between">
          <div>
            <div className="text-xs uppercase tracking-wider text-emerald-400 font-semibold flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5" />
              AI Scenario Studio
            </div>
            <h2 className="text-xl font-bold text-white mt-0.5">
              Zone {cell.cell_id}
            </h2>
            <div className="text-xs text-slate-400 mt-1">
              Current Night Heat:{' '}
              <span className="font-mono text-slate-200 font-semibold">
                {cell.suhii_night >= 0 ? '+' : ''}
                {cell.suhii_night.toFixed(2)}°C
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-all"
            title="Back to zone details"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Scrollable body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-5">
        {/* Plain English prompt */}
        <div className="text-sm text-slate-300 leading-relaxed border-l-2 border-cyan-500 pl-3">
          Ask the AI:{' '}
          <i>
            &quot;What would happen to the temperature and budget if we changed
            the land use here?&quot;
          </i>
        </div>

        {/* Step 1: Action */}
        <div>
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            1. Choose an action
          </div>
          <div className="grid grid-cols-3 gap-2">
            {ACTIONS.map((opt) => {
              const Icon = opt.icon;
              const isActive = action === opt.id;
              return (
                <button
                  key={opt.id}
                  onClick={() => {
                    setAction(opt.id);
                    setResult(null);
                    setAiTrace([]);
                  }}
                  className={`p-3 rounded-lg text-center transition-all ${
                    isActive
                      ? `bg-gradient-to-br ${opt.color} text-white shadow-lg scale-105`
                      : 'bg-slate-800/50 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <Icon className="w-5 h-5 mx-auto mb-1" />
                  <div className="text-[11px] font-semibold">{opt.label}</div>
                </button>
              );
            })}
          </div>
          <div className="text-[11px] text-slate-500 mt-2">
            {selectedAction.description}
          </div>
        </div>

        {/* Step 2: Coverage */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              2. How much area?
            </div>
            <div className="text-lg font-bold text-white font-mono">{coverage}%</div>
          </div>
          <input
            type="range"
            min={5}
            max={50}
            step={5}
            value={coverage}
            onChange={(e) => {
              setCoverage(Number(e.target.value));
              setResult(null);
              setAiTrace([]);
            }}
            className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-cyan-500"
          />
          <div className="text-[11px] text-slate-500 mt-1">
            Applying to {coverage} hectares out of the 1 km² zone.
          </div>
        </div>

        {/* Evaluate Button */}
        <button
          onClick={handleEvaluate}
          disabled={loading}
          className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 disabled:opacity-50 text-white font-semibold py-3 px-4 rounded-xl shadow-lg transition-all flex items-center justify-center gap-2"
        >
          {loading ? (
            <Activity className="w-4 h-4 animate-pulse" />
          ) : (
            <Play className="w-4 h-4" />
          )}
          {loading ? 'AI Model Running...' : 'Ask AI to Evaluate Impact'}
        </button>

        {/* AI Trace */}
        {loading && (
          <div className="bg-black/60 rounded-lg p-3 font-mono text-[10px] text-emerald-400 space-y-1 border border-emerald-900/50">
            {aiTrace.map((log, i) => (
              <div key={i} className="flex gap-1">
                <span className="text-emerald-700">{'>'}</span>
                <span>{log}</span>
              </div>
            ))}
            <div className="animate-pulse text-emerald-700">{'>'} _</div>
          </div>
        )}

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-xs text-red-300">
            {error}
          </div>
        )}

        {/* Results */}
        {result && !loading && (
          <div className="space-y-4 border-t border-slate-800 pt-4">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              3. AI Prediction Results
            </div>

            {result.extrapolation_warning && (
              <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <div className="text-xs font-semibold text-amber-300 mb-0.5">
                    Unrealistic Scenario
                  </div>
                  <div className="text-[11px] text-amber-200/80 leading-relaxed">
                    This amount of change has no historical precedent. AI confidence is lower.
                  </div>
                </div>
              </div>
            )}

            {/* Delta T */}
            {(() => {
              const d = result.delta_T_degC;
              const cool = d.p50 < 0;
              return (
                <div
                  className={`rounded-lg p-4 border-2 ${
                    cool
                      ? 'bg-emerald-500/10 border-emerald-500/30'
                      : 'bg-red-500/10 border-red-500/30'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    {cool ? (
                      <TrendingDown className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <TrendingUp className="w-4 h-4 text-red-400" />
                    )}
                    <div className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                      Predicted Temperature Change
                    </div>
                  </div>
                  <div
                    className={`text-3xl font-bold font-mono ${
                      cool ? 'text-emerald-400' : 'text-red-400'
                    }`}
                  >
                    {d.p50 > 0 ? '+' : ''}
                    {d.p50.toFixed(2)}°C
                  </div>
                  <div className="text-[11px] text-slate-400 mt-2 leading-relaxed">
                    The AI is 80% confident the real result falls between{' '}
                    <strong className="text-slate-200 font-mono">
                      {d.p10 > 0 ? '+' : ''}
                      {d.p10.toFixed(2)}°C
                    </strong>{' '}
                    and{' '}
                    <strong className="text-slate-200 font-mono">
                      {d.p90 > 0 ? '+' : ''}
                      {d.p90.toFixed(2)}°C
                    </strong>
                    .
                  </div>
                </div>
              );
            })()}

            {/* Cost */}
            <div className="bg-slate-800/50 rounded-lg p-4">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Estimated Municipal Cost
              </div>
              <div className="text-2xl font-bold text-cyan-400 font-mono">
                {result.cost_formatted}
              </div>
            </div>

            {/* Before / After */}
            <div className="bg-slate-800/50 rounded-lg p-3 space-y-2">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Before → After (Night Heat)
              </div>
              <div className="flex items-center justify-between text-sm">
                <div>
                  <div className="text-[10px] text-slate-500">Before</div>
                  <div className="font-mono text-slate-300">
                    {result.original_suhii_night.p50 >= 0 ? '+' : ''}
                    {result.original_suhii_night.p50.toFixed(2)}°C
                  </div>
                </div>
                <div className="text-slate-600">→</div>
                <div>
                  <div className="text-[10px] text-slate-500">After</div>
                  <div
                    className={`font-mono font-semibold ${
                      result.delta_T_degC.p50 < 0
                        ? 'text-emerald-400'
                        : 'text-red-400'
                    }`}
                  >
                    {result.new_suhii_night.p50 >= 0 ? '+' : ''}
                    {result.new_suhii_night.p50.toFixed(2)}°C
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
