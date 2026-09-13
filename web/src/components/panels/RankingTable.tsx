"use client";

import React, { useState } from "react";
import { Download, ChevronUp, ChevronDown, Flame } from "lucide-react";
import { CellSummary } from "@/lib/types";

interface RankingTableProps {
  rankings: CellSummary[];
  selectedCellId: string | null;
  onSelectCell: (cellId: string) => void;
}

export function RankingTable({ rankings, selectedCellId, onSelectCell }: RankingTableProps) {
  const [filter, setFilter] = useState<"all" | "hot" | "cool" | "canopy">("all");
  const [isCollapsed, setIsCollapsed] = useState(false);

  const filtered = rankings.filter((r) => {
    if (filter === "hot") return r.suhii_night >= 2.5;
    if (filter === "cool") return r.suhii_night < 1.0;
    if (filter === "canopy") return (r.frac_tree || 0) >= 0.2;
    return true;
  });

  const exportCSV = () => {
    const headers = ["Cell_ID", "Night_SUHII_degC", "Day_LST_degC", "Night_LST_degC", "Built_Fraction", "Tree_Fraction"];
    const rows = rankings.map((r) => [
      r.cell_id,
      r.suhii_night?.toFixed(2) || "0.00",
      r.lst_day?.toFixed(1) || "0.0",
      r.lst_night?.toFixed(1) || "0.0",
      ((r.frac_built || 0) * 100).toFixed(0) + "%",
      ((r.frac_tree || 0) * 100).toFixed(0) + "%",
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map((e) => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "chhaon_ward_rankings.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="h-full w-full border-t border-slate-800 bg-slate-900/95 backdrop-blur-md flex flex-col text-xs text-slate-200">
      
      {/* Header Controls */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-slate-800">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 font-bold text-slate-100">
            <Flame className="w-4 h-4 text-orange-500" />
            <span>Hotspot Triage & Ward Ranking Table</span>
            <span className="text-[10px] text-slate-400 font-normal">({filtered.length} cells)</span>
          </div>

          {/* Filter Chips */}
          <div className="flex space-x-1">
            {[
              { id: "all", label: "All" },
              { id: "hot", label: "🔥 Hotspots (>2.5°C)" },
              { id: "cool", label: "❄️ Cool Zones" },
              { id: "canopy", label: "🌳 High Canopy" },
            ].map((f) => (
              <button
                key={f.id}
                onClick={() => setFilter(f.id as any)}
                className={`px-2 py-0.5 rounded text-[10px] transition ${
                  filter === f.id
                    ? "bg-orange-600 text-white font-semibold"
                    : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={exportCSV}
            className="flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition text-[11px]"
          >
            <Download className="w-3 h-3" />
            <span>Export CSV</span>
          </button>
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="text-slate-400 hover:text-white"
          >
            {isCollapsed ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Table Content */}
      {!isCollapsed && (
        <div className="flex-1 overflow-auto">
          <table className="w-full text-left border-collapse text-[11px]">
            <thead className="sticky top-0 bg-slate-950 text-slate-400 font-semibold border-b border-slate-800">
              <tr>
                <th className="py-1.5 px-3">Cell ID</th>
                <th className="py-1.5 px-3">Night SUHII (°C)</th>
                <th className="py-1.5 px-3">Day LST (°C)</th>
                <th className="py-1.5 px-3">Night LST (°C)</th>
                <th className="py-1.5 px-3">Built-up %</th>
                <th className="py-1.5 px-3">Canopy %</th>
                <th className="py-1.5 px-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((row) => {
                const isSelected = selectedCellId === row.cell_id;
                const isHot = row.suhii_night >= 2.5;
                return (
                  <tr
                    key={row.cell_id}
                    onClick={() => onSelectCell(row.cell_id)}
                    className={`cursor-pointer border-b border-slate-800/50 transition hover:bg-slate-800/80 ${
                      isSelected ? "bg-orange-950/40 border-l-4 border-l-orange-500" : ""
                    }`}
                  >
                    <td className="py-1.5 px-3 font-mono font-semibold text-slate-200">{row.cell_id}</td>
                    <td className="py-1.5 px-3">
                      <span className={`font-bold ${isHot ? "text-red-400" : "text-orange-400"}`}>
                        +{row.suhii_night?.toFixed(2) || "0.00"}°C
                      </span>
                    </td>
                    <td className="py-1.5 px-3 text-slate-300">{row.lst_day?.toFixed(1) || "0.0"}°C</td>
                    <td className="py-1.5 px-3 text-slate-300">{row.lst_night?.toFixed(1) || "0.0"}°C</td>
                    <td className="py-1.5 px-3 text-slate-300">{((row.frac_built || 0) * 100).toFixed(0)}%</td>
                    <td className="py-1.5 px-3 text-slate-300">{((row.frac_tree || 0) * 100).toFixed(0)}%</td>
                    <td className="py-1.5 px-3">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectCell(row.cell_id);
                        }}
                        className="px-2 py-0.5 rounded bg-orange-600/80 hover:bg-orange-500 text-white text-[10px]"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

    </div>
  );
}

export default RankingTable;
