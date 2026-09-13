'use client';

import { useState, useEffect } from 'react';
import { Play, Pause, RotateCcw } from 'lucide-react';
import type { LayerSource } from '@/lib/types';

interface TimeMachineProps {
  layerSource: LayerSource;
  onLayerSourceChange: (source: LayerSource) => void;
}

const TIMELINE: {
  id: LayerSource;
  year: string;
  label: string;
}[] = [
  { id: 'observed', year: '2024', label: 'Today (Observed)' },
  { id: 'ml_fit', year: '2024', label: 'Today (ML Fit)' },
  { id: 'forecast_2031', year: '2031', label: '+7 Years (Forecast)' },
  { id: 'forecast_2041', year: '2041', label: '+17 Years (Forecast)' },
];

export default function TimeMachine({
  layerSource,
  onLayerSourceChange,
}: TimeMachineProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const currentIndex = TIMELINE.findIndex((t) => t.id === layerSource);

  // Auto-advance when playing
  useEffect(() => {
    if (!isPlaying) return;
    const timer = setInterval(() => {
      const nextIndex = (currentIndex + 1) % TIMELINE.length;
      onLayerSourceChange(TIMELINE[nextIndex].id);
      // Stop at 2041, don't loop
      if (nextIndex === TIMELINE.length - 1) {
        setTimeout(() => setIsPlaying(false), 1500);
      }
    }, 2000);
    return () => clearInterval(timer);
  }, [isPlaying, currentIndex, onLayerSourceChange]);

  const handleReset = () => {
    setIsPlaying(false);
    onLayerSourceChange('observed');
  };

  return (
    /* NO ABSOLUTE POSITIONING - Managed by parent */
    <div className="pointer-events-auto">
      <div className="bg-slate-900/95 backdrop-blur-md rounded-2xl shadow-2xl border border-slate-700 px-4 py-3 min-w-[520px]">
        <div className="flex items-center gap-3 mb-2">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            🕐 Time Machine
          </div>
          <div className="flex-1 border-t border-slate-700/50" />
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className={`
              flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium transition-all
              ${
                isPlaying
                  ? 'bg-rose-500 text-white'
                  : 'bg-emerald-500 text-white hover:bg-emerald-600'
              }
            `}
          >
            {isPlaying ? (
              <>
                <Pause className="w-3 h-3" />
                Pause
              </>
            ) : (
              <>
                <Play className="w-3 h-3" />
                Animate
              </>
            )}
          </button>
          <button
            onClick={handleReset}
            className="p-1.5 rounded-lg bg-slate-800/50 hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-all"
            title="Reset to 2024"
          >
            <RotateCcw className="w-3 h-3" />
          </button>
        </div>

        {/* Timeline dots */}
        <div className="relative">
          {/* Progress line */}
          <div className="absolute top-1/2 left-4 right-4 h-0.5 bg-slate-700 -translate-y-1/2" />
          <div
            className="absolute top-1/2 left-4 h-0.5 bg-gradient-to-r from-blue-500 via-purple-500 to-red-500 -translate-y-1/2 transition-all duration-700"
            style={{
              width: `calc(${(currentIndex / (TIMELINE.length - 1)) * 100}% * (100% - 32px) / 100%)`,
            }}
          />

          <div className="relative flex justify-between">
            {TIMELINE.map((item, idx) => {
              const isActive = idx === currentIndex;
              const isPast = idx < currentIndex;
              return (
                <button
                  key={item.id}
                  onClick={() => onLayerSourceChange(item.id)}
                  className="flex flex-col items-center group cursor-pointer"
                >
                  <div
                    className={`
                      w-4 h-4 rounded-full border-2 transition-all
                      ${
                        isActive
                          ? 'bg-gradient-to-br from-orange-400 to-red-500 border-orange-300 scale-125 shadow-lg shadow-orange-500/50'
                          : isPast
                          ? 'bg-purple-500 border-purple-400'
                          : 'bg-slate-700 border-slate-600 group-hover:bg-slate-600'
                      }
                    `}
                  />
                  <div
                    className={`
                      mt-2 text-[11px] font-semibold transition-all
                      ${isActive ? 'text-orange-400' : 'text-slate-500 group-hover:text-slate-300'}
                    `}
                  >
                    {item.year}
                  </div>
                  <div
                    className={`
                      text-[9px] uppercase tracking-wider transition-all
                      ${isActive ? 'text-orange-300/80' : 'text-slate-600'}
                    `}
                  >
                    {item.label.split(' (')[1]?.replace(')', '')}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
