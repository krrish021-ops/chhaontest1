"use client";

import React, { useState, useEffect } from "react";
import { Play, Pause, RotateCcw, AlertTriangle } from "lucide-react";
import { LayerSource } from "@/lib/types";

interface TimeMachineProps {
  currentSource: LayerSource;
  onSelectSource: (source: LayerSource) => void;
}

const TIMELINE: {
  id: LayerSource;
  year: string;
  label: string;
  disclaimer: string | null;
}[] = [
  {
    id: "observed",
    year: "2024",
    label: "Observed",
    disclaimer: null,
  },
  {
    id: "ml_fit",
    year: "2024",
    label: "Normalized",
    disclaimer:
      "Weather-normalized SUHII — ERA5 anomaly removed. " +
      "Not a separate model prediction; same observed values " +
      "after weather signal extraction.",
  },
  {
    id: "forecast_2031",
    year: "2031",
    label: "BAU Estimate",
    disclaimer:
      "⚠ Illustrative only — observed + constant +0.42°C offset. " +
      "No land-use change model (M4) exists yet. " +
      "Do not cite as a predictive projection.",
  },
  {
    id: "forecast_2041",
    year: "2041",
    label: "BAU Estimate",
    disclaimer:
      "⚠ Illustrative only — observed + constant +1.18°C offset. " +
      "No land-use change model (M4) exists yet. " +
      "Do not cite as a predictive projection.",
  },
];

export function TimeMachine({ currentSource, onSelectSource }: TimeMachineProps) {
  const [isPlaying, setIsPlaying] = useState(false);

  const activeStep = TIMELINE.find((t) => t.id === currentSource) ?? TIMELINE[0];

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (isPlaying) {
      interval = setInterval(() => {
        const currentIndex = TIMELINE.findIndex((t) => t.id === currentSource);
        const nextIndex = (currentIndex + 1) % TIMELINE.length;
        onSelectSource(TIMELINE[nextIndex].id);
      }, 2500);
    }
    return () => clearInterval(interval);
  }, [isPlaying, currentSource, onSelectSource]);

  return (
    <div className="flex flex-col space-y-1.5">
      {/* Main control row */}
      <div className="flex items-center space-x-3 rounded-full border border-slate-700/80 bg-slate-900/95 px-4 py-2 shadow-2xl backdrop-blur-md text-xs text-slate-200">

        {/* Play / Pause */}
        <button
          onClick={() => setIsPlaying(!isPlaying)}
          className="flex h-7 w-7 items-center justify-center rounded-full bg-orange-600 text-white hover:bg-orange-500 shadow transition"
        >
          {isPlaying ? (
            <Pause className="w-3.5 h-3.5" />
          ) : (
            <Play className="w-3.5 h-3.5 ml-0.5" />
          )}
        </button>

        {/* Timeline steps */}
        <div className="flex items-center space-x-2">
          {TIMELINE.map((step) => {
            const active = currentSource === step.id;
            const isForecast =
              step.id === "forecast_2031" || step.id === "forecast_2041";
            return (
              <button
                key={step.id}
                onClick={() => {
                  setIsPlaying(false);
                  onSelectSource(step.id);
                }}
                className={`flex items-center space-x-1 px-2.5 py-1 rounded-full border transition text-[11px] ${
                  active
                    ? "bg-orange-600/90 text-white font-bold border-orange-400 shadow"
                    : "bg-slate-800 text-slate-400 border-slate-700 hover:bg-slate-700 hover:text-slate-200"
                }`}
              >
                <span>{step.year}</span>
                <span className="text-[9px] opacity-75">({step.label})</span>
                {/* Warning icon on forecast frames */}
                {isForecast && (
                  <AlertTriangle className="w-2.5 h-2.5 text-amber-400 ml-0.5" />
                )}
              </button>
            );
          })}
        </div>

        {/* Reset */}
        <button
          onClick={() => {
            setIsPlaying(false);
            onSelectSource("observed");
          }}
          title="Reset to 2024 Observed"
          className="text-slate-400 hover:text-white transition"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Disclaimer bar — only shown when a non-null disclaimer exists */}
      {activeStep.disclaimer && (
        <div className="flex items-start space-x-1.5 rounded-lg border border-amber-800/50 bg-amber-950/40 px-3 py-1.5 text-[10px] text-amber-300 shadow backdrop-blur-md max-w-xl">
          <AlertTriangle className="w-3 h-3 flex-shrink-0 mt-0.5 text-amber-400" />
          <span>{activeStep.disclaimer}</span>
        </div>
      )}
    </div>
  );
}

export default TimeMachine;
