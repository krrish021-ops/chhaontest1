	"use client";

import React, { useState } from "react";
import {
  X,
  Sliders,
  AlertTriangle,
  Loader2,
  Info,
  CheckCircle2,
} from "lucide-react";
import { evaluateScenario } from "@/lib/api";
import { ScenarioResponse } from "@/lib/types";

interface ScenarioPainterProps {
  cellId: string;
  cityId: string;
  onClose: () => void;
}

const ACTIONS = [
  { id: "add_trees",      label: "🌳 Plant Trees" },
  { id: "restore_water",  label: "💧 Water Body" },
  { id: "add_concrete",   label: "🏢 Add Concrete" },
] as const;

type ActionId = typeof ACTIONS[number]["id"];

export function ScenarioPainter({ cellId, cityId, onClose }: ScenarioPainterProps) {
  const [action, setAction]           = useState<ActionId>("add_trees");
  const [coveragePct, setCoveragePct] = useState<number>(25);
  const [loading, setLoading]         = useState(false);
  const [result, setResult]           = useState<ScenarioResponse | null>(null);
  const [errorMsg, setErrorMsg]       = useState<string | null>(null);

  const handleRunSimulation = async () => {
    setLoading(true);
    setResult(null);
    setErrorMsg(null);

    try {
      const res = await evaluateScenario({
        city_id: cityId,
        cell_id: cellId,
        action,
        area_pct_change: coveragePct,
      });
      setResult(res);
    } catch (err: any) {
      setErrorMsg(
        err?.message ||
          "Scenario evaluation failed. This city/cell may not have scenario data available yet."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full rounded-xl border border-orange-500/50 bg-slate-900/98 p-4 shadow-2xl backdrop-blur-md text-xs text-slate-200">

      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-2.5 mb-3">
        <div className="flex items-center space-x-2">
          <Sliders className="w-4 h-4 text-orange-400" />
          <div>
            <h3 className="font-bold text-sm text-white">Scenario Simulator</h3>
            <p className="text-[10px] text-slate-400">Cell: {cellId}</p>
          </div>
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-white">
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* How it works note */}
      <div className="text-[10px] text-slate-500 bg-slate-800/40 rounded-lg p-2 mb-3 border border-slate-700/40">
        Evaluates a single land-cover transfer on this 1 km² cell using the
        LightGBM v1 quantile model (P10/P50/P90). Per-cell only — no
        multi-cell painting or spillover yet.
      </div>

      {/* Action picker */}
      <div className="space-y-3 mb-4">
        <div>
          <label className="text-[11px] font-semibold text-slate-300">
            Planning Intervention
          </label>
          <div className="grid grid-cols-3 gap-1.5 mt-1.5">
            {ACTIONS.map((a) => (
              <button
                key={a.id}
                onClick={() => setAction(a.id)}
                className={`py-1.5 text-[11px] text-center rounded border transition ${
                  action === a.id
                    ? "bg-orange-600 text-white font-bold border-orange-400 shadow"
                    : "bg-slate-800/80 text-slate-300 border-slate-700 hover:bg-slate-800"
                }`}
              >
                {a.label}
              </button>
            ))}
          </div>
        </div>

        {/* Coverage slider */}
        <div>
          <div className="flex justify-between text-[11px] font-semibold text-slate-300 mb-1">
            <span>Area Coverage</span>
            <span className="text-orange-400 font-bold">{coveragePct}%</span>
          </div>
          <input
            type="range"
            min="5"
            max="50"
            step="5"
            value={coveragePct}
            onChange={(e) => setCoveragePct(parseInt(e.target.value))}
            className="w-full accent-orange-500 cursor-pointer"
          />
        </div>

        {/* Quantile calibration warning */}
        <div className="flex items-start space-x-1.5 text-[10px] text-amber-400 bg-amber-950/30 p-2 rounded-lg border border-amber-800/40">
          <AlertTriangle className="w-3 h-3 flex-shrink-0 mt-0.5" />
          <span>
            Uncertainty bands are overconfident (62.4% coverage vs 80% target).
            P10–P90 range is indicative only.
          </span>
        </div>

        <button
          onClick={handleRunSimulation}
          disabled={loading}
          className="w-full py-2 rounded-lg bg-orange-600 hover:bg-orange-500 text-white font-semibold text-xs shadow-md transition flex items-center justify-center space-x-1.5 disabled:opacity-50"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Running inference...</span>
            </>
          ) : (
            <>
              <Sliders className="w-4 h-4" />
              <span>Evaluate Thermal & Cost Yield</span>
            </>
          )}
        </button>
      </div>

      {/* Error state */}
      {errorMsg && (
        <div className="flex items-start space-x-1.5 text-[11px] text-red-400 bg-red-950/40 p-2.5 rounded-lg border border-red-800/50 mb-3">
          <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Result card */}
      {result && (
        <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-2">

          {/* Success indicator */}
          <div className="flex items-center space-x-1.5 text-[10px] text-green-400 mb-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Inference complete — LightGBM v1 quantile model</span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-slate-400">Projected ΔT (P50):</span>
            <strong
              className={`text-sm ${
                result.delta_T_degC.p50 <= 0 ? "text-green-400" : "text-red-400"
              }`}
            >
              {result.delta_T_degC.p50 > 0 ? "+" : ""}
              {result.delta_T_degC.p50.toFixed(2)}°C
            </strong>
          </div>

          <div className="flex items-center justify-between text-[11px]">
            <span className="text-slate-500">Range (P10–P90):</span>
            <span className="text-slate-300 font-mono">
              {result.delta_T_degC.p10.toFixed(2)}°C →{" "}
              {result.delta_T_degC.p90.toFixed(2)}°C
            </span>
          </div>

          <div className="flex items-center justify-between text-[11px] pt-1.5 border-t border-slate-800/80">
            <span className="text-slate-400">Indicative Budget:</span>
            <strong className="text-orange-400">{result.cost_formatted}</strong>
          </div>

          {/* Cross-city warning */}
          {result.cross_city_model && (
            <div className="flex items-start space-x-1 text-[10px] text-sky-300 bg-sky-950/40 p-1.5 rounded border border-sky-800/40 mt-1">
              <Info className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
              <span>
                Model trained on {result.model_source_city} data — cross-city
                transfer (held-out MAE 1.107°C, R² −0.20). Treat as
                lower-confidence.
              </span>
            </div>
          )}

          {/* Extrapolation warning */}
          {result.extrapolation_warning && (
            <div className="flex items-start space-x-1 text-[10px] text-amber-400 bg-amber-950/40 p-1.5 rounded border border-amber-800/40 mt-1">
              <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
              <span>
                Extrapolation warning — scenario is near or outside the
                boundary of training data. Domain guard flagged low confidence.
              </span>
            </div>
          )}

        </div>
      )}

    </div>
  );
}

export default ScenarioPainter;
