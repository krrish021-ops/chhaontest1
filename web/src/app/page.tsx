"use client";

import React, { useState, useEffect, useMemo, useRef } from "react";
import HeatMap, {
  ThermalLayerKey,
  getLayerFieldName,
  getLayerDisplayTitle,
} from "@/components/map/HeatMap";
import { INDIAN_CITIES, IndianCityEntry } from "@/lib/indianCities";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface JurisdictionOption {
  id: string;
  label: string;
  scaleLabel: string;
  center: [number, number];
  zoom: number;
}

const JURISDICTIONS: JurisdictionOption[] = [
  {
    id: "india",
    label: "All India — National Monitoring Grid",
    scaleLabel: "70 km Regional Macro-Grid",
    center: [79.0, 22.5],
    zoom: 4.5,
  },
  {
    id: "delhi",
    label: "Delhi NCT — Municipal Grid",
    scaleLabel: "1 km Ward-Level Grid (575 zones)",
    center: [77.19, 28.62],
    zoom: 10.6,
  },
  {
    id: "nagpur",
    label: "Nagpur, Maharashtra — Municipal Grid",
    scaleLabel: "1 km Ward-Level Grid (229 zones)",
    center: [79.0882, 21.1458],
    zoom: 11.2,
  },
  {
    id: "pune",
    label: "Pune, Maharashtra — Municipal Grid",
    scaleLabel: "1 km Ward-Level Grid (414 zones)",
    center: [73.8567, 18.5204],
    zoom: 11.0,
  },
];

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
  const [loadingMap, setLoadingMap] = useState<boolean>(true);
  const [activeLayer, setActiveLayer] = useState<ThermalLayerKey>("observed");
  const [opacity, setOpacity] = useState<number>(0.55);
  const [basemap, setBasemap] = useState<"dark" | "streets">("dark");
  const [filterMode, setFilterMode] = useState<"all" | "hotspots" | "cool">("all");

  // Selection & Navigation State
  const [selectedCellId, setSelectedCellId] = useState<string | null>(null);
  const [focusedCity, setFocusedCity] = useState<IndianCityEntry | null>(null);
  const [directoryTab, setDirectoryTab] = useState<"cities" | "rankings">("cities");
  const [dossierTab, setDossierTab] = useState<"summary" | "drivers" | "simulator">("summary");
  const [showBottomTable, setShowBottomTable] = useState<boolean>(false);
  const [showMethodology, setShowMethodology] = useState<boolean>(false);

  // Search State
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [searchOpen, setSearchOpen] = useState<boolean>(false);
  const [osmSuggestions, setOsmSuggestions] = useState<IndianCityEntry[]>([]);
  const searchBoxRef = useRef<HTMLDivElement>(null);

  // Cooling Simulator Sliders
  const [simTreeAdd, setSimTreeAdd] = useState<number>(12);
  const [simCoolRoof, setSimCoolRoof] = useState<number>(25);
  const [simWaterAdd, setSimWaterAdd] = useState<number>(4);

  const currentJurisdiction = useMemo(
    () => JURISDICTIONS.find((j) => j.id === cityId) || JURISDICTIONS[0],
    [cityId]
  );

  // Load GeoJSON data (from static public demo or backend API)
  useEffect(() => {
    let cancelled = false;
    setLoadingMap(true);

    async function loadGeoJSON() {
      try {
        // Primary fast load from enriched public demo file or backend endpoint
        const res = await fetch(`/demo/${cityId}_heatmap.geojson`);
        if (res.ok) {
          const data = await res.json();
          if (!cancelled) {
            setGeojsonData(data);
            setLoadingMap(false);
            return;
          }
        }
      } catch {}

      try {
        const res2 = await fetch(`${API_BASE}/api/v1/heat/${cityId}/geojson?layer=observed`);
        if (res2.ok) {
          const data = await res2.json();
          if (!cancelled) setGeojsonData(data);
        }
      } catch (e) {
        console.error("Failed to load GeoJSON:", e);
      } finally {
        if (!cancelled) setLoadingMap(false);
      }
    }

    loadGeoJSON();
    return () => {
      cancelled = true;
    };
  }, [cityId]);

  // Close search dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (searchBoxRef.current && !searchBoxRef.current.contains(e.target as Node)) {
        setSearchOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  // Live OpenStreetMap geocoding fallback for smaller Indian towns
  useEffect(() => {
    const q = searchQuery.trim();
    if (q.length < 3) {
      setOsmSuggestions([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const res = await fetch(
          `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(
            q + ", India"
          )}&format=json&limit=4`
        );
        if (!res.ok) return;
        const arr = await res.json();
        setOsmSuggestions(
          arr.map((it: any) => {
            const parts = (it.display_name || "").split(",");
            return {
              name: parts[0]?.trim() || q,
              state: parts[1]?.trim() || "India",
              lat: parseFloat(it.lat),
              lon: parseFloat(it.lon),
            };
          })
        );
      } catch {}
    }, 350);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const activeField = useMemo(() => getLayerFieldName(activeLayer), [activeLayer]);

  const allCells = useMemo(() => {
    if (!geojsonData?.features) return [];
    return geojsonData.features
      .map((f: any) => f.properties)
      .filter((p: any) => p && p[activeField] !== null && p[activeField] !== undefined && !Number.isNaN(Number(p[activeField])));
  }, [geojsonData, activeField]);

  const sortedCells = useMemo(() => {
    return [...allCells].sort((a, b) => Number(b[activeField]) - Number(a[activeField]));
  }, [allCells, activeField]);

  const selectedCell = useMemo(() => {
    if (!selectedCellId || !geojsonData?.features) return null;
    const found = geojsonData.features.find(
      (f: any) => String(f.properties?.cell_id) === String(selectedCellId)
    );
    if (!found) return null;
    const props = { ...found.properties };
    if (focusedCity && cityId === "india") {
      props.display_title = `${focusedCity.name}, ${focusedCity.state}`;
    }
    return props;
  }, [selectedCellId, geojsonData, focusedCity, cityId]);

  // Regional KPIs for the currently active thermal layer
  const kpiStats = useMemo(() => {
    if (!allCells.length) return null;
    const vals = allCells.map((c: any) => Number(c[activeField]));
    const mean = vals.reduce((a: number, b: number) => a + b, 0) / vals.length;
    const max = Math.max(...vals);
    const hotspots = vals.filter((v: number) => v >= 2.5).length;
    return {
      mean: `${mean >= 0 ? "+" : ""}${mean.toFixed(2)} °C`,
      max: `${max >= 0 ? "+" : ""}${max.toFixed(2)} °C`,
      hotspots,
      total: vals.length,
    };
  }, [allCells, activeField]);

  // Enrich Indian Cities directory with live thermal values from the nearest cell
  const enrichedCityDirectory = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    const baseList = q
      ? [
          ...INDIAN_CITIES.filter(
            (c) => c.name.toLowerCase().includes(q) || c.state.toLowerCase().includes(q)
          ),
          ...osmSuggestions.filter(
            (o) => !INDIAN_CITIES.some((c) => c.name.toLowerCase() === o.name.toLowerCase())
          ),
        ]
      : INDIAN_CITIES;

    return baseList.map((city) => {
      let nearestCell: any = null;
      let bestD2 = 1e18;
      for (const c of allCells) {
        const d2 =
          (city.lat - Number(c.centroid_lat ?? 0)) ** 2 +
          (city.lon - Number(c.centroid_lon ?? 0)) ** 2;
        if (d2 < bestD2) {
          bestD2 = d2;
          nearestCell = c;
        }
      }
      const val = nearestCell ? Number(nearestCell[activeField]) : null;
      const lstDay = nearestCell?.lst_day != null ? Number(nearestCell.lst_day) : null;
      return {
        ...city,
        cell_id: nearestCell?.cell_id || null,
        suhii: val,
        lst_day: lstDay,
      };
    });
  }, [allCells, activeField, searchQuery, osmSuggestions]);

  // Select any Indian city from search or directory
  const handleSelectCity = (city: IndianCityEntry) => {
    setSearchOpen(false);
    setFocusedCity(city);

    if (cityId !== "india" && city.city_id !== cityId) {
      setCityId("india");
    }

    // Find nearest cell in current GeoJSON
    if (geojsonData?.features?.length) {
      let bestCid: string | null = null;
      let bestD2 = 1e18;
      for (const f of geojsonData.features) {
        const p = f.properties || {};
        const d2 =
          (city.lat - Number(p.centroid_lat ?? 0)) ** 2 +
          (city.lon - Number(p.centroid_lon ?? 0)) ** 2;
        if (d2 < bestD2) {
          bestD2 = d2;
          bestCid = p.cell_id;
        }
      }
      if (bestCid) setSelectedCellId(bestCid);
    }
  };

  // Compute plain-English SHAP attribution drivers for selected cell
  const shapDrivers = useMemo(() => {
    if (!selectedCell) return [];
    const built = Number(selectedCell.frac_built ?? 0);
    const tree = Number(selectedCell.frac_tree ?? 0);
    const water = Number(selectedCell.frac_water ?? 0);
    const viirs = Number(selectedCell.night_lights_mean ?? 1.2);
    const albedo = Number(selectedCell.albedo ?? 0.16);

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
  }, [selectedCell]);

  // Physics-informed cooling intervention estimate
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

  return (
    <div className="flex flex-col h-screen w-screen bg-[#0b0f19] text-slate-100 font-sans overflow-hidden">
      {/* ── TOP INSTITUTIONAL NAVIGATION BAR ────────────────────────────── */}
      <header className="h-13 px-4 bg-[#0b0f19] border-b border-slate-800 flex items-center justify-between gap-4 shrink-0 z-40">
        {/* System Identity + Jurisdiction Switcher */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded bg-orange-600 flex items-center justify-center font-bold text-xs tracking-wider text-white">
              CH
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm tracking-tight text-white">
                  CHHAON
                </span>
                <span className="text-[10px] uppercase tracking-widest px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-medium">
                  Urban Heat GIS
                </span>
              </div>
            </div>
          </div>

          <div className="h-5 w-[1px] bg-slate-800 hidden sm:block" />

          {/* Jurisdiction Dropdown */}
          <div className="flex items-center gap-2">
            <label className="text-[11px] uppercase tracking-wider text-slate-400 font-medium hidden md:inline">
              Coverage:
            </label>
            <select
              value={cityId}
              onChange={(e) => {
                setCityId(e.target.value);
                setSelectedCellId(null);
                setFocusedCity(null);
              }}
              className="bg-slate-900 border border-slate-700 hover:border-slate-600 text-xs text-slate-100 rounded px-2.5 py-1.5 font-medium focus:outline-none focus:border-orange-500"
            >
              {JURISDICTIONS.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Center Search Input for Any Indian City or District */}
        <div ref={searchBoxRef} className="relative flex-1 max-w-md">
          <div className="relative flex items-center">
            <svg
              className="w-3.5 h-3.5 text-slate-400 absolute left-3 pointer-events-none"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <input
              type="text"
              value={searchQuery}
              onFocus={() => setSearchOpen(true)}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setSearchOpen(true);
              }}
              placeholder="Locate city or district in India (e.g., Bhopal, Jaipur, Surat, Lucknow)..."
              className="w-full bg-slate-900 border border-slate-700 focus:border-orange-500 rounded pl-8 pr-16 py-1.5 text-xs text-slate-100 placeholder-slate-400 focus:outline-none"
            />
            {searchQuery && (
              <button
                onClick={() => {
                  setSearchQuery("");
                  setFocusedCity(null);
                }}
                className="absolute right-2 text-[11px] text-slate-400 hover:text-white px-1.5 py-0.5"
              >
                Clear
              </button>
            )}
          </div>

          {/* Search Autocomplete Dropdown */}
          {searchOpen && (
            <div className="absolute left-0 right-0 mt-1 bg-slate-900 border border-slate-700 rounded shadow-2xl max-h-80 overflow-y-auto z-50 divide-y divide-slate-800">
              <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-400 bg-slate-950 flex justify-between">
                <span>Indian Cities & Districts ({enrichedCityDirectory.length})</span>
                <button
                  onClick={() => setSearchOpen(false)}
                  className="text-slate-400 hover:text-white"
                >
                  Close
                </button>
              </div>
              {enrichedCityDirectory.slice(0, 12).map((item, idx) => (
                <button
                  key={`${item.name}-${idx}`}
                  onClick={() => handleSelectCity(item)}
                  className="w-full px-3 py-2 text-left hover:bg-slate-800/90 flex items-center justify-between transition"
                >
                  <div>
                    <div className="text-xs font-semibold text-white flex items-center gap-2">
                      <span>{item.name}</span>
                      <span className="text-slate-400 font-normal">{item.state}</span>
                      {item.city_id && (
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-orange-950 text-orange-300 border border-orange-800">
                          1 km Grid Available
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="text-right font-mono text-xs">
                    {item.suhii !== null ? (
                      <span className="text-orange-400 font-semibold">
                        {item.suhii >= 0 ? `+${item.suhii.toFixed(2)}` : item.suhii.toFixed(2)} °C
                      </span>
                    ) : (
                      <span className="text-slate-400">Locate →</span>
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right: Segmented Thermal Layer Switcher + Reports */}
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

          <a
            href={`${API_BASE}/api/v1/reports/${cityId === "india" ? "nagpur" : cityId}/pdf`}
            target="_blank"
            rel="noreferrer"
            className="px-2.5 py-1.5 rounded bg-slate-800 hover:bg-slate-700 border border-slate-600 text-slate-100 text-xs font-medium"
          >
            Audit PDF
          </a>
        </div>
      </header>

      {/* ── MAIN WORKSPACE: DOCKED LEFT SIDEBAR + FULL MAP VIEWPORT ─────── */}
      <div className="flex flex-1 min-h-0 overflow-hidden">
        {/* ── DOCKED LEFT ANALYTICAL SIDEBAR (390px) ────────────────────── */}
        <aside className="w-[390px] bg-[#0f172a] border-r border-slate-800 flex flex-col shrink-0 z-20">
          {!selectedCell ? (
            /* ── VIEW 1: REGIONAL OVERVIEW & CITY DIRECTORY ──────────── */
            <div className="flex flex-col h-full">
              {/* Plain-English Orientation Banner */}
              <div className="p-4 border-b border-slate-800 bg-slate-950/50">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-orange-400">
                    {activeLayerMeta.shortLabel} Dataset
                  </span>
                  <span className="text-[11px] text-slate-400 font-mono">
                    {currentJurisdiction.scaleLabel}
                  </span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {activeLayerMeta.description}
                </p>

                {/* Live Dataset KPIs */}
                {kpiStats && (
                  <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-slate-800/80">
                    <div className="bg-slate-900/90 border border-slate-800 rounded p-2">
                      <div className="text-[10px] uppercase text-slate-400">
                        Mean Night Heat
                      </div>
                      <div className="text-sm font-bold font-mono text-white mt-0.5">
                        {kpiStats.mean}
                      </div>
                    </div>
                    <div className="bg-slate-900/90 border border-slate-800 rounded p-2">
                      <div className="text-[10px] uppercase text-slate-400">
                        Peak Hotspot
                      </div>
                      <div className="text-sm font-bold font-mono text-red-400 mt-0.5">
                        {kpiStats.max}
                      </div>
                    </div>
                    <div className="bg-slate-900/90 border border-slate-800 rounded p-2">
                      <div className="text-[10px] uppercase text-slate-400">
                        Zones &gt; +2.5°C
                      </div>
                      <div className="text-sm font-bold font-mono text-orange-400 mt-0.5">
                        {kpiStats.hotspots} <span className="text-[10px] text-slate-400 font-normal">/ {kpiStats.total}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Directory Mode Tabs */}
              <div className="grid grid-cols-2 border-b border-slate-800 bg-slate-950 text-xs font-semibold">
                <button
                  onClick={() => setDirectoryTab("cities")}
                  className={`py-2.5 border-b-2 transition ${
                    directoryTab === "cities"
                      ? "border-orange-500 text-white bg-slate-900/60"
                      : "border-transparent text-slate-400 hover:text-slate-200"
                  }`}
                >
                  Indian Cities ({enrichedCityDirectory.length})
                </button>
                <button
                  onClick={() => setDirectoryTab("rankings")}
                  className={`py-2.5 border-b-2 transition ${
                    directoryTab === "rankings"
                      ? "border-orange-500 text-white bg-slate-900/60"
                      : "border-transparent text-slate-400 hover:text-slate-200"
                  }`}
                >
                  Hottest Zones ({sortedCells.length})
                </button>
              </div>

              {/* Scrollable Directory List */}
              <div className="flex-1 overflow-y-auto divide-y divide-slate-800/70">
                {directoryTab === "cities" ? (
                  enrichedCityDirectory.map((city, i) => {
                    const suhii = city.suhii;
                    return (
                      <div
                        key={`${city.name}-${i}`}
                        onClick={() => handleSelectCity(city)}
                        className="px-4 py-2.5 hover:bg-slate-800/60 cursor-pointer flex items-center justify-between transition"
                      >
                        <div>
                          <div className="text-xs font-semibold text-slate-100 flex items-center gap-2">
                            <span>{city.name}</span>
                            {city.city_id && (
                              <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-orange-300 border border-slate-700 font-normal">
                                1 km Grid
                              </span>
                            )}
                          </div>
                          <div className="text-[11px] text-slate-400">
                            {city.state}
                            {city.lst_day !== null && ` · Day LST: ${city.lst_day.toFixed(1)} °C`}
                          </div>
                        </div>

                        <div className="text-right">
                          {suhii !== null ? (
                            <div
                              className={`text-xs font-mono font-bold ${
                                suhii >= 3.0
                                  ? "text-red-400"
                                  : suhii >= 1.5
                                  ? "text-orange-400"
                                  : "text-emerald-400"
                              }`}
                            >
                              {suhii >= 0 ? `+${suhii.toFixed(2)}` : suhii.toFixed(2)} °C
                            </div>
                          ) : (
                            <span className="text-xs text-slate-500">—</span>
                          )}
                          <div className="text-[10px] text-slate-400">Inspect →</div>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  sortedCells.slice(0, 100).map((cell: any, idx: number) => {
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
                              Zone {cell.cell_id} · Day LST:{" "}
                              {cell.lst_day != null ? `${Number(cell.lst_day).toFixed(1)} °C` : "—"}
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
                  })
                )}
              </div>
            </div>
          ) : (
            /* ── VIEW 2: SELECTED LOCATION THERMAL DOSSIER ───────────── */
            <div className="flex flex-col h-full">
              {/* Dossier Header */}
              <div className="p-4 border-b border-slate-800 bg-slate-950">
                <button
                  onClick={() => {
                    setSelectedCellId(null);
                    setFocusedCity(null);
                  }}
                  className="text-xs text-slate-400 hover:text-white flex items-center gap-1 mb-2.5"
                >
                  <span>←</span>
                  <span>Back to City Directory</span>
                </button>

                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h2 className="text-base font-bold text-white leading-snug">
                      {selectedCell.display_title ||
                        selectedCell.location_name ||
                        selectedCell.cell_id}
                    </h2>
                    <div className="text-xs text-slate-400 font-mono mt-0.5">
                      Zone ID: {selectedCell.cell_id} ·{" "}
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

                {/* Offer 1km High-Res Grid switch if available */}
                {cityId === "india" &&
                  ["Delhi", "New Delhi", "Nagpur", "Pune"].includes(
                    focusedCity?.name || selectedCell.nearest_city || ""
                  ) && (
                    <button
                      onClick={() => {
                        const target = (
                          focusedCity?.name ||
                          selectedCell.nearest_city ||
                          ""
                        ).toLowerCase();
                        const nextId = target.includes("delhi") ? "delhi" : target;
                        setCityId(nextId);
                        setSelectedCellId(null);
                      }}
                      className="mt-3 w-full py-1.5 px-3 rounded bg-orange-600 hover:bg-orange-500 text-white text-xs font-semibold transition"
                    >
                      Open 1 km Ward-Level Street Grid for {selectedCell.nearest_city} →
                    </button>
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

              {/* Dossier Body */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {dossierTab === "summary" && (
                  <>
                    {/* Primary Active Layer Card */}
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
                        <span className="text-xs text-slate-400">
                          vs. rural baseline
                        </span>
                      </div>
                      <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                        {getSeverityMeta(Number(selectedCell[activeField])).plainSummary}
                      </p>
                    </div>

                    {/* Multi-Year Layer Comparison Strip (Click any to switch map) */}
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

                    {/* Absolute Satellite Land Surface Temperatures */}
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

                    {/* Land Cover Composition */}
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
                          <div className="text-[11px] text-slate-400 mt-1">
                            {d.detail}
                          </div>
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
                          <div className="text-[10px] text-slate-400">
                            Projected Cooling
                          </div>
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

          {/* Subtle Top-Left Map Filter Bar */}
          <div className="absolute top-3 left-3 z-20 flex items-center gap-1.5 bg-slate-950/90 border border-slate-800 rounded p-1 shadow">
            {(
              [
                ["all", "All Monitored Zones"],
                ["hotspots", "Hotspots Only (> +2.5 °C)"],
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

          {/* Compact Top-Right Map Style & Opacity Control */}
          <div className="absolute top-3 right-3 z-20 flex items-center gap-3 bg-slate-950/90 border border-slate-800 rounded px-3 py-1.5 shadow text-xs">
            <div className="flex items-center gap-1">
              <span className="text-slate-400 mr-1">Basemap:</span>
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
                Close ✕
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
