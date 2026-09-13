'use client';

import { useState } from 'react';
import { Search, Info, X, FileText } from 'lucide-react';
import type { CellSummary } from '@/lib/types';

interface SearchAndInfoProps {
  cells: CellSummary[];
  onSelectCell: (cellId: string) => void;
}

export default function SearchAndInfo({ cells, onSelectCell }: SearchAndInfoProps) {
  const [query, setQuery] = useState('');
  const [showModelCard, setShowModelCard] = useState(false);
  const [showResults, setShowResults] = useState(false);

  const filtered = query.length > 0
    ? cells.filter((c) => c.cell_id.toLowerCase().includes(query.toLowerCase())).slice(0, 8)
    : [];

  return (
    <>
      <div className="flex items-center gap-2">
        {/* Search */}
        <div className="relative">
          <div className="flex items-center bg-slate-900/95 backdrop-blur-md rounded-xl shadow-2xl border border-slate-700 px-3 py-2">
            <Search className="w-4 h-4 text-slate-400 mr-2" />
            <input
              type="text"
              placeholder="Search zone (e.g. C0426)"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setShowResults(true);
              }}
              onFocus={() => setShowResults(true)}
              className="bg-transparent text-sm text-white placeholder-slate-500 focus:outline-none w-48"
            />
          </div>

          {showResults && filtered.length > 0 && (
            <div className="absolute top-full mt-2 left-0 right-0 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl overflow-hidden z-30">
              {filtered.map((cell) => (
                <button
                  key={cell.cell_id}
                  onClick={() => {
                    onSelectCell(cell.cell_id);
                    setQuery('');
                    setShowResults(false);
                  }}
                  className="w-full text-left px-3 py-2 hover:bg-slate-800 text-xs border-b border-slate-800 last:border-0 flex justify-between items-center"
                >
                  <span className="font-mono text-white">{cell.cell_id}</span>
                  <span
                    className={`font-mono ${
                      cell.suhii_night >= 3 ? 'text-red-400' : 'text-slate-400'
                    }`}
                  >
                    {cell.suhii_night >= 0 ? '+' : ''}
                    {cell.suhii_night.toFixed(1)}°C
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Model Card Button */}
        <button
          onClick={() => setShowModelCard(true)}
          className="bg-slate-900/95 backdrop-blur-md rounded-xl shadow-2xl border border-slate-700 p-2.5 text-slate-400 hover:text-cyan-400 hover:border-cyan-500/50 transition-all"
          title="Model card & methodology"
        >
          <Info className="w-4 h-4" />
        </button>
      </div>

      {/* Model Card Modal */}
      {showModelCard && (
        <div
          className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 pointer-events-auto"
          onClick={() => setShowModelCard(false)}
        >
          <div
            className="bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[85vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="sticky top-0 bg-slate-900 border-b border-slate-800 p-4 flex items-center justify-between">
              <div>
                <div className="text-xs uppercase tracking-wider text-cyan-400 font-semibold">
                  Model Card
                </div>
                <h2 className="text-xl font-bold text-white mt-0.5">
                  Chhaon LightGBM v2
                </h2>
              </div>
              <button
                onClick={() => setShowModelCard(false)}
                className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-all"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-5 space-y-5 text-sm text-slate-300">
              <Section title="🎯 Purpose">
                Predict nighttime Surface Urban Heat Island Intensity (SUHII)
                for Nagpur grid cells, and simulate the impact of land-use
                interventions with uncertainty bands.
              </Section>

              <Section title="🧠 Architecture">
                <ul className="list-disc list-inside space-y-1 text-xs">
                  <li>M2 Champion: LightGBM Gradient Boosting</li>
                  <li>Features: 5 land-cover fractions (built, tree, water, crop, grass)</li>
                  <li>Physics constraints: monotone (trees cool, concrete heats)</li>
                  <li>Uncertainty: 3 quantile models (P10, P50, P90)</li>
                </ul>
              </Section>

              <Section title="📊 Honest Validation Metrics">
                <div className="bg-slate-800/50 rounded-lg p-3 space-y-2 font-mono text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Spatial CV MAE:</span>
                    <span className="text-white">~0.78 ± 0.09°C</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">In-sample MAE:</span>
                    <span className="text-amber-400">~0.18°C (optimistic)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Leakage test:</span>
                    <span className="text-emerald-400">✅ Passed</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">P10-P90 coverage:</span>
                    <span className="text-white">~78% (target 80%)</span>
                  </div>
                </div>
              </Section>

              <Section title="📡 Data Sources">
                <ul className="list-disc list-inside space-y-1 text-xs">
                  <li>NASA MODIS MOD11A1 (LST, 1km) — May 2024</li>
                  <li>ESA WorldCover 2021 (land cover, 10m)</li>
                  <li>OpenStreetMap (boundaries)</li>
                </ul>
              </Section>

              <Section title="⚠️ Known Limitations">
                <ul className="list-disc list-inside space-y-1 text-xs text-amber-200/80">
                  <li>Trained on only 229 cells × 1 month × 1 city</li>
                  <li>Sprawl forecast uses flat growth rates (not cellular automaton)</li>
                  <li>Weather normalization is a simplified proxy</li>
                  <li>LST ≠ air temperature (5–15°C hotter during day)</li>
                  <li>Native resolution 1km — do not interpret at parcel level</li>
                </ul>
              </Section>

              <Section title="🔬 Reproducibility">
                <code className="block bg-slate-800/50 rounded p-2 text-xs text-slate-300 font-mono">
                  python -m models.gbm.train_blocked<br />
                  python -m models.gbm.train_quantile
                </code>
              </Section>

              <div className="pt-3 border-t border-slate-800 flex items-center gap-3 text-xs text-slate-500">
                <FileText className="w-3.5 h-3.5" />
                <span>See docs/VALIDATION.md for full validation report</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="text-xs font-semibold text-white uppercase tracking-wider mb-2">
        {title}
      </div>
      <div className="text-xs text-slate-300 leading-relaxed">{children}</div>
    </div>
  );
}
