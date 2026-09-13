"use client";

import React, { useState, useEffect } from "react";
import { Play, Pause, RotateCcw, Clock } from "lucide-react";
import { LayerSource } from "@/lib/types";

interface TimeMachineProps {
  currentSource: LayerSource;
  onSelectSource: (source: LayerSource) => void;
}

export function TimeMachine({ currentSource, onSelectSource }: TimeMachineProps) {
  const [isPlaying, setIsPlaying] = useState(false);

  const timeline: { id: LayerSource; label: string; year: string }[] = [
    { id: "observed", label: "Observed", year: "2024" },
    { id: "ml_fit", label: "Model Fit", year: "2024" },
    { id: "forecast_2031", label: "Forecast", year: "2031" },
    { id: "forecast_2041", label: "Forecast", year: "2041" },
  ];

  useEffect(() => {
    let interval: any;
    if (isPlaying) {
      interval = setInterval(() => {
        const currentIndex = timeline.findIndex((t) => t.id === currentSource);
        const nextIndex = (currentIndex + 1) % timeline.length;
        onSelectSource(timeline[nextIndex].id);
      }, 2500);
    }
    return () => clearInterval(interval);
  }, [isPlaying, currentSource, onSelectSource]);

  return (
    <div className="flex items-center space-x-3 rounded-full border border-slate-700/80 bg-slate-900/95 px-4 py-2 shadow-2xl backdrop-blur-md text-xs text-slate-200">
      
      {/* Play / Pause */}
      <button
        onClick={() => setIsPlaying(!isPlaying)}
        className="flex h-7 w-7 items-center justify-center rounded-full bg-orange-600 text-white hover:bg-orange-500 shadow transition"
      >
        {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 ml-0.5" />}
      </button>

      {/* Timeline steps */}
      <div className="flex items-center space-x-2">
        {timeline.map((step) => {
          const active = currentSource === step.id;
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
  );
}

export default TimeMachine;
