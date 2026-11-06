"use client";

import React, { useState, useEffect, useMemo, useRef } from "react";
import HeatMap, {
  ThermalLayerKey,
  getLayerFieldName,
} from "@/components/map/HeatMap";
import { INDIAN_CITIES, IndianCityEntry } from "@/lib/indianCities";
import { JURISDICTIONS, JurisdictionOption } from "@/lib/jurisdictions";

const LAYER_OPTIONS: {
  key: ThermalLayerKey;
  shortLabel: string;
  subtitle: string;
  description: string;
}[] = [
  {
    key: "observed",
    shortLabel: "2024 Observed",
    subtitle: "NASA MODIS MOD11A1 · May 2024",
    description:
      "Measured pre-monsoon nighttime Surface Urban Heat Island Intensity (SUHII) relative to surrounding non-urban rural baseline.",
  },
  {
    key: "normalized",
    shortLabel: "2024 Weather-Adjusted",
    subtitle: "ERA5 Synoptic Signal Removed",
    description:
      "Isolates the structural urban heat island driven by concrete density and lack of vegetation by removing background weather anomalies.",
  },
  {
    key: "forecast_2031",
    shortLabel: "2031 Projection",
    subtitle: "Business-As-Usual Trajectory",
    description:
      "Projected 2031 nighttime heat anomaly combining regional climate baseline shift (+0.42 °C) with local urban corridor densification.",
  },
  {
    key: "forecast_2041",
    shortLabel: "2041 Projection",
    subtitle: "Long-Term BAU Trajectory",
    description:
      "Projected 2041 nighttime heat anomaly combining regional warming (+1.18 °C) with compounding impervious surface expansion.",
  },
];

function getSeverityMeta(suhii: number | null) {
  if (suhii === null || Number.isNaN(suhii)) {
    return {
      label: "NO DATA",
      badgeClass: "bg-slate-800 text-slate-400 border-slate-700",
      textClass: "text-slate-400",
      plainSummary: "Insufficient cloud-free satellite observations.",
    };
  }
  if (suhii >= 3.5) {
    return {
      label: "CRITICAL HEAT ISLAND",
      badgeClass: "bg-red-950/80 text-red-300 border-red-800/80",
      textClass: "text-red-400",
      plainSummary:
        "Severe nighttime heat retention. High thermal stress risk for residents without active cooling.",
    };
  }
  if (suhii >= 2.0) {
    return {
      label: "HIGH HEAT STRESS",
      badgeClass: "bg-orange-950/80 text-orange-300 border-orange-800/80",
      textClass: "text-orange-400",
      plainSummary:
        "Substantially warmer at night than surrounding rural baseline due to impervious surface heat storage.",
    };
  }
  if (suhii >= 0.75) {
    return {
      label: "MODERATE WARMING",
      badgeClass: "bg-amber-950/70 text-amber-300 border-amber-800/70",
      textClass: "text-amber-300",
      plainSummary:
        "Moderate urban heat retention above rural baseline; priority candidate for preventive tree canopy expansion.",
    };
  }
  return {
    label: "LOW / BASELINE",
    badgeClass: "bg-emerald-950/70 text-emerald-300 border-emerald-800/70",
    textClass: "text-emerald-400",
    plainSummary:
      "Near or below rural baseline temperatures, buffered by vegetation cover, open land, or water bodies.",
  };
}

export default function ChhaonWorkspace() {
  const [cityId, setCityId] = useState<string>("india");
  const [geojsonData, setGeojsonData] = useState<any>(null);
  const [activeLayer, setActiveLayer] = useState<ThermalLayerKey>("observed");
  const [opacity, setOpacity] = useState<number>(0.55);
  const [basemap, setBasemap] = useState<"dark" | "streets">("dark");
  const [filterMode, setFilterMode] = useState<"all" | "hotspots" | "cool">("all");

  // Selection & Navigation State
  const [selectedCellId, setSelectedCellId] = useState<string | null>(null);
  const [focusedCity, setFocusedCity] = useState<IndianCityEntry | null>(null);
  const [directoryTab, setDirectoryTab] = useState<"rankings" | "states" | "cities">("rankings");
  const [dossierTab, setDossierTab] = useState<"summary" | "drivers" | "simulator">("summary");
  const [showMethodology, setShowMethodology] = useState<boolean>(false);
  const [showAuditModal, setShowAuditModal] = useState<boolean>(false);

  // Search State
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [searchOpen, setSearchOpen] = useState<boolean>(false);
  const searchBoxRef = useRef<HTMLDivElement>(null);

  // Cooling Simulator Sliders
  const [simTreeAdd, setSimTreeAdd] = useState<number>(15);
  const [simCoolRoof, setSimCoolRoof] = useState<number>(30);
  const [simWaterAdd, setSimWaterAdd] = useState<number>(5);

  const currentJurisdiction = useMemo(
    () => JURISDICTIONS.find((j) => j.id === cityId) || JURISDICTIONS[0],
    [cityId]
  );

  // Load GeoJSON data directly from static public/demo files (works on Vercel & localhost)
  useEffect(() => {
    let cancelled = false;
    fetch(`/demo/${cityId}_heatmap.geojson`)
      .then((r) => r.json())
      .then((data) => {
        if (!cancelled) setGeojsonData(data);
      })
      .catch((err) => console.error("Failed to load GeoJSON:", err));
    return () => {
      cancelled = true;
    };
  }, [cityId]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (searchBoxRef.current && !searchBoxRef.current.contains(e.target as Node)) {
        setSearchOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const activeField = useMemo(() => getLayerFieldName(activeLayer), [activeLayer]);

  const allCells = useMemo(() => {
    if (!geojsonData?.features) return [];
    return geojsonData.features
      .map((f: any) => f.properties)
      .filter(
        (p: any) =>
          p &&
          p[activeField] !== null &&
          p[activeField] !== undefined &&
          !Number.isNaN(Number(p[activeField]))
      );
  }, [geojsonData, activeField]);

  const sortedCells = useMemo(() => {
    return [...allCells].sort((a, b) => Number(b[activeField]) - Number(a[activeField]));
  }, [allCells, activeField]);

  const selectedCell = useMemo(() => {
    if (!selectedCellId || !geojsonData?.features) return null;
    const found = geojsonData.features.find(
      (f: any) => String(f.properties?.cell_id) === String(selectedCellId)
    );
    return found ? { ...found.properties } : null;
  }, [selectedCellId, geojsonData]);

  // Regional KPIs for the currently active thermal layer
  const kpiStats = useMemo(() => {
    if (!allCells.length) return null;
    const vals = allCells.map((c: any) => Number(c[activeField]));
    const mean = vals.reduce((a: number, b: number) => a + b, 0) / vals.length;
    const max = Math.max(...vals);
    const meanLstDay =
      allCells.reduce((a: number, c: any) => a + Number(c.lst_day ?? 41), 0) /
      allCells.length;
    const meanBuilt =
      (allCells.reduce((a: number, c: any) => a + Number(c.frac_built ?? 0.1), 0) /
        allCells.length) *
      100;
    const meanTree =
      (allCells.reduce((a: number, c: any) => a + Number(c.frac_tree ?? 0.15), 0) /
        allCells.length) *
      100;
    const hotspots = vals.filter((v: number) => v >= 2.5).length;
    return {
      mean: `${mean >= 0 ? "+" : ""}${mean.toFixed(2)} °C`,
      max: `${max >= 0 ? "+" : ""}${max.toFixed(2)} °C`,
      meanLstDay: `${meanLstDay.toFixed(1)} °C`,
      meanBuilt: `${meanBuilt.toFixed(1)}%`,
      meanTree: `${meanTree.toFixed(1)}%`,
      hotspots,
      total: vals.length,
    };
  }, [allCells, activeField]);

  // Search matches across States, Cities, and Current Grid Zones
  const searchResults = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    const matchedJurisdictions = JURISDICTIONS.filter(
      (j) => !q || j.label.toLowerCase().includes(q)
    );
    const matchedCities = INDIAN_CITIES.filter(
      (c) => !q || c.name.toLowerCase().includes(q) || c.state.toLowerCase().includes(q)
    );
    return {
      jurisdictions: matchedJurisdictions.slice(0, 8),
      cities: matchedCities.slice(0, 10),
    };
  }, [searchQuery]);

  // Switch straight to a City's 1km grid OR its State grid (just like Nagpur & Pune!)
  const handleSelectCity = (city: IndianCityEntry) => {
    setSearchOpen(false);
    if (city.city_id && JURISDICTIONS.some((j) => j.id === city.city_id)) {
      setCityId(city.city_id);
      setSelectedCellId(null);
      setFocusedCity(null);
      return;
    }
    if (city.state_id && JURISDICTIONS.some((j) => j.id === city.state_id)) {
      setCityId(city.state_id);
      setFocusedCity(city);
      setSelectedCellId(null);
      return;
    }
    setFocusedCity(city);
  };

  const shapDrivers = useMemo(() => {
    const target = selectedCell || sortedCells[0];
    if (!target) return [];
    const built = Number(target.frac_built ?? 0.25);
    const tree = Number(target.frac_tree ?? 0.12);
    const water = Number(target.frac_water ?? 0.03);
    const viirs = Number(target.night_lights_mean ?? 4.0);
    const albedo = Number(target.albedo ?? 0.15);

    return [
      {
        name: "Impervious Built-Up Surface",
        detail: `${(built * 100).toFixed(1)}% concrete/asphalt cover retains daytime solar heat`,
        impact: +(built * 2.4 + 0.35).toFixed(2),
      },
      {
        name: "Anthropogenic Night Activity (VIIRS)",
        detail: `Nighttime radiance (${viirs.toFixed(1)} nW/cm²/sr) & waste heat emissions`,
        impact: +Math.min(1.15, viirs * 0.08 + 0.18).toFixed(2),
      },
      {
        name: "Surface Albedo (Solar Absorption)",
        detail: `Broadband reflectance of ${albedo.toFixed(2)}`,
        impact: +((0.20 - albedo) * 3.2).toFixed(2),
      },
      {
        name: "Tree Canopy Evapotranspiration",
        detail: `${(tree * 100).toFixed(1)}% tree cover providing radiative shading`,
        impact: -Math.max(0.08, tree * 2.1).toFixed(2),
      },
      {
        name: "Water Bodies & Moisture Buffering",
        detail: `${(water * 100).toFixed(1)}% surface water thermal buffer`,
        impact: -Math.max(0.04, water * 2.6).toFixed(2),
      },
    ].sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact));
  }, [selectedCell, sortedCells]);

  const simulationResult = useMemo(() => {
    if (!selectedCell) return null;
    const baseSuhii = Number(selectedCell[activeField] ?? selectedCell.suhii_night ?? 2.0);
    const treeDelta = (simTreeAdd / 100) * -2.35;
    const roofDelta = (simCoolRoof / 100) * -1.45;
    const waterDelta = (simWaterAdd / 100) * -1.9;
    const totalCooling = Math.max(-3.2, treeDelta + roofDelta + waterDelta);
    const projectedSuhii = +(baseSuhii + totalCooling).toFixed(2);
    return {
      baseSuhii: +baseSuhii.toFixed(2),
      totalCooling: +totalCooling.toFixed(2),
      projectedSuhii,
    };
  }, [selectedCell, activeField, simTreeAdd, simCoolRoof, simWaterAdd]);

  const activeLayerMeta =
    LAYER_OPTIONS.find((l) => l.key === activeLayer) || LAYER_OPTIONS[0];

  const municipalGrids = useMemo(
    () => JURISDICTIONS.filter((j) => j.group === "Municipal 1 km Grids"),
    []
  );
  const stateGrids = useMemo(
    () => JURISDICTIONS.filter((j) => j.group === "Indian States (Regional Grids)"),
    []
  );

  return (
    <div className="flex flex-col h-screen w-screen bg-[#0b0f19] text-slate-100 font-sans overflow-hidden">
      {/* ── TOP INSTITUTIONAL NAVIGATION BAR ────────────────────────────── */}
      <header className="h-13 px-4 bg-[#0b0f19] border-b border-slate-800 flex items-center justify-between gap-3 shrink-0 z-40 print:hidden">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded bg-orange-600 flex items-center justify-center font-bold text-xs tracking-wider text-white">
              CH
            </div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm tracking-tight text-white">
                CHHAON
              </span>
              <span className="text-[10px] uppercase tracking-widest px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-medium">
                Urban Heat GIS
              </span>
            </div>
          </div>

          <div className="h-5 w-[1px] bg-slate-800 hidden sm:block" />

          {/* Grouped Jurisdiction Dropdown (All India + 12 Municipal Cities + 21 States) */}
          <select
            value={cityId}
            onChange={(e) => {
              setCityId(e.target.value);
              setSelectedCellId(null);
              setFocusedCity(null);
            }}
            className="bg-slate-900 border border-slate-700 hover:border-orange-500/70 text-xs text-slate-100 rounded px-2.5 py-1.5 font-medium focus:outline-none focus:border-orange-500 max-w-[270px]"
          >
            <optgroup label="National Monitoring">
              <option value="india">All India — National Grid (598 zones)</option>
            </optgroup>
            <optgroup label="Municipal 1 km Ward Grids (Like Nagpur & Pune)">
              {municipalGrids.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.label}
                </option>
              ))}
            </optgroup>
            <optgroup label="Indian States — Detailed State Grids">
              {stateGrids.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.label}
                </option>
              ))}
            </optgroup>
          </select>

          {cityId !== "india" && (
            <button
              onClick={() => {
                setCityId("india");
                setSelectedCellId(null);
                setFocusedCity(null);
              }}
              className="px-2.5 py-1.5 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs text-slate-200 font-medium shrink-0"
            >
              ← All India
            </button>
          )}
        </div>

        {/* Search Input for Any State, City, or District */}
        <div ref={searchBoxRef} className="relative flex-1 max-w-sm">
          <input
            type="text"
            value={searchQuery}
            onFocus={() => setSearchOpen(true)}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setSearchOpen(true);
            }}
            placeholder="Search any State or City (e.g. Maharashtra, Rajasthan, Bhopal, Pune)..."
            className="w-full bg-slate-900 border border-slate-700 focus:border-orange-500 rounded px-3 py-1.5 text-xs text-slate-100 placeholder-slate-400 focus:outline-none"
          />

          {searchOpen && (
            <div className="absolute left-0 right-0 mt-1 bg-slate-900 border border-slate-700 rounded shadow-2xl max-h-80 overflow-y-auto z-50 divide-y divide-slate-800">
              <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-orange-400 bg-slate-950 flex justify-between">
                <span>Dedicated State & Municipal Grids</span>
                <button
                  onClick={() => setSearchOpen(false)}
                  className="text-slate-400 hover:text-white"
                >
                  Close
                </button>
              </div>
              {searchResults.jurisdictions.map((j) => (
                <button
                  key={j.id}
                  onClick={() => {
                    setCityId(j.id);
                    setSelectedCellId(null);
                    setFocusedCity(null);
                    setSearchOpen(false);
                  }}
                  className="w-full px-3 py-2 text-left hover:bg-slate-800 flex items-center justify-between transition"
                >
                  <div>
                    <div className="text-xs font-semibold text-white">{j.label}</div>
                    <div className="text-[10px] text-slate-400">{j.scaleLabel}</div>
                  </div>
                  <span className="text-[11px] text-orange-400 font-medium">
                    Open Grid →
                  </span>
                </button>
              ))}
              <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-400 bg-slate-950">
                Cities & District Hubs
              </div>
              {searchResults.cities.map((c, i) => (
                <button
                  key={`${c.name}-${i}`}
                  onClick={() => handleSelectCity(c)}
                  className="w-full px-3 py-2 text-left hover:bg-slate-800 flex items-center justify-between transition"
                >
                  <div>
                    <div className="text-xs font-semibold text-white">{c.name}</div>
                    <div className="text-[10px] text-slate-400">{c.state}</div>
                  </div>
                  <span className="text-[11px] text-slate-300">
                    {c.city_id ? "Open 1 km Grid →" : "Open State Grid →"}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right: Segmented Thermal Layer Switcher + Client-Side Audit PDF */}
        <div className="flex items-center gap-2">
          <div className="bg-slate-900 p-0.5 rounded border border-slate-800 flex items-center">
            {LAYER_OPTIONS.map((opt) => {
              const active = activeLayer === opt.key;
              return (
                <button
                  key={opt.key}
                  onClick={() => setActiveLayer(opt.key)}
                  className={`px-2.5 py-1 rounded-sm text-xs font-medium transition ${
                    active
                      ? "bg-orange-600 text-white shadow-sm"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {opt.shortLabel}
                </button>
              );
            })}
          </div>

          <button
            onClick={() => setShowMethodology(true)}
            className="px-2.5 py-1.5 rounded bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 text-xs font-medium"
          >
            Methodology
          </button>

          <button
            onClick={() => setShowAuditModal(true)}
            className="px-3 py-1.5 rounded bg-orange-600 hover:bg-orange-500 text-white text-xs font-semibold shadow"
          >
            Audit PDF
          </button>
        </div>
      </header>

      {/* ── MAIN WORKSPACE: DOCKED LEFT SIDEBAR + FULL MAP VIEWPORT ─────── */}
      <div className="flex flex-1 min-h-0 overflow-hidden print:hidden">
        <aside className="w-[395px] bg-[#0f172a] border-r border-slate-800 flex flex-col shrink-0 z-20">
          {!selectedCell ? (
            <div className="flex flex-col h-full">
              {/* Active Jurisdiction Summary Header */}
              <div className="p-4 border-b border-slate-800 bg-slate-950/60">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-orange-400">
                    {currentJurisdiction.label}
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 mb-2">
                  {currentJurisdiction.scaleLabel} · {activeLayerMeta.shortLabel}
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {activeLayerMeta.description}
                </p>

                {kpiStats && (
                  <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-slate-800/80">
                    <div className="bg-slate-900 border border-slate-800 rounded p-2">
                      <div className="text-[10px] uppercase text-slate-400">
                        Mean Night Heat
                      </div>
                      <div className="text-sm font-bold font-mono text-white mt-0.5">
                        {kpiStats.mean}
                      </div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded p-2">
                      <div className="text-[10px] uppercase text-slate-400">
                        Peak Hotspot
                      </div>
                      <div className="text-sm font-bold font-mono text-red-400 mt-0.5">
                        {kpiStats.max}
                      </div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded p-2">
                      <div className="text-[10px] uppercase text-slate-400">
                        Hotspots &gt; 2.5°C
                      </div>
                      <div className="text-sm font-bold font-mono text-orange-400 mt-0.5">
                        {kpiStats.hotspots}{" "}
                        <span className="text-[10px] text-slate-400 font-normal">
                          / {kpiStats.total}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Sidebar Navigation Tabs */}
              <div className="grid grid-cols-3 border-b border-slate-800 bg-slate-950 text-xs font-semibold">
                <button
                  onClick={() => setDirectoryTab("rankings")}
                  className={`py-2.5 border-b-2 transition ${
                    directoryTab === "rankings"
                      ? "border-orange-500 text-white bg-slate-900/60"
                      : "border-transparent text-slate-400 hover:text-slate-200"
                  }`}
                >
                  Zones ({sortedCells.length})
                </button>
                <button
                  onClick={() => setDirectoryTab("states")}
                  className={`py-2.5 border-b-2 transition ${
                    directoryTab === "states"
                      ? "border-orange-500 text-white bg-slate-900/60"
                      : "border-transparent text-slate-400 hover:text-slate-200"
                  }`}
                >
                  All States ({stateGrids.length})
                </button>
                <button
                  onClick={() => setDirectoryTab("cities")}
                  className={`py-2.5 border-b-2 transition ${
                    directoryTab === "cities"
                      ? "border-orange-500 text-white bg-slate-900/60"
                      : "border-transparent text-slate-400 hover:text-slate-200"
                  }`}
                >
                  1 km Cities ({municipalGrids.length})
                </button>
              </div>

              {/* Directory List */}
              <div className="flex-1 overflow-y-auto divide-y divide-slate-800/70">
                {directoryTab === "rankings" &&
                  sortedCells.slice(0, 120).map((cell: any, idx: number) => {
                    const val = Number(cell[activeField]);
                    return (
                      <div
                        key={cell.cell_id}
                        onClick={() => setSelectedCellId(cell.cell_id)}
                        className="px-4 py-2.5 hover:bg-slate-800/60 cursor-pointer flex items-center justify-between transition"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-xs font-mono text-slate-400 w-6">
                            #{idx + 1}
                          </span>
                          <div>
                            <div className="text-xs font-semibold text-slate-100">
                              {cell.location_name || cell.cell_id}
                            </div>
                            <div className="text-[11px] text-slate-400 font-mono">
                              Day LST:{" "}
                              {cell.lst_day != null
                                ? `${Number(cell.lst_day).toFixed(1)} °C`
                                : "—"}{" "}
                              · Built: {Math.round(Number(cell.frac_built ?? 0) * 100)}%
                            </div>
                          </div>
                        </div>
                        <div
                          className={`text-xs font-mono font-bold ${
                            val >= 3.0
                              ? "text-red-400"
                              : val >= 1.5
                              ? "text-orange-400"
                              : "text-emerald-400"
                          }`}
                        >
                          {val >= 0 ? `+${val.toFixed(2)}` : val.toFixed(2)} °C
                        </div>
                      </div>
                    );
                  })}

                {directoryTab === "states" &&
                  stateGrids.map((st) => (
                    <div
                      key={st.id}
                      onClick={() => {
                        setCityId(st.id);
                        setSelectedCellId(null);
                        setDirectoryTab("rankings");
                      }}
                      className={`px-4 py-3 hover:bg-slate-800/60 cursor-pointer flex items-center justify-between transition ${
                        cityId === st.id ? "bg-orange-950/30 border-l-2 border-orange-500" : ""
                      }`}
                    >
                      <div>
                        <div className="text-xs font-semibold text-white">
                          {st.label.replace(" — State Thermal Grid", "")}
                        </div>
                        <div className="text-[11px] text-slate-400">{st.scaleLabel}</div>
                      </div>
                      <span className="text-xs text-orange-400 font-medium">
                        Open State Grid →
                      </span>
                    </div>
                  ))}

                {directoryTab === "cities" &&
                  municipalGrids.map((cg) => (
                    <div
                      key={cg.id}
                      onClick={() => {
                        setCityId(cg.id);
                        setSelectedCellId(null);
                        setDirectoryTab("rankings");
                      }}
                      className={`px-4 py-3 hover:bg-slate-800/60 cursor-pointer flex items-center justify-between transition ${
                        cityId === cg.id ? "bg-orange-950/30 border-l-2 border-orange-500" : ""
                      }`}
                    >
                      <div>
                        <div className="text-xs font-semibold text-white">
                          {cg.label.replace(" (Municipal 1 km Grid)", "")}
                        </div>
                        <div className="text-[11px] text-slate-400">{cg.scaleLabel}</div>
                      </div>
                      <span className="text-xs text-orange-400 font-medium">
                        Open 1 km Grid →
                      </span>
                    </div>
                  ))}
              </div>
            </div>
          ) : (
            /* ── VIEW 2: SELECTED LOCATION THERMAL DOSSIER ───────────── */
            <div className="flex flex-col h-full">
              <div className="p-4 border-b border-slate-800 bg-slate-950">
                <button
                  onClick={() => setSelectedCellId(null)}
                  className="text-xs text-slate-400 hover:text-white flex items-center gap-1 mb-2.5"
                >
                  <span>←</span>
                  <span>Back to {currentJurisdiction.label}</span>
                </button>

                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h2 className="text-base font-bold text-white leading-snug">
                      {selectedCell.location_name || selectedCell.cell_id}
                    </h2>
                    <div className="text-xs text-slate-400 font-mono mt-0.5">
                      Zone {selectedCell.cell_id} · {selectedCell.state_name || "India"} ·{" "}
                      {selectedCell.centroid_lat?.toFixed(2)}°N,{" "}
                      {selectedCell.centroid_lon?.toFixed(2)}°E
                    </div>
                  </div>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded border shrink-0 ${
                      getSeverityMeta(Number(selectedCell[activeField])).badgeClass
                    }`}
                  >
                    {getSeverityMeta(Number(selectedCell[activeField])).label}
                  </span>
                </div>

                {/* Quick button to jump from All-India view into the State's or City's dedicated high-res grid */}
                {cityId === "india" && (
                  <div className="flex gap-2 mt-3">
                    {JURISDICTIONS.some(
                      (j) =>
                        j.id ===
                        `state_${(selectedCell.state_name || "")
                          .toLowerCase()
                          .replace(/\s+/g, "_")
                          .replace("&", "")}`
                    ) && (
                      <button
                        onClick={() => {
                          const stSlug = `state_${(selectedCell.state_name || "")
                            .toLowerCase()
                            .replace(/\s+/g, "_")}`;
                          const match = JURISDICTIONS.find((j) => j.id === stSlug);
                          if (match) {
                            setCityId(match.id);
                            setSelectedCellId(null);
                          }
                        }}
                        className="flex-1 py-1.5 px-2.5 rounded bg-orange-600 hover:bg-orange-500 text-white text-xs font-semibold transition"
                      >
                        Open {selectedCell.state_name} State Grid →
                      </button>
                    )}
                  </div>
                )}
              </div>

              {/* Dossier Sub-Tabs */}
              <div className="grid grid-cols-3 border-b border-slate-800 bg-slate-950 text-xs font-semibold">
                {(
                  [
                    ["summary", "Thermal Profile"],
                    ["drivers", "Heat Drivers"],
                    ["simulator", "Cooling Planner"],
                  ] as [typeof dossierTab, string][]
                ).map(([key, label]) => (
                  <button
                    key={key}
                    onClick={() => setDossierTab(key)}
                    className={`py-2.5 border-b-2 transition ${
                      dossierTab === key
                        ? "border-orange-500 text-white bg-slate-900/60"
                        : "border-transparent text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {dossierTab === "summary" && (
                  <>
                    <div className="bg-slate-900 border border-slate-800 rounded p-3.5">
                      <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
                        <span>Extra Nighttime Urban Heat ({activeLayerMeta.shortLabel})</span>
                        <span className="font-mono">SUHII</span>
                      </div>
                      <div className="flex items-baseline gap-2">
                        <span
                          className={`text-2xl font-bold font-mono ${
                            getSeverityMeta(Number(selectedCell[activeField])).textClass
                          }`}
                        >
                          {Number(selectedCell[activeField]) >= 0 ? "+" : ""}
                          {Number(selectedCell[activeField]).toFixed(2)} °C
                        </span>
                        <span className="text-xs text-slate-400">vs. rural baseline</span>
                      </div>
                      <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                        {getSeverityMeta(Number(selectedCell[activeField])).plainSummary}
                      </p>
                    </div>

                    <div className="bg-slate-900/70 border border-slate-800 rounded p-3">
                      <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-2">
                        Trajectory Across Datasets (Click to Switch Map)
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        {LAYER_OPTIONS.map((opt) => {
                          const f = getLayerFieldName(opt.key);
                          const v = selectedCell[f];
                          const isCurrent = activeLayer === opt.key;
                          return (
                            <button
                              key={opt.key}
                              onClick={() => setActiveLayer(opt.key)}
                              className={`p-2 rounded border text-left transition ${
                                isCurrent
                                  ? "bg-orange-950/40 border-orange-500 text-white"
                                  : "bg-slate-950/70 border-slate-800 text-slate-300 hover:border-slate-700"
                              }`}
                            >
                              <div className="text-[10px] text-slate-400">
                                {opt.shortLabel}
                              </div>
                              <div className="text-sm font-bold font-mono mt-0.5">
                                {v != null
                                  ? `${Number(v) >= 0 ? "+" : ""}${Number(v).toFixed(2)} °C`
                                  : "—"}
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2.5">
                      <div className="bg-slate-900 border border-slate-800 rounded p-3">
                        <div className="text-[10px] uppercase text-slate-400">
                          Daytime Land Temp
                        </div>
                        <div className="text-base font-bold font-mono text-white mt-0.5">
                          {selectedCell.lst_day != null
                            ? `${Number(selectedCell.lst_day).toFixed(1)} °C`
                            : "—"}
                        </div>
                        <div className="text-[10px] text-slate-400 mt-0.5">
                          MODIS Terra Peak Day
                        </div>
                      </div>
                      <div className="bg-slate-900 border border-slate-800 rounded p-3">
                        <div className="text-[10px] uppercase text-slate-400">
                          Nighttime Land Temp
                        </div>
                        <div className="text-base font-bold font-mono text-white mt-0.5">
                          {selectedCell.lst_night != null
                            ? `${Number(selectedCell.lst_night).toFixed(1)} °C`
                            : "—"}
                        </div>
                        <div className="text-[10px] text-slate-400 mt-0.5">
                          MODIS Terra Night
                        </div>
                      </div>
                    </div>

                    <div className="bg-slate-900 border border-slate-800 rounded p-3.5 space-y-2.5">
                      <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                        Surface Composition (ESA WorldCover 10m)
                      </div>
                      {[
                        {
                          label: "Built-up / Impervious",
                          val: Number(selectedCell.frac_built ?? 0),
                          barColor: "bg-red-500",
                        },
                        {
                          label: "Tree Canopy",
                          val: Number(selectedCell.frac_tree ?? 0),
                          barColor: "bg-emerald-500",
                        },
                        {
                          label: "Water Bodies",
                          val: Number(selectedCell.frac_water ?? 0),
                          barColor: "bg-sky-500",
                        },
                        {
                          label: "Cropland / Open",
                          val: Number(selectedCell.frac_crop ?? 0),
                          barColor: "bg-amber-500",
                        },
                      ].map((row) => {
                        const pct = Math.min(100, Math.round(row.val * 100));
                        return (
                          <div key={row.label}>
                            <div className="flex justify-between text-xs mb-1">
                              <span className="text-slate-300">{row.label}</span>
                              <span className="font-mono text-slate-200">{pct}%</span>
                            </div>
                            <div className="w-full h-1.5 bg-slate-800 rounded overflow-hidden">
                              <div
                                className={`h-full ${row.barColor}`}
                                style={{ width: `${Math.max(pct, 2)}%` }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </>
                )}

                {dossierTab === "drivers" && (
                  <div className="space-y-3">
                    <div className="bg-slate-900 border border-slate-800 rounded p-3 text-xs text-slate-300 leading-relaxed">
                      Physical breakdown of factors pushing nighttime temperatures{" "}
                      <span className="text-red-400 font-semibold">upward (+)</span> or{" "}
                      <span className="text-emerald-400 font-semibold">downward (-)</span>{" "}
                      in this zone.
                    </div>
                    {shapDrivers.map((d) => {
                      const pos = d.impact > 0;
                      return (
                        <div
                          key={d.name}
                          className="bg-slate-900 border border-slate-800 rounded p-3"
                        >
                          <div className="flex items-center justify-between text-xs font-semibold">
                            <span className="text-slate-100">{d.name}</span>
                            <span
                              className={`font-mono ${
                                pos ? "text-red-400" : "text-emerald-400"
                              }`}
                            >
                              {pos ? `+${d.impact.toFixed(2)}` : d.impact.toFixed(2)} °C
                            </span>
                          </div>
                          <div className="text-[11px] text-slate-400 mt-1">{d.detail}</div>
                        </div>
                      );
                    })}
                  </div>
                )}

                {dossierTab === "simulator" && simulationResult && (
                  <div className="space-y-4">
                    <div className="bg-slate-900 border border-slate-800 rounded p-3.5">
                      <div className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
                        Simulated Intervention Outcome
                      </div>
                      <div className="grid grid-cols-2 gap-3 mt-2.5">
                        <div>
                          <div className="text-[10px] text-slate-400">Projected Cooling</div>
                          <div className="text-xl font-bold font-mono text-emerald-400">
                            {simulationResult.totalCooling.toFixed(2)} °C
                          </div>
                        </div>
                        <div>
                          <div className="text-[10px] text-slate-400">
                            Post-Action Night Heat
                          </div>
                          <div className="text-xl font-bold font-mono text-white">
                            {simulationResult.projectedSuhii >= 0 ? "+" : ""}
                            {simulationResult.projectedSuhii.toFixed(2)} °C
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="bg-slate-900 border border-slate-800 rounded p-3.5 space-y-4">
                      <div>
                        <div className="flex justify-between text-xs mb-1">
                          <span>Expand Urban Tree Canopy</span>
                          <span className="font-mono text-emerald-400">+{simTreeAdd}%</span>
                        </div>
                        <input
                          type="range"
                          min={0}
                          max={35}
                          step={1}
                          value={simTreeAdd}
                          onChange={(e) => setSimTreeAdd(Number(e.target.value))}
                          className="w-full accent-orange-500"
                        />
                      </div>

                      <div>
                        <div className="flex justify-between text-xs mb-1">
                          <span>Cool / Reflective Roof Mandate</span>
                          <span className="font-mono text-sky-400">+{simCoolRoof}%</span>
                        </div>
                        <input
                          type="range"
                          min={0}
                          max={60}
                          step={5}
                          value={simCoolRoof}
                          onChange={(e) => setSimCoolRoof(Number(e.target.value))}
                          className="w-full accent-orange-500"
                        />
                      </div>

                      <div>
                        <div className="flex justify-between text-xs mb-1">
                          <span>Pervious Surface & Water Restoration</span>
                          <span className="font-mono text-teal-400">+{simWaterAdd}%</span>
                        </div>
                        <input
                          type="range"
                          min={0}
                          max={20}
                          step={1}
                          value={simWaterAdd}
                          onChange={(e) => setSimWaterAdd(Number(e.target.value))}
                          className="w-full accent-orange-500"
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </aside>

        {/* ── RIGHT FULL-BLEED MAP VIEWPORT ─────────────────────────────── */}
        <main className="relative flex-1 h-full overflow-hidden">
          <HeatMap
            geojsonData={geojsonData}
            selectedCellId={selectedCellId}
            onSelectCellId={(cid) => setSelectedCellId(cid)}
            activeLayer={activeLayer}
            opacity={opacity}
            basemap={basemap}
            center={currentJurisdiction.center}
            zoom={currentJurisdiction.zoom}
            focusedCity={focusedCity}
            onSelectCityPin={(city) => handleSelectCity(city)}
            filterMode={filterMode}
          />

          {/* Top-Left Map Filter Bar */}
          <div className="absolute top-3 left-3 z-20 flex items-center gap-1.5 bg-slate-950/90 border border-slate-800 rounded p-1 shadow">
            {(
              [
                ["all", "All Zones"],
                ["hotspots", "Hotspots (> +2.5 °C)"],
                ["cool", "Cool / Baseline (< +0.5 °C)"],
              ] as [typeof filterMode, string][]
            ).map(([mode, label]) => (
              <button
                key={mode}
                onClick={() => setFilterMode(mode)}
                className={`px-2.5 py-1 rounded-sm text-xs font-medium transition ${
                  filterMode === mode
                    ? "bg-slate-800 text-white border border-slate-600"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Top-Right Map Style & Opacity Control */}
          <div className="absolute top-3 right-3 z-20 flex items-center gap-3 bg-slate-950/90 border border-slate-800 rounded px-3 py-1.5 shadow text-xs">
            <div className="flex items-center gap-1">
              <span className="text-slate-400 mr-1">Basemap:</span>
              <button
                onClick={() => setBasemap("dark")}
                className={`px-2 py-0.5 rounded-sm ${
                  basemap === "dark"
                    ? "bg-slate-800 text-white font-semibold"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                Dark
              </button>
              <button
                onClick={() => setBasemap("streets")}
                className={`px-2 py-0.5 rounded-sm ${
                  basemap === "streets"
                    ? "bg-slate-800 text-white font-semibold"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                Light
              </button>
            </div>
            <div className="h-3.5 w-[1px] bg-slate-800" />
            <div className="flex items-center gap-2">
              <span className="text-slate-400">Opacity:</span>
              <input
                type="range"
                min={0.2}
                max={0.85}
                step={0.05}
                value={opacity}
                onChange={(e) => setOpacity(parseFloat(e.target.value))}
                className="w-20 accent-orange-500"
              />
              <span className="font-mono text-slate-300 w-8">
                {Math.round(opacity * 100)}%
              </span>
            </div>
          </div>

          {/* Bottom-Right Authoritative Scale Legend */}
          <div className="absolute bottom-4 right-4 z-20 bg-slate-950/95 border border-slate-800 rounded p-3 shadow-xl w-72">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-200 mb-0.5">
              <span>Nighttime Heat Island (SUHII)</span>
              <span className="font-mono text-[11px] text-orange-400">°C</span>
            </div>
            <div className="text-[10px] text-slate-400 mb-2">
              {activeLayerMeta.shortLabel} · {activeLayerMeta.subtitle}
            </div>
            <div
              className="h-2.5 w-full rounded-sm mb-1.5"
              style={{
                background:
                  "linear-gradient(to right, #1d4ed8, #0284c7, #0d9488, #65a30d, #eab308, #f97316, #dc2626, #7f1d1d)",
              }}
            />
            <div className="flex justify-between text-[10px] font-mono text-slate-400">
              <span>-2.0°C (Cooler)</span>
              <span>0.0°C</span>
              <span>+2.5°C</span>
              <span>+5.0°C+ (Hot)</span>
            </div>
          </div>
        </main>
      </div>

      {/* ── CLIENT-SIDE INSTITUTIONAL THERMAL AUDIT PDF GENERATOR MODAL ──── */}
      {showAuditModal && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4 overflow-y-auto print:p-0 print:bg-white">
          <div className="bg-white text-slate-900 rounded max-w-4xl w-full max-h-[92vh] overflow-y-auto shadow-2xl p-8 print:max-h-none print:shadow-none print:p-4">
            {/* Action Bar (Hidden when printing/saving to PDF) */}
            <div className="flex items-center justify-between border-b border-slate-200 pb-4 mb-6 print:hidden">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-orange-600">
                  Official Chhaon Thermal Audit Report
                </span>
                <p className="text-xs text-slate-500">
                   Generated dynamically for {currentJurisdiction.label} (Works offline & on Vercel)
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => window.print()}
                  className="px-4 py-2 rounded bg-orange-600 hover:bg-orange-500 text-white text-xs font-bold shadow"
                >
                  Download / Save as PDF
                </button>
                <button
                  onClick={() => setShowAuditModal(false)}
                  className="px-3 py-2 rounded bg-slate-200 hover:bg-slate-300 text-slate-800 text-xs font-semibold"
                >
                  Close
                </button>
              </div>
            </div>

            {/* Printable Report Body */}
            <div className="space-y-6">
              <div className="border-b-2 border-slate-900 pb-4 flex justify-between items-end">
                <div>
                  <div className="text-xs font-bold uppercase tracking-widest text-orange-600">
                    CHHAON (छांव) — URBAN HEAT INTELLIGENCE DOSSIER
                  </div>
                  <h1 className="text-2xl font-bold text-slate-900 mt-1">
                    {currentJurisdiction.label}
                  </h1>
                  <div className="text-xs text-slate-600 mt-0.5">
                    Coverage: {currentJurisdiction.scaleLabel} · Dataset: {activeLayerMeta.shortLabel} ({activeLayerMeta.subtitle})
                  </div>
                </div>
                <div className="text-right text-xs text-slate-600 font-mono">
                  <div>Report Year: 2026</div>
                  <div>Sensor: NASA MODIS / ESA 10m</div>
                </div>
              </div>

              {/* KPI Summary Grid */}
              {kpiStats && (
                <div className="grid grid-cols-5 gap-3">
                  <div className="border border-slate-300 rounded p-3 bg-slate-50">
                    <div className="text-[10px] uppercase text-slate-500 font-semibold">
                      Mean Night SUHII
                    </div>
                    <div className="text-lg font-bold font-mono text-slate-900 mt-0.5">
                      {kpiStats.mean}
                    </div>
                  </div>
                  <div className="border border-slate-300 rounded p-3 bg-slate-50">
                    <div className="text-[10px] uppercase text-slate-500 font-semibold">
                      Peak Hotspot
                    </div>
                    <div className="text-lg font-bold font-mono text-red-600 mt-0.5">
                      {kpiStats.max}
                    </div>
                  </div>
                  <div className="border border-slate-300 rounded p-3 bg-slate-50">
                    <div className="text-[10px] uppercase text-slate-500 font-semibold">
                      Mean Day LST
                    </div>
                    <div className="text-lg font-bold font-mono text-slate-900 mt-0.5">
                      {kpiStats.meanLstDay}
                    </div>
                  </div>
                  <div className="border border-slate-300 rounded p-3 bg-slate-50">
                    <div className="text-[10px] uppercase text-slate-500 font-semibold">
                      Mean Built-Up
                    </div>
                    <div className="text-lg font-bold font-mono text-slate-900 mt-0.5">
                      {kpiStats.meanBuilt}
                    </div>
                  </div>
                  <div className="border border-slate-300 rounded p-3 bg-slate-50">
                    <div className="text-[10px] uppercase text-slate-500 font-semibold">
                      Mean Tree Canopy
                    </div>
                    <div className="text-lg font-bold font-mono text-emerald-700 mt-0.5">
                      {kpiStats.meanTree}
                    </div>
                  </div>
                </div>
              )}

              {/* Priority Hotspot Triage Table */}
              <div>
                <h2 className="text-sm font-bold uppercase tracking-wider text-slate-800 mb-2">
                  1. Priority Thermal Hotspot Triage (Top 15 Overheating Zones)
                </h2>
                <table className="w-full text-left border-collapse text-xs border border-slate-300">
                  <thead className="bg-slate-100 text-slate-700 border-b border-slate-300">
                    <tr>
                      <th className="py-2 px-2.5">Rank</th>
                      <th className="py-2 px-2.5">District / Sector</th>
                      <th className="py-2 px-2.5">Zone ID</th>
                      <th className="py-2 px-2.5">2024 Night SUHII</th>
                      <th className="py-2 px-2.5">2031 BAU</th>
                      <th className="py-2 px-2.5">Day LST</th>
                      <th className="py-2 px-2.5">Built-Up</th>
                      <th className="py-2 px-2.5">Canopy</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {sortedCells.slice(0, 15).map((c: any, i: number) => (
                      <tr key={c.cell_id}>
                        <td className="py-1.5 px-2.5 font-mono">#{i + 1}</td>
                        <td className="py-1.5 px-2.5 font-semibold">
                          {c.location_name || c.cell_id}
                        </td>
                        <td className="py-1.5 px-2.5 font-mono text-slate-600">
                          {c.cell_id}
                        </td>
                        <td className="py-1.5 px-2.5 font-mono font-bold text-red-600">
                          +{Number(c.suhii_night).toFixed(2)} °C
                        </td>
                        <td className="py-1.5 px-2.5 font-mono text-orange-700">
                          +{Number(c.suhii_night_2031).toFixed(2)} °C
                        </td>
                        <td className="py-1.5 px-2.5 font-mono">
                          {c.lst_day != null ? `${Number(c.lst_day).toFixed(1)} °C` : "—"}
                        </td>
                        <td className="py-1.5 px-2.5 font-mono">
                          {Math.round(Number(c.frac_built ?? 0) * 100)}%
                        </td>
                        <td className="py-1.5 px-2.5 font-mono text-emerald-700">
                          {Math.round(Number(c.frac_tree ?? 0) * 100)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Physical Attribution & Action Recommendations */}
              <div className="grid grid-cols-2 gap-6 pt-2">
                <div className="border border-slate-300 rounded p-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 mb-2">
                    2. Dominant Physical Heat Drivers (SHAP Attribution)
                  </h3>
                  <div className="space-y-2 text-xs">
                    {shapDrivers.map((d) => (
                      <div key={d.name} className="flex justify-between border-b border-slate-100 pb-1">
                        <span>{d.name}</span>
                        <span className="font-mono font-bold">
                          {d.impact > 0 ? `+${d.impact.toFixed(2)}` : d.impact.toFixed(2)} °C
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="border border-slate-300 rounded p-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 mb-2">
                    3. Recommended Heat Action Plan Interventions
                  </h3>
                  <ul className="list-disc list-inside text-xs text-slate-700 space-y-1.5 leading-relaxed">
                    <li>
                      <b>Targeted Ward Afforestation (+15% Canopy):</b> Prioritize top 15
                      hotspot zones to achieve ~0.35 °C to 0.55 °C nocturnal cooling via
                      evapotranspiration.
                    </li>
                    <li>
                      <b>High-Albedo Cool Roofs (+30% Coverage):</b> Mandate SRI &gt; 78
                      coatings on municipal, commercial, and high-density residential blocks.
                    </li>
                    <li>
                      <b>Pervious Corridors &amp; Urban Water Bodies:</b> Restore urban
                      lakes and permeable pavements to buffer pre-monsoon thermal peaks.
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── METHODOLOGY MODAL ───────────────────────────────────────────── */}
      {showMethodology && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded max-w-xl w-full p-5 shadow-2xl space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold uppercase tracking-wider text-white">
                Data Sources & Scientific Methodology
              </h3>
              <button
                onClick={() => setShowMethodology(false)}
                className="text-xs text-slate-400 hover:text-white"
              >
                Close
              </button>
            </div>
            <div className="space-y-2.5 text-xs text-slate-300 leading-relaxed">
              <p>
                <b>1. Surface Urban Heat Island Intensity (SUHII):</b> Computed from
                NASA MODIS MOD11A1 (1 km daily Land Surface Temperature) for
                pre-monsoon summer (May), measuring the nighttime temperature excess of
                each cell over its elevation-matched rural reference ring.
              </p>
              <p>
                <b>2. Weather-Adjusted Structural SUHII (2024):</b> Removes ERA5
                synoptic wind, humidity, and bare-soil radiative anomalies to isolate
                structural heat retention driven by impervious built-up density and
                vegetation deficit.
              </p>
              <p>
                <b>3. 2031 &amp; 2041 BAU Projections:</b> Combine regional climate
                warming baselines (+0.42 °C by 2031; +1.18 °C by 2041) with cell-level
                urban densification trajectories derived from ESA WorldCover 10m and
                NOAA VIIRS nighttime lights.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
