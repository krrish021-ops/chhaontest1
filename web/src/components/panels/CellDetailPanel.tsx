"use client";

import React, { useState, useEffect } from "react";
import { X, Cpu, Sliders, AlertTriangle } from "lucide-react";
import { fetchCellExplanation, fetchCellRankings } from "@/lib/api";
import { CellExplanation, CellSummary } from "@/lib/types";
import { ScenarioComparison } from "@/components/scenario/ScenarioComparison";

interface CellDetailPanelProps {
  cellId: string;
  cityId: string;
  onClose: () => void;
  onOpenPainter: () => void;
}

const FEATURE_LABELS: Record<string, string> = {
  frac_built: "Impervious Built Surface",
  frac_tree:  "Tree Canopy Coverage",
  frac_water: "Water Body Coverage",
  frac_crop:  "Farmland / Cropland",
  frac_grass: "Open Grass / Parkland",
};

// Safe formatters — never crash on null/undefined
const fmt1 = (v: number | null | undefined) =>
  v != null ? `${v.toFixed(1)}°C` : "—";

const fmt2signed = (v: number | null | undefined) =>
  v != null ? `${v >= 0 ? "+" : ""}${v.toFixed(2)}°C` : "—";

const fmtPct = (v: number | null | undefined) =>
  v != null ? `${(v * 100).toFixed(0)}%` : "—";

export function CellDetailPanel({
  cellId,
  cityId,
  onClose,
  onOpenPainter,
}: CellDetailPanelProps) {
  const [activeTab, setActiveTab]     = useState<"current" | "ai" | "compare">("current");
  const [explanation, setExplanation] = useState<CellExplanation | null>(null);
  const [cellStats, setCellStats]     = useState<CellSummary | null>(null);
  const [loading, setLoading]         = useState(false);
  const [statsLoading, setStatsLoading] = useState(false);
  const [shapError, setShapError]     = useState<string | null>(null);

  useEffect(() => {
    if (!cellId) return;

    async function loadExplain() {
      setLoading(true);
      setShapError(null);
      try {
        const data = await fetchCellExplanation(cellId);
        setExplanation(data);
      } catch (err: any) {
        console.error("Failed to load explanation:", err);
        setExplanation(null);
        setShapError(
          err?.message?.includes("503") || err?.message?.includes("unavailable")
            ? "SHAP data requires the Parquet feature tables (run the GEE pipeline first)."
            : "Attribution data unavailable for this cell."
        );
      } finally {
        setLoading(false);
      }
    }

    async function loadStats() {
      setStatsLoading(true);
      try {
        const all = await fetchCellRankings(cityId, "suhii_night", 500);
        const match = all.find(
          (c: any) => c.cell_id.toUpperCase() === cellId.toUpperCase()
        );
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
          { id: "ai",      label: "SHAP Drivers" },
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

      {/* Tab 1: Overview */}
      {activeTab === "current" && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2">

            {/* Night SUHII */}
            <div className="p-2.5 rounded-lg bg-slate-800/80 border border-slate-700/60">
              <div className="text-[10px] text-slate-400 font-semibold">Night SUHII</div>
              <div className="text-base font-bold text-orange-400 mt-0.5">
                {loading
                  ? "…"
                  : explanation
                  ? fmt2signed(explanation.night_suhii_degC)
                  : statsLoading
                  ? "…"
                  : fmt2signed(cellStats?.suhii_night)}
              </div>
              <div className="text-[9px] text-slate-500">Above Rural Baseline</div>
            </div>

            {/* Day LST */}
            <div className="p-2.5 rounded-lg bg-slate-800/80 border border-slate-700/60">
              <div className="text-[10px] text-slate-400 font-semibold">Day Surface Temp</div>
              <div className="text-base font-bold text-slate-200 mt-0.5">
                {statsLoading ? "…" : fmt1(cellStats?.lst_day)}
              </div>
              <div className="text-[9px] text-slate-500">MODIS Terra Peak</div>
            </div>
          </div>

          {/* Day SUHII + Night LST */}
          {cellStats && (
            <div className="grid grid-cols-2 gap-2">
              <div className="p-2.5 rounded-lg bg-slate-800/80 border border-slate-700/60">
                <div className="text-[10px] text-slate-400 font-semibold">Day SUHII</div>
                <div className="text-sm font-bold text-slate-200 mt-0.5">
                  {fmt2signed(cellStats.suhii_day)}
                </div>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-800/80 border border-slate-700/60">
                <div className="text-[10px] text-slate-400 font-semibold">Night LST</div>
                <div className="text-sm font-bold text-slate-200 mt-0.5">
                  {fmt1(cellStats.lst_night)}
                </div>
              </div>
            </div>
          )}

          {/* Land cover fractions */}
          {cellStats && (
            <div className="p-2.5 rounded-lg bg-slate-800/80 border border-slate-700/60 space-y-1">
              <div className="text-[10px] font-semibold text-slate-400 mb-1">
                Land Cover (ESA WorldCover 2021)
              </div>
              {[
                { label: "Built-up",  val: cellStats.frac_built, color: "text-red-400" },
                { label: "Tree",      val: cellStats.frac_tree,  color: "text-green-400" },
                { label: "Water",     val: cellStats.frac_water, color: "text-blue-400" },
                { label: "Crop",      val: cellStats.frac_crop,  color: "text-yellow-400" },
                { label: "Grass",     val: cellStats.frac_grass, color: "text-emerald-400" },
              ].map((item) => (
                <div key={item.label} className="flex justify-between items-center">
                  <span className="text-slate-400">{item.label}</span>
                  <span className={`font-semibold ${item.color}`}>
                    {fmtPct(item.val)}
                  </span>
                </div>
              ))}
            </div>
          )}

          {!cellStats && !statsLoading && (
            <div className="text-slate-500 text-center py-2">
              Cell data not found in current rankings.
            </div>
          )}

          <button
            onClick={onOpenPainter}
            className="w-full py-2 rounded-lg bg-orange-600 hover:bg-orange-500 text-white font-semibold text-xs shadow-md transition flex items-center justify-center space-x-1.5"
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>Open Scenario Simulator</span>
          </button>
        </div>
      )}

      {/* Tab 2: SHAP Drivers */}
      {activeTab === "ai" && (
        <div className="space-y-2.5">
          <div className="text-[11px] font-semibold text-slate-300 flex items-center space-x-1">
            <Cpu className="w-3.5 h-3.5 text-purple-400" />
            <span>SHAP Attribution — LightGBM v1 TreeExplainer</span>
          </div>

          {/* Note about v1 schema */}
          <div className="text-[10px] text-slate-500 bg-slate-800/40 rounded p-2 border border-slate-700/40">
            5-feature v1 model (built, tree, water, crop, grass).
            v2's 19-feature attribution is not yet wired to SHAP.
          </div>

          {loading ? (
            <div className="text-center py-6 text-slate-500">
              Computing SHAP drivers...
            </div>
          ) : shapError ? (
            <div className="flex items-start space-x-2 text-[11px] text-amber-400 bg-amber-950/30 p-2.5 rounded-lg border border-amber-800/40">
              <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
              <span>{shapError}</span>
            </div>
          ) : explanation?.drivers?.length ? (
            <div className="space-y-2">
              {explanation.drivers.map((d, i) => {
                const isWarming = d.shap_contribution_degC >= 0;
                const label = FEATURE_LABELS[d.feature] ?? d.feature;
                return (
                  <div
                    key={i}
                    className="p-2 rounded bg-slate-800/60 border border-slate-700/50"
                  >
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
            <div className="text-slate-400 text-center py-4">
              No attribution data available for this cell.
            </div>
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
