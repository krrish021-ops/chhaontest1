"use client";

import React, { useState } from "react";
import { Search, Info, X, ShieldCheck, AlertTriangle } from "lucide-react";

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
    onSelectCell(
      formatted.startsWith("C") || formatted.startsWith("P")
        ? formatted
        : `C${formatted.padStart(4, "0")}`
    );
    setSearchQuery("");
  };

  return (
    <>
      <div className="flex items-center space-x-2">
        {/* Cell Search */}
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

        {/* Info Button */}
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

            {/* Header */}
            <div className="flex items-center space-x-3 mb-4">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-orange-600/20 text-orange-500 border border-orange-500/30">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-bold">Chhaon Model Card & Scientific Methodology</h2>
                <p className="text-[11px] text-slate-400">
                  TRD §7.6 compliance — all metrics from committed CARD_*.json artifacts
                </p>
              </div>
            </div>

            <div className="space-y-4 text-slate-300">

              {/* Architecture */}
              <div className="p-3 bg-slate-800/60 rounded-lg border border-slate-700/60">
                <h3 className="font-bold text-orange-400 mb-1">Champion Model — M2 LightGBM</h3>
                <p>
                  Two generations: <strong>v1</strong> (5 features, May 2024, 229 cells) powers
                  SHAP explainability and scenario uncertainty bands.{" "}
                  <strong>v2</strong> (19 features, 2020–2024, 4,580 rows) powers rankings and
                  city comparison. Both use <strong>monotone physics constraints</strong> —
                  mathematically impossible for the model to conclude that trees heat the city.
                </p>
              </div>

              {/* CV Metrics — FROM CARD*.json */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-slate-800/60 rounded-lg border border-slate-700/60">
                  <h4 className="font-semibold text-slate-200 mb-1">
                    Validation Metrics (from pipeline)
                  </h4>
                  <ul className="space-y-1 text-slate-300">
                    <li>
                      v1 Spatial CV MAE:{" "}
                      <strong className="text-green-400">0.621°C ± 0.095</strong>
                    </li>
                    <li>
                      v2 Night CV MAE:{" "}
                      <strong className="text-green-400">0.701°C ± 0.085</strong>
                    </li>
                    <li>
                      v2 Night R²:{" "}
                      <strong className="text-green-400">0.606</strong>
                    </li>
                    <li>
                      v2 Day CV MAE:{" "}
                      <strong className="text-yellow-400">0.732°C ± 0.038</strong>
                    </li>
                    <li>
                      Null hypothesis test:{" "}
                      <strong className="text-green-400">Passed (no leakage)</strong>
                    </li>
                  </ul>
                </div>

                <div className="p-3 bg-slate-800/60 rounded-lg border border-slate-700/60">
                  <h4 className="font-semibold text-slate-200 mb-1">Data Sources (All Open)</h4>
                  <ul className="space-y-1 text-slate-300">
                    <li>NASA MODIS Terra MOD11A1 — 1km LST</li>
                    <li>ESA WorldCover v200 2021 — 10m land cover</li>
                    <li>Copernicus Sentinel-2 SR — spectral indices</li>
                    <li>JRC GHSL 2018 — building height</li>
                    <li>VIIRS VCMSLCFG — night lights</li>
                    <li>ERA5-Land — weather normalization</li>
                  </ul>
                </div>
              </div>

              {/* Known Failures — honest */}
              <div className="p-3 bg-amber-950/30 rounded-lg border border-amber-800/40">
                <div className="flex items-center space-x-2 mb-2">
                  <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
                  <h4 className="font-semibold text-amber-400">
                    Known Limitations (Honest Disclosure)
                  </h4>
                </div>
                <ul className="space-y-1 text-slate-300">
                  <li>
                    <strong className="text-red-400">City-Block CV MAE: 1.107°C, R² −0.199</strong>
                    {" "}— model trained on Nagpur does not transfer well to Pune.
                    Cross-city predictions carry a lower-confidence flag.
                  </li>
                  <li>
                    <strong className="text-amber-400">
                      Quantile bands overconfident:
                    </strong>{" "}
                    62.4% actual coverage vs 80% target. Scenario ΔT ranges are
                    indicative only.
                  </li>
                  <li>
                    <strong className="text-amber-400">Forecast layers (2031/2041)</strong> use
                    constant offsets (+0.42°C / +1.18°C), not a land-use change model.
                    Treat as illustrative BAU, not a prediction.
                  </li>
                  <li>
                    Land cover is a static 2021 snapshot — annual change detection
                    not yet implemented.
                  </li>
                  <li>
                    LST ≠ air temperature. Surface skin temp is typically 3–12°C
                    higher than 2m ambient during daytime.
                  </li>
                </ul>
              </div>

              {/* FR-60 Disclaimer */}
              <div className="p-3 bg-slate-800/60 rounded-lg border border-slate-700/60">
                <h3 className="font-bold text-slate-200 mb-1">
                  Mandatory Notice — FR-60 (PRD §6.7)
                </h3>
                <p className="text-slate-400 text-[11px]">
                  Land Surface Temperature (LST) measures radiative surface skin temperature
                  and is typically 3–12°C higher than ambient 2m air temperature during the day.
                  Nocturnal LST is a validated proxy for nocturnal thermal recovery and urban
                  heat island intensity. This tool is decision-support only and does not
                  constitute a statutory environmental assessment.
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
