"use client";

import React, { useState } from "react";
import { Sliders, ArrowRight, ShieldCheck, DollarSign, ThermometerSnowflake, Loader2 } from "lucide-react";

interface ScenarioComparisonProps {
  cellId: string;
  cityId: string;
}

export const ScenarioComparison: React.FC<ScenarioComparisonProps> = ({ cellId, cityId }) => {
  const [loading, setLoading] = useState(false);
  const [comparisonData, setComparisonData] = useState<any>(null);

  const runComparison = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/scenario/compare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          city_id: cityId,
          cell_id: cellId,
          scenarios: [
            { name: "Option A (Tree Canopy +20%)", action: "add_trees", area_pct: 20 },
            { name: "Option B (Cool Roofs 50%)", action: "add_trees", area_pct: 35 },
            { name: "Option C (Water Reservoir)", action: "restore_water", area_pct: 15 },
          ],
        }),
      });

      if (!res.ok) throw new Error("Comparison failed");
      const data = await res.json();
      setComparisonData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-3 mt-3 pt-3 border-t border-slate-700/60 text-xs">
      <div className="flex items-center justify-between">
        <span className="font-semibold text-slate-300">Multi-Scenario Comparator</span>
        <button
          onClick={runComparison}
          disabled={loading}
          className="flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-orange-400 border border-slate-700 transition"
        >
          {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Sliders className="w-3 h-3" />}
          <span>Compare 3 Options</span>
        </button>
      </div>

      {comparisonData && (
        <div className="space-y-2 mt-2 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
          <div className="text-[11px] text-slate-400">
            Best Strategy: <strong className="text-green-400">{comparisonData.best_cooling_scenario}</strong>
          </div>

          <div className="space-y-1.5">
            {comparisonData.comparison_table.map((row: any, idx: number) => (
              <div
                key={idx}
                className="flex items-center justify-between p-2 rounded bg-slate-900 border border-slate-800/80 text-[11px]"
              >
                <div>
                  <div className="font-semibold text-slate-200">{row.name}</div>
                  <div className="text-[10px] text-slate-400">Est. Cost: {row.cost_inr_formatted}</div>
                </div>
                <div className="text-right">
                  <div className="font-bold text-green-400">{row.delta_T_p50.toFixed(2)}°C</div>
                  <div className="text-[9px] text-slate-500">({row.delta_T_p10.toFixed(1)} to {row.delta_T_p90.toFixed(1)})</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

