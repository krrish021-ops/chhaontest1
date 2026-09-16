# Chhaon (छांव) — Urban Heat Intelligence for Indian Cities

> **छांव** means *shade* in Hindi — this tool helps Indian cities find where
> shade is needed most, and what it would cost to create it.

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org)
[![LightGBM](https://img.shields.io/badge/ML-LightGBM-green.svg)](https://lightgbm.readthedocs.io)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-teal.svg)](https://fastapi.tiangolo.com)
[![MapLibre GL](https://img.shields.io/badge/Map-MapLibre_GL-orange.svg)](https://maplibre.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Table of Contents

1. [What is Chhaon?](#1-what-is-chhaon)
2. [Who is it for?](#2-who-is-it-for)
3. [What problem does it solve?](#3-what-problem-does-it-solve)
4. [How it works — big picture](#4-how-it-works--big-picture)
5. [Project structure](#5-project-structure)
6. [Technology stack](#6-technology-stack)
7. [Data sources](#7-data-sources)
8. [Data pipeline — step by step](#8-data-pipeline--step-by-step)
9. [Machine learning models](#9-machine-learning-models)
10. [Backend API](#10-backend-api)
11. [Frontend](#11-frontend)
12. [Map engine](#12-map-engine)
13. [Scenario simulator](#13-scenario-simulator)
14. [PDF report generator](#14-pdf-report-generator)
15. [Data flow diagram](#15-data-flow-diagram)
16. [How every component connects](#16-how-every-component-connects)
17. [Getting started (fresh install)](#17-getting-started-fresh-install)
18. [Environment variables](#18-environment-variables)
19. [Running the project](#19-running-the-project)
20. [API reference](#20-api-reference)
21. [Known limitations & honest disclosures](#21-known-limitations--honest-disclosures)
22. [Roadmap](#22-roadmap)
23. [Contributing](#23-contributing)
24. [License & attribution](#24-license--attribution)

---

## 1. What is Chhaon?

Chhaon is a **web-based decision-support tool** that turns satellite data
into actionable urban heat intelligence for Indian municipal planners.

It answers three questions:

| Question | What Chhaon shows |
|----------|------------------|
| **Where is it hot right now?** | A live choropleth map of every 1 km² cell in the city, coloured by how much hotter it is than the surrounding rural baseline |
| **Where will it be hotter in 2031/2041?** | Business-as-usual projections showing which zones face the worst heat if sprawl continues unchecked |
| **What can we do about it — and what does it cost?** | A scenario simulator that lets planners test planting trees, restoring water bodies, or adding concrete — and shows the predicted temperature change and rupee cost |

Everything is derived from **free, open satellite data** — no expensive
sensors, no proprietary feeds.

---

## 2. Who is it for?

| User | Role | What they use |
|------|------|---------------|
| **Municipal Town Planners** | Primary | Heat maps, hotspot rankings, scenario simulator, PDF audit reports |
| **Commissioners / Decision-makers** | Secondary | PDF reports, summary KPIs, cost-effectiveness rankings |
| **Researchers / Public** | Tertiary | GeoJSON data export, open API |

**Pilot cities:** Nagpur (229 grid cells) and Pune (414 grid cells).
Mumbai and Chhatrapati Sambhajinagar are configured but not yet ingested.

---

## 3. What problem does it solve?

Indian cities are getting hotter faster than almost anywhere else on earth.
Urban Heat Island (UHI) effect — where cities are measurably hotter than
surrounding rural areas — costs lives, reduces productivity, and drives up
energy demand.

**The problem for planners:**
- No affordable, city-scale thermal data
- No way to compare "plant trees vs restore lake vs cool roofs" quantitatively
- No tool that speaks the language of municipal budgets (₹ lakh/crore)

**What Chhaon provides:**
- Free satellite LST (Land Surface Temperature) data processed into
  per-cell SUHII (Surface Urban Heat Island Intensity) anomalies
- A physics-constrained ML model that predicts how land cover changes
  affect local temperature
- Cost estimates in Indian Rupees with lakh/crore formatting
- A PDF report formatted for statutory planning committees

---

## 4. How it works — big picture
SATELLITE DATA (Google Earth Engine)
│
▼
PYTHON PIPELINE
(boundary → LST → land cover → weather → SUHII → ML models)
│
▼
PARQUET FILES + GEOJSON FILES
(stored locally, git-ignored except demo files)
│
▼
FASTAPI BACKEND (Python)
(serves GeoJSON, rankings, SHAP explanations, scenarios, PDFs)
│
▼ HTTP REST API
NEXT.JS FRONTEND (React + TypeScript)
(MapLibre GL map + panels + scenario painter + report modal)
│
▼
MUNICIPAL PLANNER'S BROWSER

The key insight: **all heavy computation happens offline** (the pipeline).
The web app serves pre-computed files — making it fast and cheap to host.

---

chhaon/
│
├── api/                         # FastAPI backend
│   ├── main.py
│   ├── routers/
│   │   ├── cities.py
│   │   ├── layers.py
│   │   ├── cells.py
│   │   ├── scenarios.py
│   │   └── reports.py
│   ├── services/
│   │   ├── spatial_service.py
│   │   └── heat_service.py
│   └── schemas/
│       ├── heat.py
│       └── scenario.py
│
├── config/                     # City configuration
│   ├── cities.yaml
│   └── loader.py
│
├── data/                       # Project data
│   ├── demo/                   # Web-ready GeoJSON files
│   ├── tables/                 # Parquet datasets
│   └── boundaries/             # City/grid boundaries
│
├── docs/                       # Documentation & validation
│   ├── VALIDATION.md
│   └── COUNTERFACTUAL_VALIDATION.md
│
├── models/                     # Machine learning
│   ├── gbm/                    # LightGBM training
│   ├── baselines/              # Baseline models
│   ├── cv/                     # Cross-validation
│   ├── explain/                # SHAP explanations
│   ├── transfer_function/      # Scenario simulation
│   └── registry/               # Trained models
│
├── pipeline/                   # Data processing pipeline
│   ├── ingest/
│   ├── targets/
│   └── preprocess/
│
├── reports/                    # PDF report generation
│   ├── generator.py
│   └── templates/
│       └── thermal_audit.html
│
├── scripts/                    # Utility scripts
│   ├── build_heatmaps.py
│   └── rebuild_city_grids.py
│
├── tests/                      # Tests
│
├── web/                        # Next.js frontend
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   │   ├── map/
│   │   │   ├── panels/
│   │   │   └── scenario/
│   │   └── lib/
│   ├── package.json
│   └── next.config.js
│
├── requirements.txt            # Python dependencies
├── .gitignore
├── .python-version
└── README.md

---

## 6. Technology stack

### Backend (Python 3.11)

| Technology | Purpose | Why chosen |
|-----------|---------|------------|
| **FastAPI** | REST API framework | Auto OpenAPI docs, async, Pydantic validation |
| **LightGBM** | Gradient boosting ML | Fast, supports monotone constraints, interpretable |
| **SHAP** | ML explainability | TreeExplainer gives per-cell feature attribution |
| **Pandas / GeoPandas** | Data processing | Industry standard for tabular + spatial data |
| **PyArrow / Parquet** | Data storage | Columnar format, fast reads, compact |
| **WeasyPrint** | PDF generation | HTML→PDF with CSS, no external dependencies |
| **Jinja2** | HTML templating | Powers the PDF report template |
| **earthengine-api** | GEE Python client | Access to NASA/ESA satellite archives |
| **osmnx** | OSM data | City boundary extraction |
| **scikit-learn** | Preprocessing | Standard scalers, train/test splits |
| **scipy / kendalltau** | Statistics | Mann-Kendall trend test |
| **matplotlib** | Chart generation | Embedded PNG charts in PDF reports |

### Frontend (TypeScript)

| Technology | Purpose | Why chosen |
|-----------|---------|------------|
| **Next.js 14** | React framework | App Router, SSR safety for MapLibre, fast builds |
| **TypeScript** | Type safety | Catches null/undefined errors at compile time |
| **MapLibre GL 4** | Interactive map | Open-source, no API key needed, WebGL rendering |
| **Tailwind CSS** | Styling | Utility-first, fast iteration, dark theme |
| **lucide-react** | Icons | Consistent icon set, tree-shakeable |

### Infrastructure

| Technology | Purpose |
|-----------|---------|
| **Google Earth Engine** | Satellite data processing (server-side) |
| **CARTO Basemaps** | Map tiles (free, no API key required) |
| **Parquet files** | Offline data storage (no database at runtime) |

---

## 7. Data sources

All data is **free and open**. No paid APIs.

| Dataset | Provider | Resolution | What it gives us |
|---------|----------|------------|-----------------|
| **MODIS MOD11A1** | NASA Terra satellite | 1 km, daily | Land Surface Temperature (LST) — the core thermal signal |
| **ESA WorldCover v200** | European Space Agency | 10 m, 2021 | Land cover classification (built-up, trees, water, crops, grass) |
| **Sentinel-2 SR** | Copernicus / ESA | 10 m, 2024 | Spectral indices: NDVI (greenness), NDBI (built-up), MNDWI (water), albedo |
| **GHSL BUILT_H** | JRC / European Commission | 100 m, 2018 | Building height (mean, max, std per cell) |
| **VIIRS VCMSLCFG** | NOAA | 500 m, 2024 | Night lights radiance (proxy for economic activity / heat emission) |
| **ERA5-Land** | ECMWF / Copernicus | ~11 km, monthly | Weather: temperature, wind, precipitation, solar radiation, soil moisture |
| **SRTM** | NASA | 30 m | Elevation (used to filter rural reference pixels) |
| **OpenStreetMap** | OSM community | Vector | City boundaries (via osmnx) |

### Why MODIS instead of Landsat?

MODIS provides **daily thermal data** going back to 2000, which gives us
5 years of multi-month archives to train on. Landsat has better spatial
resolution (100 m thermal) but only passes every 16 days — too sparse for
monthly composites at this stage.

### What is SUHII?

**Surface Urban Heat Island Intensity (SUHII)** = city cell LST − rural
reference LST.

- Rural reference: 20 km ring around the city boundary, minus 2 km
  peri-urban buffer, filtered to cropland + grassland pixels within
  ±100 m elevation of the urban mean.
- A positive SUHII means that cell is hotter than the surrounding
  countryside. A value of +3°C means the cell is 3°C hotter than rural.

---

## 8. Data pipeline — step by step

The pipeline runs **once per city** (or when you want to refresh data).
Everything is orchestrated as Python modules you run in sequence.

### Step 1 — City boundary + grid

- Downloads the city boundary from OpenStreetMap using `osmnx`
- Creates a regular 0.01° (~1.1 km) grid clipped to the boundary
- Nagpur: 229 cells (`C0000`–`C0228`)
- Pune: 414 cells (`P0000`–`P0413`) at 0.009° grid step

Output: `data/boundaries/nagpur_grid.geojson`

### Step 2 — Land Surface Temperature

- Queries Google Earth Engine for MODIS MOD11A1 (Terra satellite)
- Time range: March–June, 2020–2024 (5 years × 4 months = 20 composites)
- Monsoon (July–September) is deliberately excluded — rain clouds corrupt
  the thermal signal
- Quality filter: accepts mandatory QA ≤ 1 (the relaxed rule is critical
  for India — strict QA=0 rejects nearly all night observations due to
  haze and dust)
- Converts DN → Kelvin → Celsius: `LST_°C = (band × 0.02) − 273.15`
- Computes monthly medians per cell

Output: `data/tables/nagpur_monthly_lst_multiyear.parquet`

### Step 3 — Rural reference temperature

- Queries Google Earth Engine for MODIS MOD11A1 (Terra satellite)
- Time range: March–June, 2020–2024 (5 years × 4 months = 20 composites)
- Monsoon (July–September) is deliberately excluded — rain clouds corrupt
  the thermal signal
- Quality filter: accepts mandatory QA ≤ 1 (the relaxed rule is critical
  for India — strict QA=0 rejects nearly all night observations due to
  haze and dust)
- Converts DN → Kelvin → Celsius: `LST_°C = (band × 0.02) − 273.15`
- Computes monthly medians per cell

Output: `data/tables/nagpur_monthly_lst_multiyear.parquet`

### Step 3 — Rural reference temperature

- ESA WorldCover 2021 at 10 m resolution
- Aggregates pixel class fractions per 1 km cell:
  - `frac_built` — impervious surfaces (class 50)
  - `frac_tree` — tree cover (class 10)
  - `frac_water` — water bodies (class 80)
  - `frac_crop` — cropland (class 40)
  - `frac_grass` — grassland (class 30)
  - `frac_bare` — bare ground (class 60)

Output: `data/tables/nagpur_landcover.parquet`

### Step 6 — Spectral indices

- **GHSL BUILT_H (2018):** mean/max/std building height per cell
- **VIIRS (2024):** mean/max night light radiance per cell
- **Derived features:**
  - `height_to_width_ratio = mean_height / 15` (assumed 15 m street width)
  - `svf_proxy = 1 − 0.5 × H/W` clamped [0.05, 1]
    (SVF = Sky View Factor — how much sky is visible from ground level;
    lower SVF = more trapped heat)

Output: `data/tables/nagpur_morphology.parquet`

### Step 8 — ERA5 weather data

- ERA5-Land monthly aggregates, March–June 2020–2024
- Variables: 2m temperature, dewpoint, skin temperature, wind speed,
  dewpoint depression, precipitation, solar radiation, soil moisture
- All cities share one value per month (ERA5 resolution ~11 km covers
  the whole city uniformly)

Output: `data/tables/nagpur_era5.parquet`

### Step 9 — Weather normalization

**Why?** A hot May 2022 vs a cool May 2023 makes the raw SUHII jump even
if nothing changed on the ground. We need to remove the weather signal to
see the land-cover signal.

**How:**
1. Compute monthly anomalies for all 8 weather variables
   (actual − long-term mean for that calendar month)
2. Identify "rural-like" cells: `frac_built < 0.20` AND
   `(crop + grass) > 0.50`
3. Train a small LightGBM model on rural cells:
   `SUHII ~ weather_anomalies`
4. Predict `E[SUHII | weather]` for all cells
5. Subtract: `SUHII_normalized = SUHII_raw − predicted_weather_component`

Output: `data/tables/nagpur_suhii_weather_normalized.parquet`

### Step 10 — Feature matrix assembly + model training

- Merges all the above tables by `cell_id` + `year` + `month`
- Result: 229 cells × 20 months = 4,580 rows × 19 features + 2 targets
- Also trains the v2 LightGBM models (see §9)

Output: `data/tables/nagpur_feature_matrix.parquet`
        `models/registry/lightgbm_suhii_night_v2.txt`
        `models/registry/lightgbm_suhii_day_v2.txt`

### Step 11 — Web GeoJSON export

- Merges feature matrix onto the grid geometry **by `cell_id`** (never
  by row position — that was the original bug)
- Adds BAU forecast fields: `suhii_night_2031 = observed + 0.42`,
  `suhii_night_2041 = observed + 1.18`
- Outputs 3 GeoJSON files per city (observed, normalized, forecast)

Output: `data/demo/nagpur_heatmap_normalized.geojson` (committed)

---

## 9. Machine learning models

### Model ladder

### Why LightGBM?

1. **Monotone physics constraints** — we can encode domain knowledge:
   - More concrete → hotter (`frac_built`: +1)
   - More trees → cooler (`frac_tree`: −1)
   - More water → cooler (`frac_water`: −1)
   - This makes it **mathematically impossible** for the model to conclude
     that planting trees heats the city
2. Fast inference (milliseconds per prediction)
3. Works well on small datasets (229–4,580 rows)
4. Built-in feature importance

### Feature list (v2, 19 features)

| Feature | Source | Physics role |
|---------|--------|-------------|
| `frac_built` | WorldCover | Heat absorber (+) |
| `frac_tree` | WorldCover | Cooling (−) |
| `frac_water` | WorldCover | Cooling (−) |
| `frac_crop` | WorldCover | Neutral (0) |
| `frac_grass` | WorldCover | Mild cooling (−) |
| `ndvi` | Sentinel-2 | Vegetation proxy (−) |
| `ndbi` | Sentinel-2 | Built-up intensity (+) |
| `mndwi` | Sentinel-2 | Water proxy (−) |
| `albedo` | Sentinel-2 | Reflectivity (−) |
| `building_height_mean` | GHSL | Canyon trapping (+) |
| `svf_proxy` | GHSL derived | Sky view factor (−) |
| `night_lights_mean` | VIIRS | Anthropogenic heat (+) |
| `era5_t2m_c_anomaly` | ERA5 | Weather (0) |
| `era5_dewpoint_depression_anomaly` | ERA5 | Weather (0) |
| `era5_wind_speed_anomaly` | ERA5 | Weather (0) |
| `era5_precip_mm_anomaly` | ERA5 | Weather (0) |
| `era5_solar_mj_anomaly` | ERA5 | Weather (0) |
| `era5_soil_moist_anomaly` | ERA5 | Weather (0) |
| `month` | Derived | Seasonality (0) |

### Validation results (honest)

| Test | Result | Pass/Fail |
|------|--------|-----------|
| v1 Spatial blocked CV MAE | 0.621°C ± 0.095 | ✅ < 0.9°C target |
| v2 Night blocked CV MAE | 0.701°C ± 0.085 | ✅ < 0.9°C target |
| v2 Night R² | 0.606 | ✅ |
| v2 Day blocked CV MAE | 0.732°C ± 0.038 | ✅ |
| Null hypothesis (shuffled targets) | Shuffled MAE 1.33 vs real 0.70 | ✅ No leakage |
| **City-block CV (Nagpur↔Pune)** | **MAE 1.107°C, R² −0.199** | **❌ Fails cross-city** |
| Quantile calibration | 62.4% coverage vs 80% target | ❌ Overconfident bands |
| Counterfactual (2020→2024) | r = 0.713, Spearman 0.765 | ✅ r ≥ 0.60 target |

**What the failures mean in practice:**
- Cross-city failure → Pune predictions carry a lower-confidence warning
- Overconfident bands → scenario ΔT ranges are indicative, not precise

### SHAP explainability

For every selected cell, we compute real SHAP values using
`shap.TreeExplainer` on the v1 booster:

```python
explainer = shap.TreeExplainer(booster)
shap_values = explainer.shap_values(cell_features)
# → per-feature °C contribution to this cell's SUHII
frac_built:  +1.85°C  (78% sealed surface — primary driver)
night_lights: +0.45°C (high anthropogenic heat emission)
frac_tree:   −0.65°C  (12% canopy provides some cooling)
frac_water:  −0.30°C  (small water body helps)
frac_grass:  −0.15°C  (minimal parkland)FastAPI (api/main.py)
    │
    ├── /api/v1/cities          → spatial_service.list_cities_service()
    ├── /api/v1/aoi/{city}      → spatial_service.get_city_aoi_service()
    ├── /api/v1/layers/{city}   → spatial_service.get_heatmap_geojson_service()
    ├── /api/v1/cells/{city}    → heat_service.get_ranked_cells_service()
    ├── /api/v1/cell/{id}/explain → heat_service.get_cell_explanation_service()
    ├── /api/v1/scenario/evaluate → scenario_engine.simulate_intervention()
    ├── /api/v1/scenario/compare  → comparison_engine.compare_scenarios()
    ├── /api/v1/report/generate   → generator.build_pdf_report()
    └── /api/v1/export/{city}     → GeoJSON / CSV downloadcurl 

Health check

Bash

curl http://localhost:8000/health

JSON

{
  "status": "healthy",
  "capabilities": {
    "demo_map": true,
    "parquet_tables": false,
    "ml_models": true,
    "shap": false,
    "scenarios": false,
    "pdf_reports": false
  }
}


web/src/app/page.tsx  (single dashboard page)
    │
    ├── <HeatMap>              MapLibre GL choropleth
    ├── <MapControls>          Layer switcher + opacity slider
    ├── <TimeMachine>          4-frame layer animator
    ├── <CityStatsBar>         Header KPIs (fetched from API)
    ├── <SearchAndInfo>        Cell search + model card modal
    ├── <CellDetailPanel>      Selected cell stats + SHAP + comparator
    ├── <RankingTable>         Sortable hotspot table + CSV export
    ├── <ScenarioPainter>      Single-cell intervention simulator
    ├── <ScenarioComparison>   A/B/C scenario comparison
    └── <ReportModal>          PDF generation trigger

const [cityId, setCityId]           // "nagpur" | "pune" | ...
const [layerSource, setLayerSource] // "observed" | "ml_fit" | "forecast_2031" | "forecast_2041"
const [basemapStyle, setBasemapStyle] // "dark" | "streets"
const [selectedCellId, setSelectedCellId] // "C0426" | null
const [geojsonData, setGeojsonData] // full city GeoJSON
const [rankings, setRankings]       // array of cell summaries

// Fetch the heatmap GeoJSON for a city
const geojson = await fetchHeatmapGeoJSON("nagpur")

// Fetch ranked cells
const rankings = await fetchCellRankings("nagpur", "suhii_night", 500)

// Fetch SHAP explanation for a cell
const explanation = await fetchCellExplanation("C0426")

// Run a scenario
const result = await evaluateScenario({
  city_id: "nagpur",
  cell_id: "C0426",
  action: "add_trees",
  area_pct_change: 25,
})

. Map engine
MapLibre GL

We use MapLibre GL (open-source fork of Mapbox GL) for the interactive
map. It renders using WebGL directly in the browser — no server-side
rendering.
Basemaps

Free CARTO basemaps — no API key required:

    Dark Matter (default) — dark background makes heat colours pop
    Voyager (streets) — shows road network for context

Heat choropleth

The city grid GeoJSON is loaded as a MapLibre source. Each cell is
coloured by its SUHII value using a 10-stop colour ramp:


−999 → #1e293b  (no data — invisible on dark background)
−4.0 → #1e3a8a  (deep cool — dark blue)
−2.0 → #2563eb  (cool — blue)
−0.5 → #38bdf8  (mild cool — light blue)
 0.0 → #5eead4  (neutral — teal)
 1.0 → #fbbf24  (warm — amber)
 2.0 → #f59e0b  (hot — orange)
 3.0 → #ea580c  (very hot — deep orange)
 4.0 → #dc2626  (critical — red)
 5.5 → #991b1b  (extreme — dark red)
 7.0 → #450a0a  (maximum — near black red)

"observed"      → suhii_night_normalized
"ml_fit"        → suhii_night_ml  (weather-normalized observed)
"forecast_2031" → suhii_night_2031  (observed + 0.42°C)
"forecast_2041" → suhii_night_2041  (observed + 1.18°C)


┌─────────────────────────────────────────────────────────────────┐
│                    GOOGLE EARTH ENGINE                          │
│  MODIS LST · WorldCover · Sentinel-2 · GHSL · VIIRS · ERA5    │
└───────────────────────────┬─────────────────────────────────────┘
                            │  earthengine-api (Python)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PYTHON PIPELINE                              │
│  boundaries → LST → rural_ref → SUHII → landcover → S2 →      │
│  morphology → ERA5 → weather_normalize → feature_matrix        │
└───────────────────────────┬─────────────────────────────────────┘
                            │  Parquet files (git-ignored)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MODEL TRAINING                               │
│  LightGBM v1 (5 feat) · v2 (19 feat) · Quantiles (P10/50/90) │
│  SHAP explainer · Domain guard · City-block CV                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │  .txt boosters (committed to git)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│               scripts/build_heatmaps.py                        │
│  Merge parquet → grid GeoJSON (by cell_id, never by row)       │
└───────────────────────────┬─────────────────────────────────────┘
                            │  data/demo/*.geojson (committed)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                              │
│  Serves GeoJSON · Rankings · SHAP · Scenarios · PDFs          │
│  Port 8000 · No DB · No cache · Files only                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │  HTTP REST (NEXT_PUBLIC_API_BASE_URL)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  NEXT.JS FRONTEND                               │
│  MapLibre choropleth · Cell panels · Scenario UI · PDF modal   │
│  Port 3000                                                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │  Browser
                            ▼
                  MUNICIPAL PLANNER
                  

page.tsx
 ├─ on load → fetchHeatmapGeoJSON("nagpur")
 │              → GET /api/v1/layers/nagpur
 │              → spatial_service.get_heatmap_geojson_service()
 │              → reads data/demo/nagpur_heatmap_normalized.geojson
 │              → returns GeoJSON to page.tsx → setGeojsonData()
 │
 ├─ on load → fetchCellRankings("nagpur")
 │              → GET /api/v1/cells/nagpur
 │              → heat_service.get_ranked_cells_service()
 │              → reads same GeoJSON, extracts + sorts properties
 │              → returns array of cell summaries → setRankings()
 │
 ├─ renders → <HeatMap geojsonData={geojsonData} />
 │              → MapLibre GL adds GeoJSON as source
 │              → colours each polygon by suhii_night_normalized
 │              → click → setSelectedCellId("C0426")
 │
 ├─ renders → <CellDetailPanel cellId="C0426" />
 │              → fetchCellExplanation("C0426")
 │              → GET /api/v1/cell/C0426/explain
 │              → heat_service.get_cell_explanation_service()
 │              → shap_explainer.explain_cell("C0426")
 │              → loads Parquet + v1 booster → SHAP values
 │              → returns drivers → renders bar chart
 │
 ├─ renders → <ScenarioPainter cellId="C0426" />
 │              → evaluateScenario({action: "add_trees", area_pct: 25})
 │              → POST /api/v1/scenario/evaluate
 │              → scenario_engine.simulate_intervention()
 │              → loads Parquet row for C0426
 │              → transfers frac_built → frac_tree
 │              → predicts with P10/P50/P90 quantile models
 │              → domain guard check
 │              → returns ΔT + cost + warnings
 │
 └─ renders → <ReportModal cityId="nagpur" />
                → POST /api/v1/report/generate
                → generator.build_pdf_report("nagpur")
                → loads feature_matrix.parquet
                → computes real SHAP chart
                → renders Jinja2 template
                → WeasyPrint → PDF
                → returns download URL

# Required
Python 3.11+
Node.js 20+
npm 9+

# For the data pipeline (optional for demo-only mode)
Google Earth Engine account (free for research)

git clone https://github.com/your-org/chhaon.git
cd chhaon

# Backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd web
npm install
cd ..

# Terminal 1 — Backend
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend
cd web && npm run dev

# Step 1 — Authenticate with Google Earth Engine
# (one-time, saves credentials locally)
python -c "import ee; ee.Authenticate()"

# Step 2 — Run pipeline in order (Nagpur)
python -m pipeline.ingest.boundaries
python -m pipeline.ingest.modis_lst
python -m pipeline.targets.rural_reference
python -m pipeline.targets.compute_suhii
python -m pipeline.ingest.landcover
python -m pipeline.ingest.sentinel2_indices
python -m pipeline.ingest.ghsl_viirs
python -m pipeline.ingest.era5_weather
python -m pipeline.preprocess.weather_normalize
python -m pipeline.preprocess.build_feature_matrix

# Step 3 — Run Pune (all-in-one)
python -m pipeline.ingest.ingest_pune

# Step 4 — Build web GeoJSONs
python -m scripts.build_heatmaps

# Step 5 — Validate models
python -m models.gbm.train_blocked
python -m models.gbm.train_quantile
python -m models.cv.city_block_cv
python -m scripts.validate_counterfactual

# URL of the FastAPI backend
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Backend (from repo root)
source .venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (from web/)
npm run dev

# Build and run everything
docker compose up --build

# API available at :8000
# Frontend available at :3000

# Check API health
curl http://localhost:8000/health

# Check cities endpoint
curl http://localhost:8000/api/v1/cities

# Check Nagpur heatmap loads
curl http://localhost:8000/api/v1/layers/nagpur | python3 -m json.tool | head -30

# Interactive API docs
open http://localhost:8000/docs


What LST is (and isn't)

    Land Surface Temperature (LST) measures radiative surface skin
    temperature and is typically 3–12°C higher than ambient 2m air
    temperature during the day. Nocturnal LST is a validated proxy for
    nocturnal thermal recovery. This tool is decision-support only and
    does not constitute a statutory environmental assessment.
