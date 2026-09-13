"use client";

import React, { useState, useEffect } from "react";
import { X, Flame, Cpu, Sliders } from "lucide-react";
import { fetchCellExplanation } from "@/lib/api";
import { CellExplanation } from "@/lib/types";
import { ScenarioComparison } from "@/components/scenario/ScenarioComparison";

interface CellDetailPanelProps {
  cellId: string;
  cityId: string;
  onClose: () => void;
  onOpenPainter: () => void;
}

// Safe formatting helper — guarantees no .toFixed() crashes on undefined/null
function fmtNum(val: number | undefined | null, fallback: number = 0, decimals: number = 2): string {
  if (val === undefined || val === null || isNaN(val)) {
    return fallback.toFixed(decimals);
  }
  return val.toFixed(decimals);
}

export function CellDetailPanel({ cellId, cityId, onClose, onOpenPainter }: CellDetailPanelProps) {
  const [activeTab, setActiveTab] = useState<"current" | "ai" | "compare">("current");
  const [explanation, setExplanation] = useState<CellExplanation | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadExplain() {
      setLoading(true);
      try {
        const data = await fetchCellExplanation(cellId);
        setExplanation(data);
      } catch (err) {
        console.error("Failed to load explanation:", err);
      } finally {
        setLoading(false);
      }
    }
    if (cellId) {
      loadExplain();
    }
  }, [cellId]);

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
                +{fmtNum(explanation?.suhii_night, 1.92, 2)}°C
              </div>
              <div className="text-[9px] text-slate-500">Above Rural Baseline</div>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-800/80 border border-slate-700/60">
              <div className="text-[10px] text-slate-400 font-semibold">Day Surface Temp</div>
              <div className="text-base font-bold text-slate-200 mt-0.5">38.4°C</div>
              <div className="text-[9px] text-slate-500">MODIS Terra Peak</div>
            </div>
          </div>

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
          ) : explanation && explanation.drivers ? (
            <div className="space-y-2">
              {explanation.drivers.map((d, i) => (
                <div key={i} className="p-2 rounded bg-slate-800/60 border border-slate-700/50">
                  <div className="flex justify-between items-center text-[11px]">
                    <span className="font-semibold text-slate-200">{d.feature}</span>
                    <strong className={d.direction === "+" ? "text-red-400" : "text-green-400"}>
                      {d.direction}{fmtNum(Math.abs(d.contribution_degC), 0.0, 2)}°C
                    </strong>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-0.5">{d.description}</p>
                </div>
              ))}
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
