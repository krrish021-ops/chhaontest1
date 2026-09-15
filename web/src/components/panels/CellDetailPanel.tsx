"use client";

import React, { useState, useEffect } from "react";
import { X, Flame, Cpu, Sliders } from "lucide-react";
import { fetchCellExplanation, fetchCellRankings } from "@/lib/api";
import { CellExplanation, CellSummary } from "@/lib/types";
import { ScenarioComparison } from "@/components/scenario/ScenarioComparison";

interface CellDetailPanelProps {
  cellId: string;
  cityId: string;
  onClose: () => void;
  onOpenPainter: () => void;
}

// Human-readable labels for raw feature keys (presentation only —
// the underlying values are real, this just relabels them nicely).
const FEATURE_LABELS: Record<string, string> = {
  frac_built: "Impervious Built Surface",
  frac_tree: "Tree Canopy Coverage",
  frac_water: "Water Body Coverage",
  frac_crop: "Farmland / Cropland",
  frac_grass: "Open Grass / Parkland",
};

export function CellDetailPanel({ cellId, cityId, onClose, onOpenPainter }: CellDetailPanelProps) {
  const [activeTab, setActiveTab] = useState<"current" | "ai" | "compare">("current");
  const [explanation, setExplanation] = useState<CellExplanation | null>(null);
  const [cellStats, setCellStats] = useState<CellSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [statsLoading, setStatsLoading] = useState(false);

  useEffect(() => {
    if (!cellId) return;

    async function loadExplain() {
      setLoading(true);
      try {
        const data = await fetchCellExplanation(cellId);
        setExplanation(data);
      } catch (err) {
        console.error("Failed to load explanation:", err);
        setExplanation(null);
      } finally {
        setLoading(false);
      }
    }

    async function loadStats() {
      setStatsLoading(true);
      try {
        // Fetch a large slice so we can find this specific cell
        // regardless of its rank (city grids are small: 229-414 cells).
        const all = await fetchCellRankings(cityId, "suhii_night", 500);
        const match = all.find((c) => c.cell_id.toUpperCase() === cellId.toUpperCase());
        setCellStats(match ?? null);
      } catch (err) {
        console.error("Failed to load cell stats:", err);
        setCellStats(null);
      } finally {
        setStatsLoading(false);
      }
    }

    loadExplain();
    loadStats();
  }, [cellId, cityId]);

  return (
    <div className="flex flex-col h-full rounded-xl border border-slate-700/80 bg-slate-900/95 p-4 shadow-2xl backdrop-blur-md text-xs text-slate-200 overflow-y-auto">

      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3">
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-mono font-black text-sm text-white">{cellId}</span>
            <span className="rounded bg-orange-600/20 text-orange-400 border border-orange-500/30 px-1.5 py-0.5 text-[10px]">
              Active Zone
            </span>
          </div>
          <p className="text-[10px] text-slate-400">1km × 1km Municipal Analysis Cell</p>
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-white">
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 border-b border-slate-800 pb-2 mb-3">
        {[
          { id: "current", label: "Overview" },
          { id: "ai", label: "AI Diagnosis" },
          { id: "compare", label: "Comparator" },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id as any)}
            className={`flex-1 py-1 text-center rounded transition font-medium ${
              activeTab === t.id
                ? "bg-orange-600 text-white"
                : "bg-slate-800/60 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab 1: Current Overview */}
      {activeTab === "current" && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2">
            <div className="p-2.5 rounded-lg bg-slate-800/80 border border-slate-700/60">
              <div className="text-[10px] text-slate-400 font-semibold">Night SUHII Anomaly</div>
              <div className="text-base font-bold text-orange-400 mt-0.5">
                {loading
                  ? "…"
                  : explanation
                  ? `+${explanation.night_suhii_degC.toFixed(2)}°C`
                  : "N/A"}
              </div>
              <div className="text-[9px] text-slate-500">Above Rural Baseline</div>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-800/80 border border-slate-700/60">
              <div className="text-[10px] text-slate-400 font-semibold">Day Surface Temp</div>
              <div className="text-base font-bold text-slate-200 mt-0.5">
                {statsLoading
                  ? "…"
                  : cellStats
                  ? `${cellStats.lst_day.toFixed(1)}°C`
                  : "N/A"}
              </div>
              <div className="text-[9px] text-slate-500">MODIS Terra Peak</div>
            </div>
          </div>

          {cellStats && (
            <div className="grid grid-cols-2 gap-2">
              <div className="p-2.5 rounded-lg bg-slate-800/80 border border-slate-700/60">
                <div className="text-[10px] text-slate-400 font-semibold">Day SUHII</div>
                <div className="text-sm font-bold text-slate-200 mt-0.5">
                  {cellStats.suhii_day >= 0 ? "+" : ""}
                  {cellStats.suhii_day.toFixed(2)}°C
                </div>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-800/80 border border-slate-700/60">
                <div className="text-[10px] text-slate-400 font-semibold">Night LST</div>
                <div className="text-sm font-bold text-slate-200 mt-0.5">
                  {cellStats.lst_night.toFixed(1)}°C
                </div>
              </div>
            </div>
          )}

          {/* Action Trigger */}
          <button
            onClick={onOpenPainter}
            className="w-full py-2 rounded-lg bg-orange-600 hover:bg-orange-500 text-white font-semibold text-xs shadow-md transition flex items-center justify-center space-x-1.5"
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>Open Scenario Painter Studio</span>
          </button>
        </div>
      )}

      {/* Tab 2: AI Diagnosis (SHAP) */}
      {activeTab === "ai" && (
        <div className="space-y-2.5">
          <div className="text-[11px] font-semibold text-slate-300 flex items-center space-x-1">
            <Cpu className="w-3.5 h-3.5 text-purple-400" />
            <span>SHAP Machine Learning Attribution</span>
          </div>

          {loading ? (
            <div className="text-center py-6 text-slate-500">Calculating SHAP drivers...</div>
          ) : explanation && explanation.drivers && explanation.drivers.length > 0 ? (
            <div className="space-y-2">
              {explanation.drivers.map((d, i) => {
                const isWarming = d.shap_contribution_degC >= 0;
                const label = FEATURE_LABELS[d.feature] ?? d.feature;
                return (
                  <div key={i} className="p-2 rounded bg-slate-800/60 border border-slate-700/50">
                    <div className="flex justify-between items-center text-[11px]">
                      <span className="font-semibold text-slate-200">{label}</span>
                      <strong className={isWarming ? "text-red-400" : "text-green-400"}>
                        {isWarming ? "+" : ""}
                        {d.shap_contribution_degC.toFixed(2)}°C
                      </strong>
                    </div>
                    <p className="text-[10px] text-slate-400 mt-0.5">{d.text}</p>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-slate-400">Attribution data unavailable for this cell.</div>
          )}
        </div>
      )}

      {/* Tab 3: Multi-Scenario Comparator */}
      {activeTab === "compare" && (
        <ScenarioComparison cellId={cellId} cityId={cityId} />
      )}

    </div>
  );
}

export default CellDetailPanel;
