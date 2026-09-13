'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';

import MapControls from '@/components/map/MapControls';
import TimeMachine from '@/components/map/TimeMachine';
import CellDetailPanel from '@/components/panels/CellDetailPanel';
import RankingTable from '@/components/panels/RankingTable';
import CityStatsBar from '@/components/panels/CityStatsBar';
import SearchAndInfo from '@/components/panels/SearchAndInfo';
import ScenarioPainter from '@/components/scenario/ScenarioPainter';
import { fetchLayerGeoJSON, fetchCells } from '@/lib/api';
import type {
  HeatmapGeoJSON,
  CellProperties,
  CellSummary,
  LayerSource,
  TimeMode,
  DisplayMode,
  BasemapStyle,
} from '@/lib/types';
import { Info } from 'lucide-react';

// Dynamic import with ssr: false prevents MapLibre from crashing Next.js SSR
const HeatMap = dynamic(() => import('@/components/map/HeatMap'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full bg-slate-950 flex items-center justify-center text-cyan-400 text-sm font-mono animate-pulse">
      Loading interactive map engine...
    </div>
  ),
});

const CITY_ID = 'nagpur';

export default function DashboardPage() {
  const [heatmapData, setHeatmapData] = useState<HeatmapGeoJSON | null>(null);
  const [cells, setCells] = useState<CellSummary[]>([]);
  const [selectedCell, setSelectedCell] = useState<CellProperties | null>(null);
  const [showScenario, setShowScenario] = useState(false);

  const [layerSource, setLayerSource] = useState<LayerSource>('observed');
  const [timeMode, setTimeMode] = useState<TimeMode>('night');
  const [displayMode, setDisplayMode] = useState<DisplayMode>('suhii');
  const [basemapStyle, setBasemapStyle] = useState<BasemapStyle>('dark');
  const [heatmapOpacity, setHeatmapOpacity] = useState<number>(0.65);

  const leftOpen = selectedCell !== null;

  useEffect(() => {
    fetchLayerGeoJSON(CITY_ID).then(setHeatmapData).catch(console.error);
    fetchCells(CITY_ID, 50).then(setCells).catch(console.error);
  }, []);

  const handleCellClick = (cell: CellProperties) => {
    setSelectedCell(cell);
    setShowScenario(false);
  };

  const handleSelectByCellId = (cellId: string) => {
    const feature = heatmapData?.features.find(
      (f) => String(f.properties.cell_id) === String(cellId)
    );
    if (feature) {
      const p = feature.properties;
      const n = (k: keyof typeof p, fb = 0) => {
        const v = p[k];
        const parsed = typeof v === 'number' ? v : parseFloat(String(v ?? ''));
        return Number.isFinite(parsed) ? parsed : fb;
      };
      setSelectedCell({
        ...p,
        cell_id: String(p.cell_id),
        lat: n('lat'),
        lon: n('lon'),
        suhii_night: n('suhii_night'),
        suhii_day: n('suhii_day'),
        lst_day: n('lst_day'),
        lst_night: n('lst_night'),
        frac_built: n('frac_built'),
        frac_tree: n('frac_tree'),
        frac_water: n('frac_water'),
      });
      setShowScenario(false);
      return;
    }

    const row = cells.find((c) => String(c.cell_id) === String(cellId));
    if (row) {
      setSelectedCell({
        cell_id: row.cell_id,
        lat: row.lat,
        lon: row.lon,
        suhii_night: row.suhii_night,
        suhii_day: row.suhii_day,
        frac_built: row.frac_built,
        frac_tree: row.frac_tree,
        frac_water: row.frac_water,
        lst_day: 0,
        lst_night: 0,
      });
      setShowScenario(false);
    }
  };

  const layerExplanation: Record<LayerSource, string> = {
    observed: 'Satellite Observation: Real historical temperature recorded by NASA MODIS.',
    ml_fit: "AI Model Fit: The LightGBM model's understanding of the current city.",
    forecast_2031: 'AI Forecast: Projects 7 years of concrete sprawl and evaluates future heat.',
    forecast_2041: 'AI Forecast: Projects 17 years of concrete sprawl and evaluates future heat.',
  };

  return (
    <div className="w-screen h-screen bg-slate-950 relative overflow-hidden">
      {/* MAP — full background */}
      <div className="absolute inset-0 z-0">
        <HeatMap
          data={heatmapData}
          layerSource={layerSource}
          timeMode={timeMode}
          displayMode={displayMode}
          basemapStyle={basemapStyle}
          heatmapOpacity={heatmapOpacity}
          selectedCellId={selectedCell?.cell_id || null}
          onCellClick={handleCellClick}
        />
      </div>

      {/* TOP-LEFT: Brand + Search (only when left panel closed) */}
      {!leftOpen && (
        <div className="absolute top-3 left-3 z-30 flex flex-col gap-2 pointer-events-auto">
          <div className="flex items-center gap-2">
            <div className="inline-flex items-center gap-3 bg-slate-900/95 backdrop-blur-md rounded-xl shadow-2xl border border-slate-700 px-4 py-2.5">
              <div>
                <div className="flex items-baseline gap-2">
                  <h1 className="text-lg font-bold bg-gradient-to-r from-cyan-400 to-teal-400 bg-clip-text text-transparent">
                    Chhaon
                  </h1>
                  <span className="text-sm text-slate-400">(छांव)</span>
                </div>
                <p className="text-xs text-slate-500 -mt-0.5">Nagpur Urban Heat AI</p>
              </div>
            </div>
            <SearchAndInfo cells={cells} onSelectCell={handleSelectByCellId} />
          </div>
          <div className="inline-flex items-center gap-2 bg-cyan-950/80 border border-cyan-500/30 text-cyan-200 text-xs px-3 py-1.5 rounded-lg shadow-lg backdrop-blur-md max-w-md">
            <Info className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
            {layerExplanation[layerSource]}
          </div>
        </div>
      )}

      {/* TOP-RIGHT: City Stats */}
      <div className="absolute top-3 right-3 z-30 pointer-events-auto">
        <CityStatsBar data={heatmapData} />
      </div>

      {/* LEFT PANEL: Cell detail or Scenario */}
      {selectedCell && !showScenario && (
        <div className="absolute top-3 left-3 bottom-[280px] z-40 pointer-events-auto">
          <CellDetailPanel
            cell={selectedCell}
            onClose={() => setSelectedCell(null)}
            onStartScenario={() => setShowScenario(true)}
          />
        </div>
      )}
      {selectedCell && showScenario && (
        <div className="absolute top-3 left-3 bottom-[280px] z-40 pointer-events-auto">
          <ScenarioPainter
            cell={selectedCell}
            onClose={() => setShowScenario(false)}
          />
        </div>
      )}

      {/* RIGHT CONTROLS — below stats bar */}
      <div className="absolute top-[72px] right-3 z-30 pointer-events-auto">
        <MapControls
          layerSource={layerSource}
          onLayerSourceChange={setLayerSource}
          timeMode={timeMode}
          onTimeModeChange={setTimeMode}
          displayMode={displayMode}
          onDisplayModeChange={setDisplayMode}
          basemapStyle={basemapStyle}
          onBasemapStyleChange={setBasemapStyle}
          heatmapOpacity={heatmapOpacity}
          onHeatmapOpacityChange={setHeatmapOpacity}
        />
      </div>

      {/* TIME MACHINE — centered, above ranking */}
      <div className="absolute bottom-[280px] left-1/2 -translate-x-1/2 z-30 pointer-events-auto">
        <TimeMachine
          layerSource={layerSource}
          onLayerSourceChange={setLayerSource}
        />
      </div>

      {/* RANKING TABLE — bottom strip */}
      <div className="absolute bottom-0 left-0 right-0 z-30 pointer-events-auto h-[270px]">
        <RankingTable
          cells={cells}
          selectedCellId={selectedCell?.cell_id || null}
          onRowClick={handleSelectByCellId}
        />
      </div>
    </div>
  );
}
