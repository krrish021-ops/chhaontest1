"use client";

import React from "react";
import { Layers, Eye, Sun, Moon, Cpu, TrendingUp } from "lucide-react";
import { LayerSource, BasemapStyle } from "@/lib/types";

interface MapControlsProps {
  layerSource: LayerSource;
  onSelectLayerSource: (source: LayerSource) => void;
  basemapStyle: BasemapStyle;
  onSelectBasemapStyle: (style: BasemapStyle) => void;
  opacity: number;
  onChangeOpacity: (opacity: number) => void;
}

export function MapControls({
  layerSource,
  onSelectLayerSource,
  basemapStyle,
  onSelectBasemapStyle,
  opacity,
  onChangeOpacity,
}: MapControlsProps) {
  const layers: { id: LayerSource; label: string; desc: string; icon: any; color: string }[] = [
    { id: "observed", label: "Observed 2024", desc: "NASA MODIS satellite", icon: Sun, color: "from-blue-600 to-cyan-600" },
    { id: "ml_fit", label: "ML Fit 2024", desc: "LightGBM physics fit", icon: Cpu, color: "from-purple-600 to-indigo-600" },
    { id: "forecast_2031", label: "Forecast 2031", desc: "7-year sprawl", icon: TrendingUp, color: "from-orange-600 to-amber-600" },
    { id: "forecast_2041", label: "Forecast 2041", desc: "17-year sprawl", icon: TrendingUp, color: "from-red-600 to-rose-600" },
  ];

  return (
    <div className="flex flex-col space-y-2.5 w-72 rounded-xl border border-slate-700/80 bg-slate-900/95 p-3.5 shadow-2xl backdrop-blur-md text-xs text-slate-200">
      
      {/* Layer Sources */}
      <div>
        <div className="flex items-center space-x-1.5 mb-2 font-semibold text-slate-300">
          <Layers className="w-3.5 h-3.5 text-orange-400" />
          <span>Thermal Layer Source</span>
        </div>
        <div className="grid grid-cols-2 gap-1.5">
          {layers.map((l) => {
            const Icon = l.icon;
            const active = layerSource === l.id;
            return (
              <button
                key={l.id}
                onClick={() => onSelectLayerSource(l.id)}
                className={`flex flex-col text-left p-2 rounded-lg border transition ${
                  active
                    ? `bg-gradient-to-br ${l.color} text-white border-white/30 shadow-md`
                    : "bg-slate-800/80 border-slate-700/60 hover:bg-slate-800 text-slate-300"
                }`}
              >
                <div className="flex items-center space-x-1 font-bold">
                  <Icon className="w-3 h-3 flex-shrink-0" />
                  <span className="truncate">{l.label}</span>
                </div>
                <span className={`text-[9px] mt-0.5 ${active ? "text-white/80" : "text-slate-400"}`}>
                  {l.desc}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Basemap Styles */}
      <div className="pt-2 border-t border-slate-800">
        <div className="text-[11px] font-semibold text-slate-400 mb-1.5">Basemap Style</div>
        <div className="grid grid-cols-3 gap-1">
          {(["dark", "streets", "satellite"] as BasemapStyle[]).map((style) => (
            <button
              key={style}
              onClick={() => onSelectBasemapStyle(style)}
              className={`py-1 text-center capitalize rounded border transition ${
                basemapStyle === style
                  ? "bg-slate-700 text-white font-semibold border-slate-500"
                  : "bg-slate-800/60 text-slate-400 border-slate-700/50 hover:bg-slate-800"
              }`}
            >
              {style}
            </button>
          ))}
        </div>
      </div>

      {/* Opacity Slider */}
      <div className="pt-2 border-t border-slate-800">
        <div className="flex justify-between text-[11px] text-slate-400 mb-1">
          <span>Heat Layer Opacity</span>
          <span>{Math.round(opacity * 100)}%</span>
        </div>
        <input
          type="range"
          min="0.2"
          max="1.0"
          step="0.05"
          value={opacity}
          onChange={(e) => onChangeOpacity(parseFloat(e.target.value))}
          className="w-full accent-orange-500 cursor-pointer"
        />
      </div>

      {/* SUHII Legend */}
      <div className="pt-2 border-t border-slate-800">
        <div className="flex justify-between text-[10px] text-slate-400 mb-1">
          <span>Cooler (Vidarbha Oasis)</span>
          <span>Hotter (UHI Peak)</span>
        </div>
        <div className="h-2 w-full rounded bg-gradient-to-r from-blue-500 via-amber-400 to-red-600" />
        <div className="flex justify-between text-[9px] text-slate-500 mt-1 font-mono">
          <span>-3.0°C</span>
          <span>0.0°C</span>
          <span>+4.5°C</span>
        </div>
      </div>

    </div>
  );
}

export default MapControls;

