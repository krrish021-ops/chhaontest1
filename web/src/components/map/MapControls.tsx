'use client';

import { Sun, Moon, Satellite, Brain, Sparkles, TrendingUp, Map, Layers, Eye } from 'lucide-react';
import type { LayerSource, TimeMode, DisplayMode, BasemapStyle } from '@/lib/types';

interface MapControlsProps {
  layerSource: LayerSource;
  onLayerSourceChange: (source: LayerSource) => void;
  timeMode: TimeMode;
  onTimeModeChange: (mode: TimeMode) => void;
  displayMode: DisplayMode;
  onDisplayModeChange: (mode: DisplayMode) => void;
  basemapStyle: BasemapStyle;
  onBasemapStyleChange: (style: BasemapStyle) => void;
  heatmapOpacity: number;
  onHeatmapOpacityChange: (opacity: number) => void;
}

const LAYER_OPTIONS: {
  id: LayerSource;
  label: string;
  sublabel: string;
  icon: any;
  color: string;
}[] = [
  {
    id: 'observed',
    label: 'Observed',
    sublabel: '2024 · Real',
    icon: Satellite,
    color: 'from-blue-500 to-cyan-500',
  },
  {
    id: 'ml_fit',
    label: 'ML Fit',
    sublabel: '2024 · Model',
    icon: Brain,
    color: 'from-purple-500 to-pink-500',
  },
  {
    id: 'forecast_2031',
    label: 'Forecast',
    sublabel: '2031 · +7yr',
    icon: Sparkles,
    color: 'from-orange-500 to-red-500',
  },
  {
    id: 'forecast_2041',
    label: 'Forecast',
    sublabel: '2041 · +17yr',
    icon: TrendingUp,
    color: 'from-red-600 to-rose-700',
  },
];

const BASEMAP_OPTIONS: {
  id: BasemapStyle;
  label: string;
  icon: any;
}[] = [
  { id: 'dark', label: 'Dark Canvas', icon: Layers },
  { id: 'streets', label: 'Detailed Streets (OSM)', icon: Map },
  { id: 'satellite', label: 'Satellite Aerial', icon: Satellite },
];

export default function MapControls({
  layerSource,
  onLayerSourceChange,
  timeMode,
  onTimeModeChange,
  displayMode,
  onDisplayModeChange,
  basemapStyle,
  onBasemapStyleChange,
  heatmapOpacity,
  onHeatmapOpacityChange,
}: MapControlsProps) {
  return (
    /* NO ABSOLUTE POSITIONING - Managed by parent in page.tsx */
    <div className="flex flex-col gap-3 max-h-[calc(100vh-6rem)] overflow-y-auto pr-1 w-[340px]">
      
      {/* Basemap Style Selector */}
      <div className="bg-slate-900/95 backdrop-blur-md rounded-xl shadow-2xl border border-slate-700 p-3">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
          <Map className="w-3.5 h-3.5 text-cyan-400" />
          Basemap Detail
        </div>
        <div className="grid grid-cols-3 gap-1.5">
          {BASEMAP_OPTIONS.map((style) => {
            const Icon = style.icon;
            const isActive = basemapStyle === style.id;
            return (
              <button
                key={style.id}
                onClick={() => onBasemapStyleChange(style.id)}
                className={`
                  p-2 rounded-lg text-center transition-all flex flex-col items-center gap-1
                  ${
                    isActive
                      ? 'bg-cyan-500 text-white shadow-lg font-semibold'
                      : 'bg-slate-800/50 text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                  }
                `}
              >
                <Icon className="w-4 h-4" />
                <span className="text-[10px] leading-tight">{style.label}</span>
              </button>
            );
          })}
        </div>

        {/* Opacity Slider */}
        <div className="mt-3 pt-2 border-t border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span className="flex items-center gap-1 text-[11px]">
              <Eye className="w-3 h-3 text-slate-400" /> Heat Layer Transparency
            </span>
            <span className="font-mono text-[11px] text-cyan-400">
              {Math.round(heatmapOpacity * 100)}%
            </span>
          </div>
          <input
            type="range"
            min={0.2}
            max={0.95}
            step={0.05}
            value={heatmapOpacity}
            onChange={(e) => onHeatmapOpacityChange(Number(e.target.value))}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
          />
        </div>
      </div>

      {/* Layer Source Selector */}
      <div className="bg-slate-900/95 backdrop-blur-md rounded-xl shadow-2xl border border-slate-700 p-3">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          Data Forecast Model
        </div>
        <div className="grid grid-cols-2 gap-2">
          {LAYER_OPTIONS.map((option) => {
            const Icon = option.icon;
            const isActive = layerSource === option.id;
            return (
              <button
                key={option.id}
                onClick={() => onLayerSourceChange(option.id)}
                className={`
                  relative overflow-hidden rounded-lg p-2.5 text-left transition-all
                  ${
                    isActive
                      ? `bg-gradient-to-br ${option.color} shadow-lg scale-[1.02]`
                      : 'bg-slate-800/50 hover:bg-slate-800 border border-slate-700/50'
                  }
                `}
              >
                <div className="flex items-start gap-2">
                  <Icon
                    className={`w-4 h-4 mt-0.5 shrink-0 ${
                      isActive ? 'text-white' : 'text-slate-400'
                    }`}
                  />
                  <div>
                    <div
                      className={`text-sm font-semibold leading-tight ${
                        isActive ? 'text-white' : 'text-slate-200'
                      }`}
                    >
                      {option.label}
                    </div>
                    <div
                      className={`text-[10px] uppercase tracking-wider mt-0.5 ${
                        isActive ? 'text-white/80' : 'text-slate-500'
                      }`}
                    >
                      {option.sublabel}
                    </div>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Time Mode Toggle */}
      <div className="bg-slate-900/95 backdrop-blur-md rounded-xl shadow-2xl border border-slate-700 p-3">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
          Overpass Time
        </div>
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => onTimeModeChange('day')}
            className={`
              flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all
              ${
                timeMode === 'day'
                  ? 'bg-amber-500 text-white shadow-lg'
                  : 'bg-slate-800/50 text-slate-300 hover:bg-slate-800'
              }
            `}
          >
            <Sun className="w-4 h-4" />
            Day LST
          </button>
          <button
            onClick={() => onTimeModeChange('night')}
            className={`
              flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all
              ${
                timeMode === 'night'
                  ? 'bg-indigo-500 text-white shadow-lg'
                  : 'bg-slate-800/50 text-slate-300 hover:bg-slate-800'
              }
            `}
          >
            <Moon className="w-4 h-4" />
            Night LST
          </button>
        </div>
      </div>

      {/* Display Mode Toggle */}
      <div className="bg-slate-900/95 backdrop-blur-md rounded-xl shadow-2xl border border-slate-700 p-3">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
          Display Mode
        </div>
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => onDisplayModeChange('suhii')}
            className={`
              px-3 py-2 rounded-lg text-sm font-medium transition-all
              ${
                displayMode === 'suhii'
                  ? 'bg-rose-500 text-white shadow-lg'
                  : 'bg-slate-800/50 text-slate-300 hover:bg-slate-800'
              }
            `}
          >
            SUHII Anomaly
          </button>
          <button
            onClick={() => onDisplayModeChange('absolute')}
            className={`
              px-3 py-2 rounded-lg text-sm font-medium transition-all
              ${
                displayMode === 'absolute'
                  ? 'bg-emerald-500 text-white shadow-lg'
                  : 'bg-slate-800/50 text-slate-300 hover:bg-slate-800'
              }
            `}
          >
            Absolute °C
          </button>
        </div>
      </div>

      {/* Legend */}
      <div className="bg-slate-900/95 backdrop-blur-md rounded-xl shadow-2xl border border-slate-700 p-3">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
          {displayMode === 'suhii' ? 'SUHII (°C above Rural)' : 'Surface Temperature (°C)'}
        </div>
        <div className="h-2 rounded-full bg-gradient-to-r from-blue-500 via-yellow-300 via-orange-500 to-red-600" />
        <div className="flex justify-between mt-1.5 text-[10px] text-slate-400 font-mono">
          {displayMode === 'suhii' ? (
            <>
              <span>&lt; -2°C</span>
              <span>0°C</span>
              <span>+2°C</span>
              <span>+4°C</span>
              <span>&gt; +6°C</span>
            </>
          ) : (
            <>
              <span>25°C</span>
              <span>30°C</span>
              <span>35°C</span>
              <span>40°C</span>
              <span>&gt; 45°C</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
