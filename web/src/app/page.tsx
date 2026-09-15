"use client";

import React, { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import { FileText, Download, Building, AlertCircle } from "lucide-react";

import { LayerSource, BasemapStyle, CityInfo } from "@/lib/types";
import { fetchHeatmapGeoJSON, fetchCellRankings } from "@/lib/api";

import { MapControls }    from "@/components/map/MapControls";
import { TimeMachine }    from "@/components/map/TimeMachine";
import { CellDetailPanel } from "@/components/panels/CellDetailPanel";
import { RankingTable }   from "@/components/panels/RankingTable";
import { CityStatsBar }   from "@/components/panels/CityStatsBar";
import { SearchAndInfo }  from "@/components/panels/SearchAndInfo";
import { ScenarioPainter } from "@/components/scenario/ScenarioPainter";
import { ReportModal }    from "@/components/panels/ReportModal";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const HeatMap = dynamic(() => import("@/components/map/HeatMap"), {
  ssr: false,
  loading: () => (
    <div className="flex h-screen w-screen items-center justify-center bg-slate-950 text-slate-400">
      Loading Chhaon Urban Heat Intelligence Engine...
    </div>
  ),
});

export default function DashboardPage() {
  const [cityId, setCityId]           = useState<string>("nagpur");
  const [cities, setCities]           = useState<CityInfo[]>([]);
  const [layerSource, setLayerSource] = useState<LayerSource>("observed");
  const [basemapStyle, setBasemapStyle] = useState<BasemapStyle>("dark");
  const [heatOpacity, setHeatOpacity] = useState<number>(0.85);
  const [selectedCellId, setSelectedCellId] = useState<string | null>(null);
  const [isPainterOpen, setIsPainterOpen]   = useState<boolean>(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState<boolean>(false);
  const [geojsonData, setGeojsonData] = useState<any>(null);
  const [rankings, setRankings]       = useState<any[]>([]);
  const [dataError, setDataError]     = useState<string | null>(null);

  // Load city list from API (reflects cities.yaml — no hardcoding)
  useEffect(() => {
    fetch(`${API_BASE}/api/v1/cities`)
      .then((r) => r.json())
      .then((data: CityInfo[]) => {
        // Only show cities that actually have data
        const available = data.filter((c) => c.data_available);
        setCities(available);
        // Default to first available city
        if (available.length > 0 && !available.find((c) => c.id === cityId)) {
          setCityId(available[0].id);
        }
      })
      .catch((err) => {
        console.error("Failed to load city list:", err);
        // Fallback to hardcoded known-good cities if API is down
        setCities([
          { id: "nagpur", name: "Nagpur, MH", data_available: true } as CityInfo,
          { id: "pune",   name: "Pune, MH",   data_available: true } as CityInfo,
        ]);
      });
  }, []);

  // Load heatmap + rankings when city changes
  useEffect(() => {
    async function loadData() {
      setDataError(null);
      setGeojsonData(null);
      setSelectedCellId(null);
      try {
        const geojson = await fetchHeatmapGeoJSON(cityId);
        setGeojsonData(geojson);
        const ranks = await fetchCellRankings(cityId);
        setRankings(ranks);
      } catch (err: any) {
        console.error(`Failed to load data for ${cityId}:`, err);
        setDataError(`Could not load data for ${cityId}. Is the API running?`);
      }
    }
    loadData();
  }, [cityId]);

  return (
    <main className="relative h-screen w-screen overflow-hidden bg-slate-950 font-sans text-slate-100">

      {/* ── Top Header ───────────────────────────────────────────────── */}
      <header className="absolute top-0 left-0 right-0 z-30 flex h-14 items-center justify-between border-b border-slate-800 bg-slate-900/90 px-4 backdrop-blur-md">

        {/* Brand + City Picker */}
        <div className="flex items-center space-x-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-orange-600 font-black text-white shadow-lg">
            छां
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-tight text-white flex items-center space-x-2">
              <span>Chhaon (छांव)</span>
              <span className="rounded bg-orange-500/20 px-1.5 py-0.5 text-[10px] font-semibold text-orange-400 border border-orange-500/30">
                v3.1
              </span>
            </h1>
            <p className="text-[10px] text-slate-400">
              Urban Heat Intelligence for Indian Cities
            </p>
          </div>

          {/* City Switcher — from API, not hardcoded */}
          <div className="ml-4 flex items-center space-x-1.5 bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1">
            <Building className="w-3.5 h-3.5 text-orange-400" />
            <select
              value={cityId}
              onChange={(e) => setCityId(e.target.value)}
              className="bg-transparent text-xs font-semibold text-white focus:outline-none cursor-pointer"
            >
              {cities.length > 0 ? (
                cities.map((c) => (
                  <option key={c.id} value={c.id} className="bg-slate-900 text-white">
                    {c.name || c.id}
                  </option>
                ))
              ) : (
                <>
                  <option value="nagpur" className="bg-slate-900 text-white">Nagpur, MH</option>
                  <option value="pune"   className="bg-slate-900 text-white">Pune, MH</option>
                </>
              )}
            </select>
          </div>
        </div>

        {/* City Stats Bar */}
        <div className="hidden xl:block">
          <CityStatsBar cityId={cityId} />
        </div>

        {/* Header Actions */}
        <div className="flex items-center space-x-2.5">
          <SearchAndInfo onSelectCell={(id) => setSelectedCellId(id)} />

          <button
            onClick={() => setIsReportModalOpen(true)}
            className="flex items-center space-x-1.5 rounded-lg bg-orange-600/90 px-3 py-1.5 text-xs font-semibold text-white shadow hover:bg-orange-500 transition"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Thermal Audit PDF</span>
          </button>

          <a
            href={`${API_BASE}/api/v1/export/${cityId}?format=geojson`}
            download
            className="flex items-center space-x-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-700 hover:text-white transition"
          >
            <Download className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">GeoJSON</span>
          </a>
        </div>
      </header>

      {/* ── Data error banner ────────────────────────────────────────── */}
      {dataError && (
        <div className="absolute top-14 left-0 right-0 z-40 flex items-center space-x-2 bg-red-950/90 border-b border-red-800 px-4 py-2 text-xs text-red-300">
          <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
          <span>{dataError}</span>
        </div>
      )}

      {/* ── Map Viewport ─────────────────────────────────────────────── */}
      <div className="absolute inset-0 pt-14">
        <HeatMap
          geojsonData={geojsonData}
          layerSource={layerSource}
          basemapStyle={basemapStyle}
          opacity={heatOpacity}
          selectedCellId={selectedCellId}
          onSelectCell={(id) => setSelectedCellId(id)}
        />
      </div>

      {/* ── Map Controls (Top-Right) ─────────────────────────────────── */}
      <div className="absolute top-16 right-3 z-20">
        <MapControls
          layerSource={layerSource}
          onSelectLayerSource={(s) => setLayerSource(s)}
          basemapStyle={basemapStyle}
          onSelectBasemapStyle={(b) => setBasemapStyle(b)}
          opacity={heatOpacity}
          onChangeOpacity={(o) => setHeatOpacity(o)}
        />
      </div>

      {/* ── Cell Detail Panel (Top-Left) ─────────────────────────────── */}
      {selectedCellId && (
        <div className="absolute top-16 left-3 bottom-[280px] z-20 w-84 max-w-[90vw]">
          <CellDetailPanel
            cellId={selectedCellId}
            cityId={cityId}
            onClose={() => setSelectedCellId(null)}
            onOpenPainter={() => setIsPainterOpen(true)}
          />
        </div>
      )}

      {/* ── Scenario Painter (Top-Left, over detail panel) ───────────── */}
      {isPainterOpen && selectedCellId && (
        <div className="absolute top-16 left-3 z-30 w-84 max-w-[90vw]">
          <ScenarioPainter
            cellId={selectedCellId}
            cityId={cityId}
            onClose={() => setIsPainterOpen(false)}
          />
        </div>
      )}

      {/* ── Time Machine (Bottom-Center) ─────────────────────────────── */}
      <div className="absolute bottom-[280px] left-1/2 -translate-x-1/2 z-20">
        <TimeMachine
          currentSource={layerSource}
          onSelectSource={(s) => setLayerSource(s)}
        />
      </div>

      {/* ── Ranking Table (Bottom Drawer) ────────────────────────────── */}
      <div className="absolute bottom-0 left-0 right-0 h-[270px] z-20">
        <RankingTable
          rankings={rankings}
          selectedCellId={selectedCellId}
          onSelectCell={(id) => setSelectedCellId(id)}
        />
      </div>

      {/* ── Report Modal ─────────────────────────────────────────────── */}
      <ReportModal
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        cityId={cityId}
      />

    </main>
  );
}
