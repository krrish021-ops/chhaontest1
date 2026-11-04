"use client";

import React, { useState } from "react";
import {
  Sliders,
  Loader2,
  AlertTriangle,
  Info,
  CheckCircle2,
} from "lucide-react";
import { API_BASE } from "@/lib/api";

interface ScenarioComparisonProps {
  cellId: string;
  cityId: string;
}

export const ScenarioComparison: React.FC<ScenarioComparisonProps> = ({
  cellId,
  cityId,
}) => {
  const [loading, setLoading]             = useState(false);
  const [comparisonData, setComparisonData] = useState<any>(null);
  const [error, setError]                 = useState<string | null>(null);

  const runComparison = async () => {
    setLoading(true);
    setError(null);
    setComparisonData(null);

    try {
      const res = await fetch(`${API_BASE}/api/v1/scenario/compare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          city_id: cityId,
          cell_id: cellId,
          scenarios: [
            { name: "Option A: Tree Canopy (+20%)",   action: "add_trees",      area_pct: 20 },
            { name: "Option B: Water Body (+15%)",    action: "restore_water",  area_pct: 15 },
            { name: "Option C: Densification (+25%)", action: "add_concrete",   area_pct: 25 },
          ],
        }),
      });

      if (res.status === 501) {
        throw new Error(
          "Scenario data not available for this city. " +
          "Run the GEE pipeline to generate the feature matrix first."
        );
      }
      if (!res.ok) {
        throw new Error(`Server error ${res.status} — check API logs.`);
      }

      const data = await res.json();
      setComparisonData(data);
    } catch (err: any) {
      setError(err.message || "Comparison failed unexpectedly.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-3 mt-3 pt-3 border-t border-slate-700/60 text-xs">

      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="font-semibold text-slate-300">
          Multi-Scenario Comparator
        </span>
        <button
          onClick={runComparison}
          disabled={loading}
          className="flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-orange-400 border border-slate-700 transition disabled:opacity-50"
        >
          {loading ? (
            <Loader2 className="w-3 h-3 animate-spin" />
          ) : (
            <Sliders className="w-3 h-3" />
          )}
          <span>Compare 3 Options</span>
        </button>
      </div>

      {/* What this does */}
      <div className="text-[10px] text-slate-500 bg-slate-800/40 rounded p-2 border border-slate-700/40">
        Evaluates tree planting, water restoration, and densification
        side-by-side on this cell using the LightGBM v1 quantile model.
        Per-cell only — no multi-cell or ward aggregation.
      </div>

      {/* Calibration warning */}
      <div className="flex items-start space-x-1.5 text-[10px] text-amber-400 bg-amber-950/30 p-2 rounded border border-amber-800/40">
        <AlertTriangle className="w-3 h-3 flex-shrink-0 mt-0.5" />
        <span>
          Uncertainty bands overconfident (62.4% vs 80% target).
          ΔT ranges are indicative only.
        </span>
      </div>

      {/* Error state */}
      {error && (
        <div className="flex items-start space-x-1.5 text-[11px] text-red-400 bg-red-950/40 p-2.5 rounded-lg border border-red-800/50">
          <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Results */}
      {comparisonData && (
        <div className="space-y-2 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">

          {/* Success */}
          <div className="flex items-center space-x-1.5 text-[10px] text-green-400 mb-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Inference complete — LightGBM v1 quantile model</span>
          </div>

          <div className="text-[11px] text-slate-400">
            Best Strategy:{" "}
            <strong className="text-green-400">
              {comparisonData.best_cooling_scenario}
            </strong>
          </div>

          <div className="space-y-1.5">
            {comparisonData.comparison_table?.map((row: any, idx: number) => (
              <div
                key={idx}
                className="flex items-center justify-between p-2 rounded bg-slate-900 border border-slate-800/80 text-[11px]"
              >
                <div>
                  <div className="font-semibold text-slate-200">{row.name}</div>
                  <div className="text-[10px] text-slate-400">
                    Est. Cost: {row.cost_inr_formatted ?? "—"}
                  </div>
                </div>
                <div className="text-right">
                  <div
                    className={`font-bold ${
                      row.delta_T_p50 <= 0 ? "text-green-400" : "text-red-400"
                    }`}
                  >
                    {row.delta_T_p50 != null
                      ? `${row.delta_T_p50 >= 0 ? "+" : ""}${row.delta_T_p50.toFixed(2)}°C`
                      : "—"}
                  </div>
                  <div className="text-[9px] text-slate-500">
                    {row.delta_T_p10 != null && row.delta_T_p90 != null
                      ? `(${row.delta_T_p10.toFixed(1)} to ${row.delta_T_p90.toFixed(1)})`
                      : ""}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Cross-city warning if present */}
          {comparisonData.cross_city_model && (
            <div className="flex items-start space-x-1 text-[10px] text-sky-300 bg-sky-950/40 p-1.5 rounded border border-sky-800/40">
              <Info className="w-3 h-3 flex-shrink-0 mt-0.5" />
              <span>
                Cross-city model applied (held-out MAE 1.107°C).
                Treat as lower-confidence.
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
