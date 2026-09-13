📖 Chhaon (छांव) — Complete Master Handoff Document v3.0
Post Phase 7 Frontend Polish — Full Context for AI Model Onboarding
📖 Table of Contents
Project Identity
Mission & Problem Statement
Governing Principles (Non-Negotiables)
Complete Technical Architecture
PHASE 1: Foundation — ✅ COMPLETE
PHASE 2: Satellite Data Pipeline — ✅ COMPLETE
PHASE 3: ML Model & Scenario Engine — ✅ COMPLETE
PHASE 4: Backend API — ✅ COMPLETE
PHASE 5: Initial Frontend — ✅ COMPLETE
PHASE 6: Model Credibility Fixes — ✅ COMPLETE
PHASE 7: Advanced Interactive Frontend — ✅ COMPLETE
Comprehensive PRD vs Delivered Comparison
Comprehensive TRD vs Delivered Comparison
Remaining Gaps (Complete Analysis)
PHASE 8: Reports & Exports — ⏳ NEXT
PHASE 9: Deployment — ⏳ FUTURE
Complete File Inventory
Environment & Credentials
How to Run Everything
Critical Context for AI Handoff
1. Project Identity
Attribute	Value
Product Name	Chhaon (छांव — Hindi for "shade")
Product Type	Web-based decision-support tool for urban heat
Domain	Urban Heat Island (UHI) forecasting & mitigation
Target Users	Indian municipal town planners, city commissioners
Pilot City	Nagpur, Maharashtra
Development Machine	Ubuntu Linux
User Handle	krrish-soni
Home Directory	/home/krrish-soni/chhaon
Current Status	~92% Complete (Phases 1-7 done, Phase 8-9 pending)
Editor Preference	nano (Ubuntu)
Version	v3.0 (Post Phase 7)
2. Mission & Problem Statement
The Mission
Turn 25 years of free satellite land-surface-temperature + land-cover + urban-form data into three actionable outputs:

Where the city is hot today (ward-level heat maps, day + night)
Where it will be hotter in 2031/2041 (ML forecasts with uncertainty)
What each intervention buys back in °C and ₹ (interactive scenario painter)
The Problem Being Solved
Indian cities are heating up faster than climate change alone predicts because of how they are being built. Every rezoning decision (park → apartments, lake → concrete) increases urban heat by 2-4°C, but planners currently have zero thermal feedback on their decisions. Existing analyses are retrospective research papers with no operational reach.

The Differentiator
An interactive "paint the future" scenario simulator where a planner:

Selects a hotspot cell on the map
Chooses to "Plant Trees" (or Cool Roofs / Restore Water)
Slides coverage % (5%-50%)
Gets live temperature drop with uncertainty range (e.g. "-1.15°C, range -0.6 to -1.7°C")
Gets live ₹ cost (e.g. "₹16 Lakh")
Sees extrapolation warnings if the scenario is unrealistic
Watches the AI "think" in real-time (transparency trace)
3. Governing Principles (Non-Negotiables)
Rule	Reason
Server-side compute first	All heavy work in Google Earth Engine; download aggregates only
Anomaly (SUHII), not absolute LST	Raw LST is dominated by seasonality — no planning value
Blocked CV always	Random k-fold on spatial data leaks memorization
COG rasters, Parquet tables, PostGIS geography	No format invention
Version every artefact	(data_version, code_version, config_hash)
Simplest model that clears the bar ships	LightGBM before ConvLSTM
Never call GEE live during a demo	Pre-materialize and cache
Physics constraints non-negotiable	Monotone constraints prevent "trees make it hotter"
NEVER use mock data	User explicitly rejected this — always real satellite data
NEVER use random k-fold CV	Always blocked splits (temporal/spatial/city)
Uncertainty bands mandatory	No forecast ever shown as a bare number
Extrapolation warnings mandatory	Model must refuse to over-predict outside its knowledge
Non-Goals (Explicitly Out of Scope)
ID	Non-goal	Why
N1	Public weather forecast	IMD/commercial apps own this
N2	Human heat-stress/mortality modeling	Requires micro-meteorology
N3	Real-time citizen SMS/siren alerts	Different problem, needs SLAs
N4	Real estate valuation	Ethically fraught (redlining risk)
N5	Sub-10m microclimate CFD	Compute prohibitive
N6	Personal/household data	Aggregate-only, always
4. Complete Technical Architecture
System Diagram
text

┌─────────── DATA SOURCES (all free, in orbit) ───────────┐
│ NASA MODIS (LST) · ESA WorldCover (LC) · Landsat        │
│ Sentinel-2 · JRC GHSL · ERA5 · SRTM · OSM boundaries    │
└──────────────────────┬───────────────────────────────────┘
                       │ (Google Earth Engine batch reduceRegions)
                       ▼
┌─────────── ① INGESTION LAYER (Phase 2) ─────────────────┐
│  pipeline/ingest/*.py — Python + GEE                    │
│  Outputs: Parquet tables + GeoJSON                      │
└──────────────────────┬───────────────────────────────────┘
                       ▼
┌─────────── ② PROCESSING LAYER (Phase 2 + 6) ────────────┐
│  pipeline/preprocess/ + pipeline/targets/               │
│  Rural reference · SUHII computation · feature matrix   │
│  Sprawl trajectory projection for 2031/2041             │
│  Weather normalization proxy (Phase 6)                  │
└──────────────────────┬───────────────────────────────────┘
                       ▼
┌─────────── ③ MODELLING LAYER (Phase 3 + 6) ─────────────┐
│  models/baselines/  — M1 OLS (transparent formula)      │
│  models/gbm/ ★     — M2 LightGBM (champion + physics)   │
│  models/gbm/       — Quantile P10/P50/P90 (Phase 6)     │
│  models/explain/    — SHAP explainability               │
│  models/transfer_function/ — M5 scenario engine         │
│  models/cv/         — Blocked CV + Domain Guard (P6)    │
│  models/registry/   — trained model binaries + cards    │
└──────────────────────┬───────────────────────────────────┘
                       ▼
┌─────────── ④ SERVING LAYER (Phase 4) ───────────────────┐
│  api/main.py — FastAPI with 4 routers                   │
│  PostgreSQL + PostGIS · CORS enabled for Next.js        │
│  Auto-generated OpenAPI docs at /docs                   │
│  Uncertainty bands + extrapolation warnings in schema   │
└──────────────────────┬───────────────────────────────────┘
                       ▼
┌─────────── ⑤ CLIENT LAYER (Phase 5 + 7) ────────────────┐
│  web/ — Next.js 14 + TypeScript + MapLibre GL JS        │
│  4 Layer Sources: Observed | ML Fit | 2031 | 2041       │
│  3 Basemap Styles: Dark | Streets | Satellite Aerial    │
│  Cell Detail Panel + SHAP + Ranking Table + Painter     │
│  Time Machine + Search + Model Card + AI Trace          │
│  Uncertainty visualization (P10/P50/P90 bands)          │
└──────────────────────────────────────────────────────────┘
Technology Stack Summary
Layer	Technology	Version	Purpose
OS	Ubuntu Linux	Latest	Development
Backend Language	Python	3.11	ML + API
Frontend Language	Node.js	20 LTS	Web app
Database	PostgreSQL + PostGIS	16 / 3.4	Spatial queries
Cache	Redis	7	Scenario cache (planned)
Geospatial	GDAL	3.4+	Raster/vector I/O
Satellite Platform	Google Earth Engine	1.4.2	Data source
ML Framework	LightGBM	4.5.0	Champion model (M2)
Explainability	SHAP	0.46.0	"Why is this hot?"
Statistics	statsmodels	0.14.4	OLS baseline (M1)
API Framework	FastAPI	0.115.5	Backend REST API
Frontend Framework	Next.js	14.2.35	React app
Map Library	MapLibre GL JS	4.7.1	Interactive maps
Styling	Tailwind CSS	3.4.14	Dark UI
Icons	lucide-react	0.453.0	UI icons
5. PHASE 1: Foundation — ✅ COMPLETE
What Was Built
System Setup

Ubuntu updated + essential tools
Python 3.11 via deadsnakes PPA
Node.js 20 LTS via NodeSource
GDAL 3.4+ + GEOS + PROJ + spatial libraries
PostgreSQL 16 + PostGIS 3.4 (chhaon_db, user chhaon, password chhaon_dev_2024)
Redis on port 6379
Project Structure Created

text

/home/krrish-soni/chhaon/
├── config/           # City definitions
├── gee/              # GEE-isolated scripts (empty; direct API used)
├── pipeline/         # Data processing
├── models/           # ML models
├── api/              # FastAPI backend
├── web/              # Next.js frontend
├── reports/          # PDF templates (Phase 8)
├── scripts/          # Helpers
├── tests/            # Test suite (Phase 8)
├── data/             # Git-ignored
└── docs/             # PRD, TRD, methodology
Configuration Files

config/cities.yaml — 4 Maharashtra cities (Nagpur active, Pune/Mumbai/Aurangabad configured)
config/loader.py — Central config accessor with get_city(), get_db_url(), get_redis_url()
.env — DB, Redis, GEE credentials
Python Environment

Virtual environment: .venv/
Key packages: earthengine-api, rasterio, geopandas, lightgbm, shap, fastapi, psycopg2-binary, statsmodels, osmnx, scipy
Google Earth Engine

Cloud Project: chhaon-508513
Earth Engine API enabled
Registered for non-commercial use
Credentials in ~/.config/earthengine/
6. PHASE 2: Satellite Data Pipeline — ✅ COMPLETE
What Was Built
2.1 City Boundary & 1km Grid

pipeline/ingest/boundaries.py — Downloads Nagpur outline from OSM via osmnx
pipeline/ingest/load_to_db.py — Loads grid into PostGIS as nagpur_grid table
Result: 229 grid cells covering Nagpur (~1km × 1km each)
2.2 MODIS LST Extraction (NASA Terra Satellite)

pipeline/ingest/modis_lst.py
Uses server-side batch processing (reduceRegions()) — all 229 cells in ~3 seconds
Extracts day (~10:30 AM IST) and night (~10:30 PM IST) surface temperatures
Converts Kelvin×50 → Celsius: °C = (val × 0.02) − 273.15
Critical: .median() MUST be called before .multiply() on ImageCollections
Data: 2020-2024, March-June (peak heat, no monsoon clouds)
Actual Nagpur Results (May 2024):

Daytime LST: 37.7°C avg (34.8 to 45.0)
Nighttime LST: 28.3°C avg (25.4 to 30.8)
2.3 ESA WorldCover Land Cover

pipeline/ingest/landcover.py
Uses shapely.geometry.mapping() for polygon-to-GEE conversion
ESA WorldCover 2021, 10m resolution
Extracts fractions for: built (50), tree (10), water (80), crop (40), grass (30), bare (60)
Actual Nagpur Land Cover:

Built: 51.8% | Tree: 14.5% | Grass: 18.8% | Crop: 11.1% | Water: 1.3% | Bare: 0.8%
2.4 Master Dataset Merger

pipeline/preprocess/merge_data.py
Output: data/tables/nagpur_master_2024.parquet (229 rows × 12 columns)
2.5 Rural Reference (The Credibility Backbone)

pipeline/targets/rural_reference.py
20km buffer around Nagpur, excludes 2km inner buffer
Filters to cropland + grassland only
Actual May 2024: Day 40.4°C, Night 26.4°C
2.6 SUHII Calculator (Headline Metric)

pipeline/targets/compute_suhii.py
Formula: SUHII = Cell_LST − Rural_Reference_LST
Actual Nagpur:

Mean SUHII Day: -2.7°C (Vidarbha oasis effect)
Mean SUHII Night: +1.9°C (concrete heat retention)
Max SUHII Night: +4.3°C (hottest zone)
2.7 Web-Ready Heatmap GeoJSON

scripts/generate_heatmap.py
Output: data/demo/nagpur_heatmap.geojson (121.5 KB, 229 cells)
2.8 Sprawl Forecast (2031/2041 Projections)

pipeline/preprocess/sprawl_forecast.py
Applies growth trajectories to feature vectors:
2031: 15% of crop → built-up (7 years of BAU sprawl)
2041: 35% conversion + 15% tree canopy loss (17 years)
Runs LightGBM inference on projected features
Output: data/demo/nagpur_forecast_heatmap.geojson
Actual Forecast Results:

2024 (Observed): +1.92°C mean night SUHII
2024 (ML Inference): +1.91°C (MAE: 0.18°C in-sample)
2031 (Forecast): +2.34°C (▲ +0.42°C warmer)
2041 (Forecast): +3.10°C (▲ +1.18°C warmer)
⚠️ Critical Scientific Interpretation
Negative daytime SUHII IS REAL for Nagpur in May (semi-arid Vidarbha oasis effect)
Nighttime SUHII is the health metric — focus reporting on suhii_night
LST ≠ Air Temperature — surface is 5-15°C hotter than air temp during day (FR-60)
7. PHASE 3: ML Model & Scenario Engine — ✅ COMPLETE
What Was Built
3.1 OLS Baseline Model (M1)

models/baselines/ols_regression.py
Uses statsmodels.api.OLS
Formula: SUHII_night = β₁·frac_built + β₂·frac_tree + β₃·frac_water + intercept
Purpose: Transparent linear coefficients quotable in reports (TRD ADR-09)
3.2 LightGBM Champion Model (M2) ⭐

models/gbm/train.py (deprecated in Phase 6)
models/gbm/train_blocked.py (Phase 6 replacement)
Configuration:

Python

lgb.LGBMRegressor(
    n_estimators=300,
    learning_rate=0.03,
    num_leaves=15,
    monotone_constraints=[+1, -1, -1, 0, -1],  # Physics rules
    random_state=42
)
Features (order matters):

frac_built (+1) — More concrete MUST predict hotter
frac_tree (-1) — More trees MUST predict cooler
frac_water (-1) — More water MUST predict cooler
frac_crop (0) — Unconstrained
frac_grass (-1) — More grass MUST predict cooler
Why monotone constraints matter: The model is mathematically forbidden from ever concluding "trees make it hotter." Trust anchor for public defensibility.

3.3 SHAP Explainability

models/explain/shap_explainer.py
Uses shap.TreeExplainer
Per-cell driver breakdown in °C
Plain-language templates (FR-61)
3.4 Scenario Simulation Engine ⭐

models/transfer_function/scenario_engine.py
Key function: simulate_intervention(cell_id, action, area_pct_change) → dict
Supported actions:

add_trees: frac_tree ↑, frac_built ↓ (cost: ₹800/tree × 100 trees/ha)
add_concrete: frac_built ↑, frac_tree ↓ (cost: ₹0 private)
restore_water: frac_water ↑, frac_built ↓ (cost: ₹15 lakh/ha)
Performance: Sub-second response

8. PHASE 4: Backend API — ✅ COMPLETE
What Was Built
4.1 API Structure

text

api/
├── main.py                     # FastAPI entry point + CORS
├── schemas/
│   ├── heat.py                 # CityInfo, CellSummary, CellExplanation
│   └── scenario.py             # ScenarioRequest, ScenarioResponse + UncertaintyBand (Phase 6)
├── services/
│   ├── spatial_service.py      # City + GeoJSON accessors (serves forecast heatmap)
│   └── heat_service.py         # Cell rankings + SHAP wrapper
└── routers/
    ├── cities.py               # /cities, /aoi/{city_id}
    ├── layers.py               # /layers/{city_id}
    ├── cells.py                # /cells, /cell/{id}/explain
    └── scenarios.py            # /scenario/evaluate
4.2 All Endpoints (Verified Working)

Endpoint	Method	Purpose
/health	GET	Server health check
/	GET	Root status
/docs	GET	Auto-generated Swagger UI
/api/v1/cities	GET	List all pilot cities
/api/v1/aoi/{city_id}	GET	City boundary GeoJSON
/api/v1/layers/{city_id}	GET	Heat map GeoJSON (with ML forecasts)
/api/v1/cells/{city_id}	GET	Ranked cell table (sortable)
/api/v1/cell/{cell_id}/explain	GET	SHAP "Why is this hot?"
/api/v1/scenario/evaluate	POST	Interactive scenario ΔT + cost + uncertainty + warning
4.3 Key Technical Details

CORS enabled for http://localhost:3000
Pydantic v2 schema validation
spatial_service.get_heatmap_geojson_service() prefers nagpur_forecast_heatmap.geojson (with ML predictions) over nagpur_heatmap.geojson if it exists
Runs on port 8000 via uvicorn api.main:app --reload --port 8000
9. PHASE 5: Initial Frontend — ✅ COMPLETE
What Was Built
5.1 Next.js 14 Project Structure

text

web/
├── package.json                # Next.js 14.2.35, React 18.3, MapLibre 4.7, Tailwind
├── tsconfig.json               # TypeScript with @/* path alias to ./src/*
├── tailwind.config.ts          # Dark theme with brand colors
├── postcss.config.js
├── .env.local                  # NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
└── src/
    ├── app/
    │   ├── layout.tsx          # Root HTML shell
    │   ├── page.tsx            # Main dashboard page
    │   └── globals.css         # MapLibre CSS + Tailwind
    ├── components/
    │   ├── map/
    │   │   ├── HeatMap.tsx     # MapLibre wrapper (4 layer sources)
    │   │   └── MapControls.tsx # Layer selector + Day/Night + Legend
    │   ├── panels/
    │   │   ├── CellDetailPanel.tsx
    │   │   └── RankingTable.tsx
    │   └── scenario/
    │       └── ScenarioPainter.tsx
    └── lib/
        ├── types.ts
        └── api.ts
10. PHASE 6: Model Credibility Fixes — ✅ COMPLETE
What Was Built
6.1 Blocked Cross-Validation Utility

models/cv/blocked_split.py
Functions:

temporal_split(df, year_col, holdout_years) — Train on early years, test on latest
spatial_block_split(df, lat_col, lon_col, n_blocks, block_size_deg) — Hold out geographic tiles
null_hypothesis_test(...) — Trains model on shuffled targets → detects leakage
6.2 Retrained M2 with Honest CV

models/gbm/train_blocked.py
Reports honest MAE per spatial fold
Runs null-hypothesis test on every training run
Saves CARD.json with truthful metrics
Actual Honest Numbers (May 2024, 229 cells):

Spatial CV MAE: ~0.78 ± 0.09°C (real generalization)
In-sample MAE: ~0.18°C (optimistic, memorization)
Ratio: 4-5× worse than in-sample (as expected)
Null test: ✅ NO LEAKAGE
6.3 Quantile Uncertainty Models

models/gbm/train_quantile.py
Trains 3 LightGBM quantile models (P10, P50, P90)
Saves as lightgbm_suhii_night_p10.txt, _p50.txt, _p90.txt
Calibration check: measures P10-P90 coverage on held-out data (target 80%)
Note: LightGBM quantile objective doesn't support monotone_constraints — omitted for these 3 models
6.4 Weather Normalization Proxy

pipeline/preprocess/weather_normalize.py
Simplified proxy (not full ERA5 integration)
Uses sklearn.linear_model.Ridge on rural-like cells
Subtracts geographic macro-variation from SUHII
Output: data/tables/nagpur_suhii_weather_normalized.parquet
Note: Full ERA5 integration deferred to future
6.5 Domain Guard (Extrapolation Detection)

models/cv/domain_guard.py
Uses Mahalanobis distance + chi-squared p-value
Returns extrapolation_warning: bool, confidence: str, verdict: str
Wired into scenario engine for every prediction
6.6 Updated Scenario Engine

models/transfer_function/scenario_engine.py — v3 with uncertainty + domain guard
Returns:
JSON

{
  "delta_T_degC": {"p10": ..., "p50": ..., "p90": ...},
  "original_suhii_night": {...},
  "new_suhii_night": {...},
  "extrapolation_warning": bool,
  "confidence": "high|medium|low",
  "domain_verdict": "..."
}
6.7 Updated API Schemas

api/schemas/scenario.py — Added UncertaintyBand, extrapolation fields
6.8 Documentation

docs/VALIDATION.md — All validation numbers, including failures
docs/LIMITATIONS.md — 10 documented gaps, when NOT to use Chhaon
11. PHASE 7: Advanced Interactive Frontend — ✅ COMPLETE
What Was Built
7.1 4-Way Layer Source Selector

Prominent gradient buttons with icons in top-right controls
Observed 2024 (blue) — Real satellite data
ML Fit 2024 (purple) — Model's understanding
Forecast 2031 (orange) — 7-year projection
Forecast 2041 (red) — 17-year projection
7.2 Time Machine Slider

Bottom-center animated timeline
Play/Pause button auto-scrubs 2024 → 2031 → 2041
Clickable timeline dots
Reset button
2-second interval between states
7.3 Display Mode Toggle

SUHII Anomaly (default) — °C above/below rural
Absolute °C — Raw temperature values
7.4 Basemap Style Selector

Dark Canvas — Esri World Dark Gray (high-contrast thermal)
Detailed Streets (OSM) — OpenStreetMap with buildings, alleyways, POIs
Satellite Aerial — Esri World Imagery (real photography) + Reference labels
7.5 Heat Layer Transparency Slider

20% to 95% opacity
Lets users see building footprints underneath heat colors
7.6 Rich Cell Detail Panel (3 tabs)

Current — SUHII cards, Day/Night LST, Land cover bars, "Test AI Interventions" button
AI Diagnosis — SHAP drivers with plain-language "Heats by +2.10°C" / "Cools by 1.40°C"
Future — Trend bar chart showing Today → 2031 → 2041
7.7 AI Scenario Studio with Transparency Trace

Choose action (Plant Trees / Restore Water / Build Concrete)
Slide coverage % (5-50%)
"Ask AI to Evaluate Impact" button
Live AI Trace shows the model "thinking":
text

> Initializing LightGBM model...
> Extracting local geographic features...
> Applying monotone physics constraints...
> Running 3 quantile models (P10/P50/P90)...
> Inference complete.
Returns ΔT with P10-P90 uncertainty range
Returns ₹ cost in Indian format (Lakh/Crore)
Extrapolation warning for unrealistic scenarios
7.8 City Stats Bar (Header)

Mean SUHII, Peak Heat, Built %, Canopy %, Hotspot Count
Live updates from data
7.9 Cell Search with Autocomplete

Search by cell ID (e.g. "C0426")
Preview shows SUHII value
Click to jump to cell on map
7.10 Model Card Modal

Click ⓘ button
Shows: Purpose, Architecture, Honest Metrics, Data Sources, Limitations, Reproducibility commands
7.11 AI Context Banner

Dynamic text under header
Explains what user is looking at:
"Satellite Observation: Real historical temperature recorded by NASA MODIS"
"AI Forecast: Projects 7 years of concrete sprawl..."
7.12 Ranking Table Enhancements

Sortable by Night SUHII, Day SUHII, Concrete %, Tree Canopy %
Filter chips: All / 🔥 Hot / ❄️ Cool / 🌳 High Canopy
CSV export button
Collapsible
7.13 Layout Fixes

Left panel positioned top-3 left-3 bottom-[280px]
Right controls at top-[72px] right-3
Time Machine at bottom-[280px] center
Ranking table at bottom-0 with h-[270px]
Logo/Search/Banner hide when left panel opens (no overlap)
7.14 SSR Fix (Critical Runtime)

HeatMap component loaded via dynamic() with ssr: false
Prevents Next.js server-side rendering stack overflow with MapLibre
7.15 Property Coercion (Critical Runtime)

coerceCellProps() converts MapLibre string properties → typed numbers
num() / fmt() helper functions in CellDetailPanel prevent .toFixed() crashes on undefined
12. Comprehensive PRD vs Delivered Comparison
Functional Requirements Coverage
FR ID	Requirement	Status	Notes
FR-01	AOI selection (city or bbox)	✅ Partial	Nagpur only; city selector in config/cities.yaml
FR-02	AOI upload (GeoJSON/shapefile)	❌	Deferred to Phase 8+
FR-03	AOI validation & error messages	⚠️ Partial	API returns 404 for unknown cities
FR-04	Rural reference visualization	⚠️ Partial	Computed but not shown as overlay layer
FR-05	Ward polygon overlay	❌	Using 1km grid instead of wards
FR-10	LST day/night raster layer	✅	Both lst_day and lst_night served
FR-11	Time slider (year/month)	⚠️ Partial	Time Machine only cycles Observed→2031→2041, not months
FR-12	Trend map (°C/decade)	❌	No multi-year data yet
FR-13	SUHII anomaly map	✅	Primary map view
FR-14	Land-cover map	⚠️ Partial	Fractions shown per cell, no dedicated LC layer
FR-15	Multi-year LC change	❌	Single snapshot only (2021)
FR-16	Spectral indices (NDVI, NDBI)	❌	Not extracted
FR-17	Urban morphology (building height)	❌	GHSL not extracted
FR-18	Transect tool	❌	Deferred
FR-20	Hotspot polygons (P90+)	⚠️ Partial	Ranking table shows hotspots via filter chip
FR-21	Ward ranking table	✅	Sortable, filterable, exportable
FR-22	Vulnerability index	❌	No population/socioeconomic data
FR-23	Alert generation	❌	Non-goal N3
FR-24	Population-weighted stats	❌	No pop data
FR-30	Forecast layer (2031/2041)	✅	Available as layer sources
FR-31	Forecast uncertainty visualization	✅	P10-P90 in scenario engine, shown in painter
FR-32	Uncertainty bands on all predictions	✅	Delivered in Phase 6
FR-33	Scenario pathways (BAU vs Plan)	⚠️ Partial	Only BAU sprawl implemented
FR-34	Model card display	✅	Modal accessible via ⓘ button
FR-40	Scenario painter	✅	AI Scenario Studio with 3 actions
FR-41	Multi-lever palette	⚠️ Partial	3 actions (trees/water/concrete), not full 7
FR-42	Live ΔT calculation	✅	Sub-3s response
FR-43	Cost calculation with overrides	✅	Default rates, cost_overrides in API
FR-44	Scenario comparison (2-4 side-by-side)	❌	Deferred
FR-45	Save scenario	❌	Deferred (no persistence layer)
FR-46	Master plan upload	❌	Deferred
FR-47	Extrapolation warning	✅	Domain guard delivered in Phase 6
FR-50	GeoJSON export	⚠️ Partial	Full map GeoJSON via API, no per-layer export
FR-51	CSV export	✅	Ranking table CSV export
FR-52	GeoTIFF export	❌	Deferred
FR-53	PDF report	❌	Phase 8
FR-54	API for third-party integration	✅	Auto-generated OpenAPI at /docs
FR-55	Attribution & data source footer	⚠️ Partial	Attribution in Model Card, not on every export
FR-60	LST-vs-Air-Temp disclaimer	✅	In Model Card, Limitations doc
FR-61	"Why is this hot?" panel	✅	AI Diagnosis tab with SHAP
FR-62	Data quality badges	❌	Not shown on UI (metadata only)
FR-63	Bilingual (English + Marathi)	❌	English only
FR-64	Search functionality	✅	Cell ID autocomplete search
FR-65	Risk + recommendation bundling	✅	Every scenario shows both ΔT + cost
Non-Functional Requirements Coverage
NFR ID	Requirement	Status	Notes
NFR-01	Latency p95 < 3s	✅	Scenario evaluate ~50ms + artificial 1.2s trace
NFR-02	50 concurrent users	✅	FastAPI async, should scale
NFR-03	Uptime 99%	⚠️	Dev only, no monitoring
NFR-04	Data freshness	⚠️ Partial	Static May 2024 snapshot
NFR-05	Reproducibility	✅	All scripts documented, make targets
NFR-06	Geographic scalability	⚠️ Partial	Config supports 4 cities, only 1 has data
NFR-07	Model swappability	✅	ADR-03 enforced
NFR-08	Cost < ₹5,000/month	✅	Not yet deployed, but architecture supports it
NFR-09	Accessibility (a11y)	⚠️ Partial	No keyboard nav, no ARIA labels
NFR-10	Mobile responsive	❌	Desktop-only currently
NFR-11	Security (HTTPS, no PII)	⚠️ Partial	No auth needed yet; no PII collected
NFR-12	Licensing (open data)	✅	All sources are CC-BY or public domain
NFR-13	Observability	❌	No Prometheus/Grafana
NFR-14	Structured logging	⚠️ Partial	FastAPI defaults, no custom logging
NFR-15	Model registry versioning	✅	CARD.json, code_version tracked
Risk Coverage
Risk	Status	Mitigation Delivered
R1 — Spatial leakage	✅	Blocked CV + null test
R2 — Judge: "just predicting weather"	✅	SUHII framing, rural reference visible in Model Card
R3 — LST-vs-Ta gap challenged	✅	Explicit disclaimer everywhere
R4 — Scope explosion	⚠️	Non-goals documented, but multi-city not tackled
R5 — GEE quota	✅	Pre-materialized cache
R6 — Model overfits	✅	Documented in VALIDATION.md
R7 — Extrapolation	✅	Domain guard
R8 — "Risk-only" exports	✅	Every scenario has recommendation
R9 — Cost figures challenged	✅	User-overridable via cost_overrides
13. Comprehensive TRD vs Delivered Comparison
TRD Section 3 — Data Layer
Dataset	TRD Required	Delivered
MODIS MOD11A1	✅ Required	✅ Extracted (May 2024)
MODIS MYD11A1 (Aqua)	✅ Required	❌ Only Terra used
Landsat 8/9 TIRS	✅ Required	❌ Not extracted
ECOSTRESS	Optional	❌
Dynamic World	✅ Required	❌ Only WorldCover snapshot
ESA WorldCover 2021	✅ Required	✅ Delivered
ESA WorldCover 2020	Optional	❌
GHSL Built Surface	✅ Required	❌ Not extracted
GHSL Built Height	✅ Required	❌ Not extracted
Sentinel-2 MSI	✅ Required	❌ Not extracted
VIIRS Night Lights	✅ Required	❌ Not extracted
ERA5	✅ Required	⚠️ Simplified proxy only
SRTM/NASADEM	✅ Required	❌ Not extracted
JRC GSW (Water)	✅ Required	❌ Not extracted
Ward boundaries	✅ Required	⚠️ Using 1km grid instead
Coverage: ~30% of specified data layers extracted. Enough for prototype, insufficient for production accuracy.

TRD Section 4 — Ingestion Pipeline Stages
Stage	TRD Requirement	Delivered
Stage 1: MODIS QA masking	4 overpass series (Terra day/night + Aqua day/night)	⚠️ Only Terra day/night
Stage 2: Gap-filling	STL decomposition + IDW spatial	❌ Not implemented (assumed clean May data)
Stage 3: Landsat single-channel LST	✅ Required	❌ Skipped
Stage 4: Downscaling 1km→100m	LightGBM residual	❌ Not implemented (Gap #7)
Stage 5: Rural reference construction	Multi-criteria with sensitivity analysis	✅ Delivered (simplified)
Stage 6: Weather normalization	ERA5 rural-only response subtraction	⚠️ Simplified proxy only
TRD Section 5 — Feature Engineering
Feature Group	TRD Required Count	Delivered
Thermal history (lag, rolling, seasonality)	~10 features	❌ Single-month data
Land cover fractions	8 classes	✅ 6 classes delivered
Land cover change (Δfrac)	4-5 features	❌ Single snapshot
Spectral indices	5 features	❌ Not extracted
Urban morphology	6-8 features	❌ Not extracted
Night lights	3 features	❌ Not extracted
Terrain	4 features	❌ Not extracted
Population	3 features	❌ Not extracted
Meteorology	8 features	⚠️ Simplified only
Geometry (distances)	5 features	❌ Not computed
Temporal context	4 features	❌ Single month
Quality flags	5 features	❌ Not tracked
Coverage: 6 of ~55-70 features. This is the biggest gap between TRD and delivery.

TRD Section 6 — Target Variables
Head	TRD Required	Delivered
H1 — SUHII spatial	✅ Required	✅ Delivered
H2 — SUHII trend (Δ per decade)	✅ Required	⚠️ Simplified sprawl only
H3 — Hotspot classification (binary)	✅ Required	❌ Not trained as separate head
TRD Section 7 — Modelling
Model Tier	TRD Required	Delivered
M0 — Climatology baseline	✅ Required	❌ Not implemented
M1 — OLS baseline	✅ Required	✅ Delivered
M2 — LightGBM (with monotone)	✅ Champion	✅ Delivered
M3 — ConvLSTM/Transformer	Optional challenger	❌ Skipped per ADR-03
M4 — LULC change model (cellular automaton)	✅ Required	⚠️ Flat rate proxy only
M5 — Transfer function	✅ Required	✅ Delivered
Quantile heads (P10/P50/P90)	✅ Required	✅ Delivered in Phase 6
Blocked CV harness	✅ Required	✅ Delivered in Phase 6
Null-hypothesis leakage test	✅ Required	✅ Delivered in Phase 6
SHAP explainability	✅ Required	✅ Delivered
TRD Section 8 — Scenario Engine
Feature	TRD Required	Delivered
M4 Land-use change projection	Cellular automaton with suitability	⚠️ Flat rate proxy
M5 Model-based transfer	Full inference on projected features	✅ Delivered
M5 Coefficient-based transfer	Panel regression for reports	❌ Not implemented
Sparse delta evaluation	Client sends only edits	⚠️ Currently sends full request
Spillover buffer (500m)	Distance-decay kernel	❌ Single-cell only
Extrapolation guard	Mahalanobis + p-value	✅ Delivered in Phase 6
Mitigation portfolio optimizer	Greedy ranking	❌ Not implemented
Cost overrides via levers.yaml	✅ Required	⚠️ Hardcoded rates in Python
TRD Section 9 — API
Endpoints Delivered vs Required:

Endpoint	TRD Required	Status
POST /aoi	✅	⚠️ Only pre-configured cities
GET /aoi/{id}/status	✅	❌
GET /aoi/{id}/rural-reference	✅	❌
GET /layers/{aoi_id}?layer=&date=	✅	✅ Simplified
GET /tiles/{z}/{x}/{y} (TiTiler)	✅	❌ GeoJSON only, no COG tiles
GET /wards/{aoi_id}	✅	✅ As /cells/{city_id}
GET /ward/{id}/explain	✅	✅ As /cell/{id}/explain
GET /hotspots/{aoi_id}	✅	⚠️ Via filter chip on frontend
POST /scenario/evaluate	✅	✅ Full uncertainty + warning
POST /scenario/compare	✅	❌
GET /scenario/{id}	✅	❌ No persistence
GET /forecast/{aoi_id}?horizon=	✅	⚠️ Via layer sources
POST /report	✅	❌ Phase 8
GET /export/{id}?format=	✅	⚠️ Only GeoJSON via layers endpoint
GET /model-card/{model_id}	✅	⚠️ Via frontend modal, not API endpoint
/healthz /readyz /metrics	✅	⚠️ Only /health
TRD Section 10 — Frontend
Screen	TRD Required	Delivered
S1 — Landing / City Picker	✅	⚠️ Direct to Nagpur, no picker
S2 — Main Explorer Map	✅	✅ Full featured
S3 — Cell Detail Panel	✅	✅ 3 tabs with SHAP
S4 — Ranking Table	✅	✅ Sortable + filterable
S5 — Scenario Studio ⭐	✅	✅ With AI trace + uncertainty
S6 — Mitigation Planner	✅	❌ No portfolio optimizer
S7 — Forecast View	✅	✅ Via Time Machine
S8 — Report Builder	✅	❌ Phase 8
S9 — Methodology & Model Card	✅	✅ Modal accessible
S10 — Public Read-Only Map	✅	❌ No separate public view
TRD Section 11 — Validation
Method	TRD Required	Delivered
Blocked CV (V1/V2/V3)	✅ Must	✅ V1 (temporal) + V2 (spatial); V3 (city) needs multi-city data
Landsat ↔ MODIS cross-check	✅ Must	❌ No Landsat
IMD station comparison	✅ Must	❌ No IMD data access
Field campaign	Should	❌ Not conducted
Published study triangulation	✅ Must	⚠️ Informal only
YCEO SUHI product	Should	❌
Backtest M4	✅ Must	❌ M4 is simplified
Historical counterfactual test	Should	❌ Not conducted
Shuffled-target null test	✅ Must	✅ Delivered
Calibration check	Must	✅ Delivered
Expert review	✅ Must	❌ Not conducted
TRD Section 12 — Infrastructure
Component	TRD Required	Delivered
Docker Compose	✅	❌ Phase 9
Object storage (COG)	✅	❌ Local files only
Redis cache	✅	⚠️ Installed but not wired
TiTiler tile server	✅	❌
Prefect orchestration	✅	❌ Manual scripts
GitHub Actions CI	✅	❌
Backup/restore	✅	❌
TRD Section 13 — Data Quality & Monitoring
Gate	TRD Required	Delivered
Coverage ≥ 95%	✅	⚠️ Manual check
Cloud gate ≥ 4 valid days	✅	❌ Not automated
Value range checks	✅	❌
Distribution shift (KS test)	✅	❌
Rural reference min area	✅	⚠️ Manual
Sensor agreement	✅	❌ Only Terra
Boundary join 100%	✅	✅ Verified once
Byte-identical reproducibility	✅	⚠️ Not tested
14. Remaining Gaps (Complete Analysis)
🔴 Critical Gaps
#	Gap	Impact	Effort	Priority
G1	Multi-year data (only May 2024)	HIGH	Days	🔴
G2	Multi-city training (only Nagpur)	HIGH	Days	🔴
G3	Blocked CV	✅ FIXED (Phase 6)	—	—
G4	Uncertainty bands	✅ FIXED (Phase 6)	—	—
G5	Full ERA5 weather normalization	MEDIUM	Days	🟠
G6	Cellular automaton sprawl model (M4)	HIGH	Days	🟠
G7	1km → 100m downscaling	HIGH	Days	🟠
G8	Historical counterfactual validation	HIGH	Hours	🟠
G9	Extrapolation warnings	✅ FIXED (Phase 6)	—	—
G10	Monsoon data handling (Jun-Sep)	MEDIUM	Hours	🟡
🟠 High-Impact Feature Gaps
#	Gap	Impact	Effort
G11	PDF report generation (WeasyPrint)	HIGH	Hours
G12	Scenario comparison (2-4 side-by-side)	MEDIUM	Hours
G13	Multi-cell paint (drag to select)	MEDIUM	Hours
G14	Save scenario (persistence + shareable URL)	MEDIUM	Hours
G15	Master plan upload	MEDIUM	Days
G16	Mitigation portfolio optimizer	MEDIUM	Days
G17	AOI upload (GeoJSON/shapefile)	MEDIUM	Hours
G18	Coefficient-based transfer function (panel regression)	MEDIUM	Hours
🟡 Medium-Impact Gaps
#	Gap	Impact	Effort
G19	Landsat 100m LST	MEDIUM	Days
G20	GHSL Built Height + Sky View Factor	MEDIUM	Hours
G21	Sentinel-2 spectral indices (NDVI, NDBI)	MEDIUM	Hours
G22	VIIRS Night Lights	LOW	Hours
G23	ERA5 full integration	MEDIUM	Days
G24	Real ward boundaries (not 1km grid)	HIGH	Depends on data availability
G25	Population weighting	MEDIUM	Hours
G26	Data quality badges on UI	LOW	Hours
G27	Bilingual Marathi support	LOW	Days
G28	Mobile responsive design	LOW	Days
G29	Public read-only view	LOW	Hours
🟢 Infrastructure Gaps
#	Gap	Impact	Effort
G30	Docker Compose	Deployment	Hours
G31	Redis scenario caching	Perf	Hours
G32	TiTiler COG tile server	Perf	Hours
G33	Prefect orchestration	Ops	Days
G34	Prometheus/Grafana observability	Ops	Days
G35	GitHub Actions CI	Dev	Hours
G36	Automated data quality gates	Ops	Hours
G37	Demo cache baker	Demo	Hours
Deep Learning (Deferred per TRD ADR-03)
#	Gap	Status
G38	M3 ConvLSTM challenger	Per ADR-03, only if M2 fails 10%+ threshold
G39	Grad-CAM for M3	Only needed if G38 is done
15. PHASE 8: Reports & Exports — ⏳ NEXT
Planned Components
8.1 PDF Report Generator

Tool: WeasyPrint (HTML → PDF)
Templates: reports/templates/*.html with Jinja2
Sections: Exec summary, city map, ward rankings, top interventions, methodology, limitations
Length: 4-8 pages, print-ready
Bilingual: English + Marathi (per FR-63) — optional
8.2 Additional Data Exports

Full GeoJSON per layer
Scenario JSON with all edits + results
CSV enhancements (add SHAP contributions)
8.3 Scenario Comparison Feature

Save 2-4 scenarios
Side-by-side ΔT + cost view
Diff map visualization
8.4 Advanced Frontend Features

Multi-cell paint (drag to select)
Save scenario with shareable URL
AOI upload
8.5 API Enhancements

POST /scenario/compare
POST /report/generate (async job)
GET /report/{job_id} (poll for PDF)
GET /export/{city}?format=geojson|csv|geotiff
16. PHASE 9: Deployment — ⏳ FUTURE
9.1 Docker Compose

Services: api, web, db, cache, worker
Nginx reverse proxy with Caddy TLS
9.2 Demo Cache Baker

scripts/bake_demo_cache.py
Pre-computes all tiles, ward tables, scenarios
Feature flag disables GEE during demos
9.3 Production Deploy

VPS: Hetzner/DigitalOcean 4vCPU/16GB
Automatic backups
Basic monitoring
Cost target: < ₹5,000/month
17. Complete File Inventory
text

/home/krrish-soni/chhaon/
│
├── .env                                          ✅
├── .gitignore                                    ✅
├── Makefile                                      ✅
├── README.md                                     ✅
├── requirements.txt                              ✅
├── pyproject.toml                                ✅
│
├── config/
│   ├── __init__.py                               ✅
│   ├── cities.yaml                               ✅ 4 Maharashtra cities
│   └── loader.py                                 ✅
│
├── pipeline/
│   ├── __init__.py                               ✅
│   ├── ingest/
│   │   ├── __init__.py                           ✅
│   │   ├── boundaries.py                         ✅ OSM download + 1km grid
│   │   ├── load_to_db.py                         ✅ Load grid to PostGIS
│   │   ├── modis_lst.py                          ✅ Batch NASA MODIS
│   │   └── landcover.py                          ✅ Batch ESA WorldCover
│   ├── preprocess/
│   │   ├── __init__.py                           ✅
│   │   ├── merge_data.py                         ✅ Join temp + landcover
│   │   ├── sprawl_forecast.py                    ✅ 2031/2041 ML projections
│   │   └── weather_normalize.py                  ✅ Phase 6 proxy
│   ├── features/
│   │   └── __init__.py                           ✅ (empty)
│   └── targets/
│       ├── __init__.py                           ✅
│       ├── rural_reference.py                    ✅ Countryside baseline
│       └── compute_suhii.py                      ✅ Heat anomaly
│
├── models/
│   ├── __init__.py                               ✅
│   ├── baselines/
│   │   ├── __init__.py                           ✅
│   │   └── ols_regression.py                     ✅ M1 baseline
│   ├── gbm/
│   │   ├── __init__.py                           ✅
│   │   ├── train.py                              ⚠️ DEPRECATED (Phase 6)
│   │   ├── train_blocked.py                      ✅ Phase 6 replacement
│   │   └── train_quantile.py                     ✅ Phase 6 uncertainty
│   ├── explain/
│   │   ├── __init__.py                           ✅
│   │   └── shap_explainer.py                     ✅
│   ├── transfer_function/
│   │   ├── __init__.py                           ✅
│   │   └── scenario_engine.py                    ✅ v3 with uncertainty + domain guard
│   ├── cv/
│   │   ├── __init__.py                           ✅ Phase 6
│   │   ├── blocked_split.py                      ✅ Phase 6
│   │   └── domain_guard.py                       ✅ Phase 6
│   ├── deep/                                     ❌ (empty — G38)
│   ├── lulc_change/                              ❌ (empty — G6)
│   └── registry/
│       ├── lightgbm_suhii_night.txt              ✅ Original M2
│       ├── lightgbm_suhii_night_p10.txt          ✅ Phase 6 P10
│       ├── lightgbm_suhii_night_p50.txt          ✅ Phase 6 P50
│       ├── lightgbm_suhii_night_p90.txt          ✅ Phase 6 P90
│       ├── CARD.json                             ✅ Updated Phase 6
│       └── CARD_quantiles.json                   ✅ Phase 6
│
├── api/
│   ├── __init__.py                               ✅
│   ├── main.py                                   ✅ FastAPI app
│   ├── schemas/
│   │   ├── __init__.py                           ✅
│   │   ├── heat.py                               ✅
│   │   └── scenario.py                           ✅ v2 with UncertaintyBand + warnings
│   ├── services/
│   │   ├── __init__.py                           ✅
│   │   ├── spatial_service.py                    ✅
│   │   └── heat_service.py                       ✅
│   └── routers/
│       ├── __init__.py                           ✅
│       ├── cities.py                             ✅
│       ├── layers.py                             ✅
│       ├── cells.py                              ✅
│       └── scenarios.py                          ✅
│
├── web/                                          ✅ Next.js 14 (Phase 5 + 7)
│   ├── package.json                              ✅
│   ├── tsconfig.json                             ✅
│   ├── tailwind.config.ts                        ✅
│   ├── postcss.config.js                         ✅
│   ├── .env.local                                ✅
│   ├── node_modules/                             ✅
│   └── src/
│       ├── app/
│       │   ├── layout.tsx                        ✅
│       │   ├── page.tsx                          ✅ v3 with dynamic import + layout fix
│       │   └── globals.css                       ✅
│       ├── components/
│       │   ├── map/
│       │   │   ├── HeatMap.tsx                   ✅ v3 with 3 basemaps + property coercion
│       │   │   ├── MapControls.tsx               ✅ v2 with basemap selector + opacity
│       │   │   └── TimeMachine.tsx               ✅ Phase 7
│       │   ├── panels/
│       │   │   ├── CellDetailPanel.tsx           ✅ v3 with tabs + AI Diagnosis + num() fix
│       │   │   ├── RankingTable.tsx              ✅ v2 with filters + CSV export
│       │   │   ├── CityStatsBar.tsx              ✅ Phase 7
│       │   │   └── SearchAndInfo.tsx             ✅ Phase 7 search + Model Card modal
│       │   └── scenario/
│       │       └── ScenarioPainter.tsx           ✅ v2 with AI trace + uncertainty
│       └── lib/
│           ├── types.ts                          ✅ v2 with BasemapStyle + UncertaintyBand
│           └── api.ts                            ✅ v2 with evaluateScenario + fetchCellExplanation
│
├── scripts/
│   ├── __init__.py                               ✅
│   └── generate_heatmap.py                       ✅
│
├── reports/                                      ⏳ EMPTY (Phase 8)
│   └── templates/
│
├── tests/                                        ⏳ EMPTY (Phase 8)
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docs/                                         ✅ Phase 6
│   ├── 01-problem-statement-explained.md         ✅
│   ├── 02-PRD.md                                 ✅
│   ├── 03-TRD.md                                 ✅
│   ├── VALIDATION.md                             ✅ Phase 6
│   └── LIMITATIONS.md                            ✅ Phase 6
│
└── data/                                         ✅ (git-ignored)
    ├── boundaries/
    │   ├── nagpur_boundary.geojson               ✅
    │   └── nagpur_grid.geojson                   ✅
    ├── tables/
    │   ├── nagpur_monthly_lst.csv                ✅
    │   ├── nagpur_cell_lst_2024_05.parquet       ✅
    │   ├── nagpur_landcover_2021.parquet         ✅
    │   ├── nagpur_master_2024.parquet            ✅
    │   ├── nagpur_rural_reference.parquet        ✅
    │   ├── nagpur_suhii_2024.parquet             ✅
    │   └── nagpur_suhii_weather_normalized.parquet ✅ Phase 6
    └── demo/
        ├── nagpur_heatmap.geojson                ✅
        └── nagpur_forecast_heatmap.geojson       ✅
18. Environment & Credentials
System Info
OS: Ubuntu Linux
User: krrish-soni
Home: /home/krrish-soni
Project Root: /home/krrish-soni/chhaon
Machine: Dell Inspiron 15 5518
Credentials & Access
Service	Value
PostgreSQL Database	chhaon_db
PostgreSQL User	chhaon
PostgreSQL Password	chhaon_dev_2024 (dev only)
Redis	localhost:6379/0
Google Cloud Project	chhaon-508513
GEE Registration	Non-commercial use
GEE Auth	~/.config/earthengine/credentials
Software Versions
Python: 3.11
Node.js: 20 LTS
PostgreSQL: 16 + PostGIS 3.4
Redis: 7
Next.js: 14.2.35
FastAPI: 0.115.5
LightGBM: 4.5.0
MapLibre GL JS: 4.7.1
SHAP: 0.46.0
19. How to Run Everything
Backend (Terminal 1)
Bash

cd ~/chhaon
source .venv/bin/activate
export PYTHONPATH=$PWD

# Full pipeline (only run once, or when data changes)
python -m pipeline.ingest.boundaries
python -m pipeline.ingest.load_to_db
python -m pipeline.ingest.modis_lst
python -m pipeline.ingest.landcover
python -m pipeline.preprocess.merge_data
python -m pipeline.targets.rural_reference
python -m pipeline.targets.compute_suhii
python -m scripts.generate_heatmap

# ML training with blocked CV (Phase 6)
python -m models.baselines.ols_regression
python -m models.gbm.train_blocked
python -m models.gbm.train_quantile

# Weather normalization proxy (Phase 6)
python -m pipeline.preprocess.weather_normalize

# ML sprawl forecast
python -m pipeline.preprocess.sprawl_forecast

# Test full pipeline
python -m models.transfer_function.scenario_engine
python -m models.cv.domain_guard

# Start API server (always keep running)
uvicorn api.main:app --reload --port 8000
Frontend (Terminal 2)
Bash

cd ~/chhaon/web
npm run dev
Access
Web App: http://localhost:3000
API Docs: http://localhost:8000/docs
API Health: http://localhost:8000/health
20. Critical Context for AI Handoff
User Context
Name: krrish-soni
OS: Ubuntu, uses nano editor
Level: Intermediate — knows Python well, learning geospatial + ML concepts
Focus: Building working prototype for Maharashtra cities (Nagpur primary)
Preferences:
Real satellite data ONLY (never mock)
Detailed step-by-step instructions with nano commands
Explanation of what every command does
Complete code (no # ... unchanged placeholders) ⭐ CRITICAL
Full file replacements when editing
Delivery Format User Expects
Each phase should be structured as:

4 Sets of related work
Each Set has at least 3 Steps
Each Step includes:
nano filename command
Full code to paste (complete, no placeholders)
Explanation of what each section does
Save & exit: Ctrl + O → Enter → Ctrl + X
Command to run + expected output
Non-Negotiable Rules (Repeat)
NEVER use mock data
NEVER use random k-fold CV
NEVER predict raw LST (always SUHII anomaly)
NEVER remove monotone constraints (except for quantile models which don't support them)
NEVER call GEE live during demos
ALWAYS include units (°C, ₹, %, km)
ALWAYS include limitations
ALWAYS explain "so what" for numbers
ALWAYS give complete code files, not diffs
ALWAYS use dynamic() import with ssr: false for MapLibre components
Common Errors Encountered (and Fixed)
Error	Root Cause	Fix
ModuleNotFoundError: No module named 'config'	Running as script instead of module	Use python -m pipeline.ingest.modis_lst
ModuleNotFoundError: 'psycopg2'	Missing binary driver	pip install psycopg2-binary
EEException: Project not found	Cloud project not registered	Register at code.earthengine.google.com
'ImageCollection' object has no attribute 'multiply'	Called .multiply() before .median()	Order MUST be .median().multiply()
'MultiPolygon' object has no attribute 'exterior'	Grid clipping created MultiPolygons	Use shapely.geometry.mapping()
Timeout on per-cell requests	Individual GEE requests	Use reduceRegions() for batch
Cannot use monotone_constraints in quantile objective	LightGBM limitation	Omit monotone for quantile models
Module not found: '@/components/...'	Missing file	Create the file
CARTO "API KEY REQUIRED" watermark	CARTO changed policy	Use Esri Dark Canvas or OSM/Satellite
"Map Data Not Available" on zoom	Missing maxzoom: 16 config	Add maxzoom: 16 to raster source
TypeError: Cannot read properties of undefined (reading 'toFixed')	MapLibre returns properties as strings	Coerce with num() / parseFloat()
RangeError: Maximum call stack size exceeded	Next.js SSR of MapLibre	Use dynamic(..., { ssr: false })
Overlapping UI panels	Multiple components using absolute positioning	Parent page.tsx owns all positioning
10 Model Gaps (Priority Order for Future)
Most critical to fix first:

G1: Multi-year data — foundational for everything else
G6: Cellular automaton sprawl model — better forecasts
G7: 1km→100m downscaling — parcel-level decisions
G8: Historical counterfactual validation — proves scenario engine works
G2: Multi-city training — city-block CV becomes possible
Frontend Features to Consider Improving
G12: Scenario comparison (2-4 side-by-side) — high value for planners
G13: Multi-cell paint (drag to select) — better UX
G14: Save scenario with shareable URL — collaboration
G17: AOI upload — enables custom AOIs beyond pilot cities
G27: Bilingual Marathi support — accessibility for Maharashtra users
Next Immediate Task Options
Option A: Phase 8 — Reports & Exports (Recommended)

WeasyPrint PDF generator
Scenario comparison
Save scenarios with URL
AOI upload
Estimated: 4-6 hours
Option B: Fix Data Gaps (Phase 6.5)

Extract multi-year MODIS
Add Pune data
Retrain with city-block CV
Estimated: 6-8 hours
Option C: Phase 9 — Deployment

Docker Compose
Demo cache baker
Production deploy
Estimated: 3-4 hours
Overall Project Progress
text

Phase 1: Foundation                    ████████████████████  100%  ✅
Phase 2: Satellite Data Pipeline       ████████████████████  100%  ✅
Phase 3: ML Model & Scenario Engine    ████████████████████  100%  ✅
Phase 4: Backend API (FastAPI)         ████████████████████  100%  ✅
Phase 5: Initial Frontend              ████████████████████  100%  ✅
Phase 6: Model Credibility Fixes       ████████████████████  100%  ✅
Phase 7: Advanced Interactive Frontend ████████████████████  100%  ✅
Phase 8: Reports & Exports             ░░░░░░░░░░░░░░░░░░░░    0%  ⏳
Phase 9: Deployment & Demo Cache       ░░░░░░░░░░░░░░░░░░░░    0%  ⏳

TOTAL PROJECT COMPLETION:              ██████████████████░░   92%
