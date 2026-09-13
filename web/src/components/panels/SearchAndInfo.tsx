"use client";

import React, { useState } from "react";
import { Search, Info, X, ShieldCheck, Database, BookOpen } from "lucide-react";

interface SearchAndInfoProps {
  onSelectCell: (cellId: string) => void;
}

export function SearchAndInfo({ onSelectCell }: SearchAndInfoProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    const formatted = searchQuery.trim().toUpperCase();
    onSelectCell(formatted.startsWith("C") || formatted.startsWith("P") ? formatted : `C${formatted.padStart(4, "0")}`);
    setSearchQuery("");
  };

  return (
    <>
      <div className="flex items-center space-x-2">
        {/* Cell Search Input */}
        <form onSubmit={handleSearch} className="relative">
          <input
            type="text"
            placeholder="Search Cell (e.g. C0426)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-40 sm:w-52 rounded-lg border border-slate-700 bg-slate-800/90 px-2.5 py-1 text-xs text-white placeholder-slate-400 focus:border-orange-500 focus:outline-none"
          />
          <button type="submit" className="absolute right-2 top-1.5 text-slate-400 hover:text-white">
            <Search className="w-3.5 h-3.5" />
          </button>
        </form>

        {/* Model Card / Info Button */}
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex h-7 w-7 items-center justify-center rounded-lg border border-slate-700 bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white transition"
          title="Methodology & Model Card"
        >
          <Info className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Model Card Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="relative w-full max-w-2xl rounded-xl border border-slate-700 bg-slate-900 p-6 shadow-2xl text-slate-100 max-h-[85vh] overflow-y-auto text-xs">
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute right-4 top-4 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center space-x-3 mb-4">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-orange-600/20 text-orange-500 border border-orange-500/30">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-bold">Chhaon Model Card & Scientific Methodology</h2>
                <p className="text-[11px] text-slate-400">TRD §7.6 & PRD Compliance v3.1</p>
              </div>
            </div>

            <div className="space-y-4 text-slate-300">
              <div className="p-3 bg-slate-800/60 rounded-lg border border-slate-700/60">
                <h3 className="font-bold text-orange-400 mb-1">Champion Model Architecture</h3>
                <p>
                  <strong>LightGBM Regressor (M2)</strong> trained with <strong>Monotone Physics Constraints</strong> (+1 on concrete, -1 on canopy, water, grass). Mathematically impossible to conclude trees heat the city.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-slate-800/60 rounded-lg border border-slate-700/60">
                  <h4 className="font-semibold text-slate-200">Honest Blocked Cross-Validation</h4>
                  <ul className="list-disc list-inside mt-1 space-y-0.5 text-slate-300">
                    <li>Spatial CV MAE: <strong>0.612°C</strong> (held-out blocks)</li>
                    <li>City-Block MAE: <strong>0.842°C</strong> (Nagpur ↔ Pune)</li>
                    <li>Null Hypothesis Test: <strong>Passed</strong> (No leakage)</li>
                  </ul>
                </div>
                <div className="p-3 bg-slate-800/60 rounded-lg border border-slate-700/60">
                  <h4 className="font-semibold text-slate-200">Satellite Sources (All Free/Open)</h4>
                  <ul className="list-disc list-inside mt-1 space-y-0.5 text-slate-300">
                    <li>NASA MODIS Terra (MOD11A1) 1km LST</li>
                    <li>ESA WorldCover 2021 (10m Land Cover)</li>
                    <li>Copernicus Sentinel-2 MSI (Indices)</li>
                    <li>JRC GHSL (Height) & VIIRS (Night Lights)</li>
                  </ul>
                </div>
              </div>

              <div className="p-3 bg-slate-800/60 rounded-lg border border-slate-700/60">
                <h3 className="font-bold text-slate-200 mb-1">Mandatory Disclaimers (FR-60)</h3>
                <p className="text-slate-400 text-[11px]">
                  Land Surface Temperature (LST) measures radiative surface skin temperature and is typically 3–12°C higher than ambient 2m air temperature during the day. Nocturnal LST is a validated proxy for nocturnal thermal recovery.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default SearchAndInfo;
