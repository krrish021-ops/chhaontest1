# Chhaon (छांव) — Pan-India Urban Heat Intelligence & Decision-Support GIS

**Chhaon** (*छांव*, Hindi for *"Shade"*) is an end-to-end satellite remote sensing, machine learning attribution, and urban cooling simulation platform designed for Indian municipal corporations, state climate change cells, smart city missions, and urban planners.

It integrates multi-sensor Earth observation data from **NASA MODIS**, **ESA WorldCover (10 m)**, **Copernicus Sentinel-2**, **NASA SRTM**, **JRC Global Human Settlement Layer (GHSL)**, **NOAA VIIRS**, and **ECMWF ERA5-Land** to map, explain, and mitigate **Surface Urban Heat Island Intensity (SUHII)** across India—operating seamlessly from a **Pan-India national macro-grid** down to **1 km × 1 km municipal ward-level grids**.

---

## Table of Contents

1. [Why Chhaon? The Urban Heat Challenge in India](#1-why-chhaon-the-urban-heat-challenge-in-india)
2. [Key Platform Capabilities](#2-key-platform-capabilities)
3. [Multi-Scale Spatial Coverage](#3-multi-scale-spatial-coverage)
4. [Scientific & Remote Sensing Methodology](#4-scientific--remote-sensing-methodology)
5. [Four-Layer Thermal Analytics Engine](#5-four-layer-thermal-analytics-engine)
6. [Machine Learning, SHAP Attribution & Cooling Simulator](#6-machine-learning-shap-attribution--cooling-simulator)
7. [System Architecture & File-by-File Breakdown](#7-system-architecture--file-by-file-breakdown)
8. [Satellite Data Sources & GEE Specifications](#8-satellite-data-sources--gee-specifications)
9. [Complete REST API Reference](#9-complete-rest-api-reference)
10. [Google Earth Engine Ingestion Pipeline Guide](#10-google-earth-engine-ingestion-pipeline-guide)
11. [Local Installation & Setup (Ubuntu / Linux / macOS)](#11-local-installation--setup-ubuntu--linux--macos)
12. [Cloud Deployment Guide (Vercel + Render / Docker)](#12-cloud-deployment-guide-vercel--render--docker)
13. [Core Engineering Guardrails & Data Integrity Rules](#13-core-engineering-guardrails--data-integrity-rules)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. Why Chhaon? The Urban Heat Challenge in India

During the pre-monsoon summer peak (May), Indian cities experience severe thermal stress. While daytime land surface temperatures (`LST_day`) regularly exceed **42 °C – 47 °C**, **nighttime Surface Urban Heat Island Intensity (`SUHII_night`)** is the primary driver of heat-related morbidity and mortality:

- **Nocturnal Heat Retention**: High-thermal-mass concrete, asphalt, and dense low-sky-view-factor (`SVF`) street canyons trap shortwave radiation during the day and re-emit longwave radiation throughout the night.
- **Physiological Stress**: When nighttime temperatures remain **+2.5 °C to +6.0 °C warmer** than the surrounding rural countryside, the human body cannot recover from daytime heat exposure—disproportionately impacting informal settlements and households without active air conditioning.
- **Actionable Municipal Triage**: Most Indian Heat Action Plans (HAPs) rely on a single airport weather station to represent an entire city. Chhaon replaces single-point station readings with **cell-by-cell spatial intelligence**, identifying *which specific 1 km² municipal zones* are overheating, *why* they are overheating, and *how much cooling (`Δ°C`)* can be achieved through targeted urban forestry, cool roofs, and water body restoration.

---

## 2. Key Platform Capabilities

| Module | Capability | Technical Implementation |
| :--- | :--- | :--- |
| **Pan-India & Municipal GIS** | Seamless switching between the **All-India National Monitoring Grid** (`~70 km` cells) and **1 km × 1 km Municipal Grids** (`Delhi`, `Pune`, `Nagpur`, and extensible to all Indian cities). | `MapLibre GL JS` vector rendering with dynamic color interpolation injected beneath basemap symbol layers (`firstSymbolId`) so city names, roads, and state borders remain sharp. |
| **110+ Indian City Directory** | Built-in gazetteer of **110+ Indian cities and district headquarters** across all States and Union Territories, plus live **OpenStreetMap Nominatim** geocoding fallback for any town or locality. | Instant autocomplete search, camera fly-to (`flyTo`), and automatic selection of the underlying thermal analysis cell in `web/src/lib/indianCities.ts`. |
| **Four-Layer Thermal Switcher** | Instant live switching between **2024 Observed**, **2024 Weather-Adjusted (ERA5)**, **2031 BAU Projection**, and **2041 BAU Projection**. | Updates map polygon fills, regional KPI cards, city directory values, hotspot rankings, and location trajectories in real time. |
| **Plain-English Thermal Dossier** | Translates raw satellite metrics into clear decision-support dossiers with severity badges (`CRITICAL HEAT ISLAND`, `HIGH HEAT STRESS`, `MODERATE WARMING`, `LOW / BASELINE`), daytime/nighttime LST, and 10 m land-cover composition bars. | Docked 390 px left analytical workspace in `web/src/app/page.tsx` with zero floating-panel clutter. |
| **SHAP Physical Attribution** | Per-cell breakdown of physical drivers pushing nighttime temperatures upward (`+°C` from impervious surface, VIIRS anthropogenic heat, low albedo) or downward (`-°C` from tree canopy evapotranspiration and water bodies). | `LightGBM` + `TreeSHAP` (`models/explain/shap_explainer.py`) and physical attribution profiles. |
| **Cooling Intervention Planner** | Interactive sliders for **Urban Tree Canopy Expansion (`+%`)**, **Cool / Reflective Roof Mandate (`+%`)**, and **Pervious Surface & Water Restoration (`+%`)** with real-time `Δ°C` cooling estimates. | Physics-constrained land-cover simplex transfer function (`models/transfer_function/scenario_engine.py`). |
| **Automated Audit PDF Dossier** | One-click generation of print-ready municipal thermal audit reports with statistical tables, hotspot rankings, and policy recommendations. | `WeasyPrint` + `Jinja2` + `Matplotlib` (`reports/generator.py`). |

---

## 3. Multi-Scale Spatial Coverage

Chhaon operates across two complementary spatial scales:

### Tier 1: All-India National Monitoring Macro-Grid (`city_id: "india"`)
- **Resolution**: `0.65° × 0.65°` (~70 km × 70 km) border-clipped cells (`IN0001`–`IN0659`) covering the Indian mainland and island territories.
- **Valid Monitored Landmass Zones**: 598 quality-screened cells (ocean/glacier fringe cells with no valid LST are automatically excluded).
- **Rural Baseline Methodology**: Each macro-cell is evaluated against a **150 km focal-mean non-urban regional ring** so that Himalayan, coastal, arid (Thar), and peninsular zones are compared against their true local non-urban climate baseline rather than a single national average.

### Tier 2: 1 km × 1 km Municipal Ward-Level Grids
Pre-built and verified high-resolution municipal grids included out of the box:
1. **Delhi NCT (`city_id: "delhi"`)**: **575 cells** (`DL0001`–`DL0575`), covering the core urban extent `[77.08°E, 28.52°N, 77.30°E, 28.72°N]`.
2. **Pune, Maharashtra (`city_id: "pune"`)**: **414 cells** (`P0001`–`P0414`), covering the Pune Municipal Corporation (PMC) boundary.
3. **Nagpur, Maharashtra (`city_id: "nagpur"`)**: **229 cells** (`C0001`–`C0229`), covering the Nagpur Municipal Corporation (NMC) boundary.

### Pre-Configured Indian Cities Ready for GEE Ingestion (`config/cities.yaml`)
`config/cities.yaml` includes bounding boxes, centroids, climate zones, and cell prefixes for **Mumbai, Bengaluru, Ahmedabad, Hyderabad, Chennai, Kolkata, Jaipur, Lucknow, and Aurangabad (Chhatrapati Sambhajinagar)**, plus automatic OpenStreetMap boundary lookup for any other Indian municipality.

---

## 4. Scientific & Remote Sensing Methodology

### 4.1 Land Surface Temperature (LST) Extraction & Quality Control
Daily 1 km thermal infrared observations are sourced from **NASA MODIS Terra (`MODIS/061/MOD11A1`)** for the pre-monsoon summer month of **May** across **2020–2024**:
- **Bitmask QA Filtering**: Only pixels where `QC_Day` and `QC_Night` mandatory QA bits `(bits 0–1) <= 1` (good quality, cloud-free) and average emissivity error `(bits 2–3) <= 2` are retained.
- **Kelvin-to-Celsius Conversion**:
  $$\text{LST (}^\circ\text{C)} = (\text{DN} \times 0.02) - 273.15$$

### 4.2 Elevation-Controlled Rural Reference Ring
To avoid confounding urban heat with topographic elevation differences or water bodies, Chhaon constructs an **Elevation-Controlled Rural Reference Ring** for each municipality:
1. **Spatial Ring**: A **5 km buffer ring** immediately outside the municipal boundary (`city_geom.buffer(5000).difference(city_geom)`).
2. **Land-Cover Mask (`ESA WorldCover 10 m`)**: Excludes all built-up pixels (`Map != 50`), permanent water bodies (`Map != 80`), and bare/snow anomalies (`Map != 60`).
3. **Topographic Mask (`NASA SRTM 30 m`)**: Retains only rural pixels whose elevation lies within **$\pm 100\text{ m}$** of the urban core's mean elevation:
   $$|Z_{\text{rural}} - \bar{Z}_{\text{urban}}| \le 100\text{ m}$$
4. **Robust Percentile Trimming**: Trims the bottom 5% and top 5% (`[Q05, Q95]`) of rural LST pixels before computing the rural baseline $\text{LST}_{\text{rural}}$.

### 4.3 Surface Urban Heat Island Intensity (SUHII)
For every grid cell $i$, Daytime and Nighttime SUHII are computed as:
$$\text{SUHII}_{\text{night}, i} = \text{LST}_{\text{night}, i} - \overline{\text{LST}}_{\text{night, rural}}$$
$$\text{SUHII}_{\text{day}, i} = \text{LST}_{\text{day}, i} - \overline{\text{LST}}_{\text{day, rural}}$$

### 4.4 Spectral Indices & Broadband Surface Albedo (`Sentinel-2 SR`)
Cloud-screened (`CLOUDY_PIXEL_PERCENTAGE < 20%`, `SCL` mask removing clouds, cirrus, and shadows) Sentinel-2 Level-2A Harmonized surface reflectance (`B2, B3, B4, B8, B11, B12` scaled by `1/10000`) is used to compute:
- **Normalized Difference Vegetation Index (NDVI)**:
  $$\text{NDVI} = \frac{\rho_{\text{NIR}} - \rho_{\text{Red}}}{\rho_{\text{NIR}} + \rho_{\text{Red}}} = \frac{B8 - B4}{B8 + B4}$$
- **Normalized Difference Built-Up Index (NDBI)**:
  $$\text{NDBI} = \frac{\rho_{\text{SWIR1}} - \rho_{\text{NIR}}}{\rho_{\text{SWIR1}} + \rho_{\text{NIR}}} = \frac{B11 - B8}{B11 + B8}$$
- **Modified Normalized Difference Water Index (MNDWI)**:
  $$\text{MNDWI} = \frac{\rho_{\text{Green}} - \rho_{\text{SWIR1}}}{\rho_{\text{Green}} + \rho_{\text{SWIR1}}} = \frac{B3 - B11}{B3 + B11}$$
- **Broadband Shortwave Albedo (Liang, 2001)**:
  $$\alpha = 0.356 B2 + 0.130 B4 + 0.373 B8 + 0.085 B11 + 0.072 B12 - 0.0018$$

### 4.5 3D Urban Morphology & Sky-View Factor Proxy (`JRC GHSL`)
Using the **JRC Global Human Settlement Layer (`GHS_BUILT_H`, 100 m)** mean building height $H_{\text{mean}}$ (m) and built-up fraction $f_{\text{built}}$, Chhaon computes a physically bounded **Sky-View Factor Proxy ($\text{SVF}_{\text{proxy}} \in [0.1, 1.0]$)** representing how much of the overlying hemisphere is visible for nocturnal radiative cooling:
$$\text{SVF}_{\text{proxy}} = \text{clip}\left(\frac{1}{1 + 0.08 \cdot H_{\text{mean}} \cdot (1 + 2 f_{\text{built}})}, \; 0.10, \; 1.00\right)$$

---

## 5. Four-Layer Thermal Analytics Engine

Every GeoJSON feature in `data/demo/` and `web/public/demo/` carries four distinct thermal layers that can be toggled live in the top navigation bar:

1. **`observed` (`suhii_night`) — 2024 Observed Satellite**:
   - Direct May 2024 MODIS nighttime SUHII observation (°C above rural baseline).
2. **`normalized` (`suhii_night_normalized`) — 2024 Weather-Adjusted (ERA5)**:
   - Removes synoptic meteorological anomalies (wind speed, relative humidity, and arid bare-soil radiative bias) to isolate the **structural urban heat island** attributable to concrete density (`frac_built`), tree canopy deficit (`frac_tree`), water buffering (`frac_water`), surface albedo (`albedo`), and nighttime anthropogenic radiance (`night_lights_mean`).
3. **`forecast_2031` (`suhii_night_2031`) — 2031 Business-As-Usual (BAU) Projection**:
   - Combines the regional climate warming baseline (`+0.42 °C` by 2031) with cell-level urban densification trajectories derived from built-up intensity, VIIRS nighttime light growth, and vegetation deficit.
4. **`forecast_2041` (`suhii_night_2041`) — 2041 Long-Term BAU Projection**:
   - Combines the long-term regional warming baseline (`+1.18 °C` by 2041) with compounding impervious surface intensification.

---

## 6. Machine Learning, SHAP Attribution & Cooling Simulator

### 6.1 LightGBM Spatial Model (`models/registry/`)
- **Features (12 Physical Predictors)**:
  `frac_built`, `frac_tree`, `frac_water`, `frac_crop`, `frac_grass`, `ndvi`, `ndbi`, `mndwi`, `albedo`, `building_height_mean`, `night_lights_mean`, `svf_proxy`.
- **Spatial Block Cross-Validation (`models/validation/spatial_cv.py`)**:
  Evaluated using geographic spatial blocks (`2 km × 2 km`) rather than random row splits to prevent spatial autocorrelation leakage.

### 6.2 Per-Cell TreeSHAP Attribution (`models/explain/shap_explainer.py`)
For any selected cell $i$, Chhaon decomposes the predicted nighttime SUHII into additive physical contributions:
$$\widehat{\text{SUHII}}_{\text{night}, i} = \phi_0 + \sum_{k=1}^{12} \phi_{i, k}$$
where $\phi_0$ is the city baseline expectation and $\phi_{i, k}$ is the exact **TreeSHAP** value (in `°C`) of feature $k$ in cell $i$.

### 6.3 Physics-Constrained Cooling Scenario Simulator (`models/transfer_function/scenario_engine.py`)
When a user simulates urban interventions (e.g., `+15% Tree Canopy`, `+30% Cool Roofs`, `+5% Water Restoration`):
1. **Simplex Conservation**: Land-cover fractions are re-normalized so that:
   $$f_{\text{built}} + f_{\text{tree}} + f_{\text{water}} + f_{\text{crop}} + f_{\text{grass}} + f_{\text{bare}} = 1.0$$
2. **Coupled Biophysical Co-Evolution**:
   - Increasing `frac_tree` proportionally increases `ndvi` (`+0.45 * Δtree`) and lowers `ndbi` (`-0.30 * Δtree`).
   - Increasing Cool Roof coverage increases cell `albedo` (`+0.25 * Δroof_frac * frac_built`).
   - Expanding `frac_water` increases `mndwi` (`+0.50 * Δwater`).
3. **Physical Plausibility Clamping**: Total predicted cooling $\Delta \text{SUHII}$ is bounded within empirically realistic limits (`[-3.5 °C, +1.0 °C]`).

---

## 7. System Architecture & File-by-File Breakdown

[![Architecture diagram of krrish021-ops/chhaontest1](https://gitdiagram.com/krrish021-ops/chhaontest1/diagram.png)](https://gitdiagram.com/krrish021-ops/chhaontest1?utm_source=readme&utm_medium=picture)

## 8. Satellite Data Sources & GEE Specifications
Sensor / Product	Earth Engine Asset ID	Spatial Resolution	Temporal Coverage	Extracted Features
MODIS Terra LST	MODIS/061/MOD11A1	1,000 m	Daily (May 2020–2024)	lst_day, lst_night, suhii_day, suhii_night
ESA WorldCover v200	ESA/WorldCover/v200/2021	10 m	Annual Baseline	frac_built, frac_tree, frac_water, frac_crop, frac_grass, frac_bare
Sentinel-2 MSI L2A	COPERNICUS/S2_SR_HARMONIZED	10 m – 20 m	5-day revisit (May)	ndvi, ndbi, mndwi, albedo
NASA SRTM Digital Elevation	USGS/SRTMGL1_003	30 m	Static DEM	Elevation-matched (±100 m) rural reference ring mask
JRC GHSL Built Height	JRC/GHSL/P2023A/GHS_BUILT_H	100 m	Epoch 2023	building_height_mean, svf_proxy
NOAA VIIRS Nighttime Lights	NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG	463 m	Monthly (May)	night_lights_mean (avg_rad in 
nW
⋅
cm
−
2
⋅
sr
−
1
nW⋅cm 
−2
 ⋅sr 
−1
 )
ECMWF ERA5-Land	ECMWF/ERA5_LAND/MONTHLY_AGGR	~11,132 m	Monthly (May)	temp_2m, wind_speed_10m, rh for synoptic normalization
## 9. Complete REST API Reference
When the FastAPI backend is running on http://localhost:8000, full interactive Swagger documentation is available at http://localhost:8000/docs.

9.1 List Configured Jurisdictions
Endpoint: GET /api/v1/spatial/cities
Response (200 OK):
JSON

[
  {
    "id": "india",
    "name": "All India (National)",
    "state": "Pan-India",
    "climate_zone": "All Indian Climate Zones",
    "center": [78.9629, 22.5937],
    "zoom": 4.6,
    "has_data": true
  },
  {
    "id": "delhi",
    "name": "Delhi",
    "state": "NCT of Delhi",
    "climate_zone": "Composite",
    "center": [77.209, 28.6139],
    "zoom": 10.5,
    "has_data": true
  }
]
9.2 Fetch Multi-Layer Heatmap GeoJSON
Endpoint: GET /api/v1/heat/{city_id}/geojson?layer={observed|normalized|forecast}
Description: Returns a GeoJSON FeatureCollection where each polygon feature includes cell_id, location_name, suhii_night, suhii_night_normalized, suhii_night_2031, suhii_night_2041, lst_day, lst_night, and land-cover fractions.
9.3 Fetch Ranked Thermal Hotspots
Endpoint: GET /api/v1/heat/{city_id}/rankings?sort_by=suhii_night&limit=50
Description: Returns cells sorted in descending order of nighttime SUHII, automatically filtering or pushing null/NaN cells to the bottom.
9.4 Fetch Per-Cell SHAP Physical Attribution
Endpoint: GET /api/v1/heat/{city_id}/cells/{cell_id}/shap
Example: GET /api/v1/heat/nagpur/cells/C0427/shap
Response (200 OK):
JSON

{
  "city_id": "nagpur",
  "cell_id": "C0427",
  "predicted_suhii": 5.45,
  "base_value": 2.91,
  "cross_city_model": false,
  "extrapolation_warning": null,
  "drivers": [
    {
      "feature": "frac_built",
      "label": "Built-up Impervious Fraction",
      "feature_value": 0.84,
      "shap_value": 1.42,
      "direction": "warming"
    }
  ]
}
9.5 Simulate Cooling Interventions
Endpoint: POST /api/v1/scenarios/{city_id}/simulate
Request Body:
JSON

{
  "cell_id": "C0427",
  "tree_canopy_delta_pct": 15.0,
  "cool_roof_Converter_pct": 30.0,
  "water_body_delta_pct": 5.0,
  "green_space_delta_pct": 10.0
}
9.6 Generate & Download Municipal Thermal Audit PDF
Endpoint: GET /api/v1/reports/{city_id}/pdf
Description: Streams a print-ready application/pdf thermal audit report for the requested municipality.
10. Google Earth Engine Ingestion Pipeline Guide
Chhaon includes a universal 7-step Google Earth Engine ingestion script (pipeline/ingest/ingest_city.py) that can ingest any Indian city:

How the 7-Step Pipeline Works
Step 1 — Boundary & 1 km Grid Generation: Queries OpenStreetMap (osmnx.geocode_to_gdf) or uses the configured bounding box in config/cities.yaml to construct a UTM-projected 1 km × 1 km fishnet grid clipped to the city boundary (data/boundaries/{city}_grid.geojson).
Step 2 — MODIS LST & Rural Ring SUHII: Extracts May daytime/nighttime LST and elevation-matched rural ring baselines across 2020–2024.
Step 3 — ESA WorldCover 10 m Fractions: Extracts frac_built, frac_tree, frac_water, frac_crop, frac_grass, and frac_bare.
Step 4 — Sentinel-2 Spectral & Albedo: Extracts cloud-masked ndvi, ndbi, mndwi, and broadband albedo.
Step 5 — JRC GHSL Morphology: Extracts building_height_mean and svf_proxy.
Step 6 — NOAA VIIRS Nighttime Radiance: Extracts night_lights_mean.
Step 7 — ERA5-Land Meteorology & Master Merge: Merges all features on (cell_id, year, month) into data/tables/{city}_feature_matrix.parquet.
Commands to Ingest Any New Indian City
Bash

cd /home/krrish-soni/Downloads/chhaontest1-main
source .venv/bin/activate

# Authenticate with Google Earth Engine (one-time setup)
earthengine authenticate

# Fast 5-year pre-monsoon (May) ingestion for any city in config/cities.yaml
python -m pipeline.ingest.ingest_city mumbai --fast
python -m scripts.build_heatmaps mumbai

# Or ingest Jaipur, Bengaluru, Hyderabad, Chennai, Kolkata, Lucknow, etc.
python -m pipeline.ingest.ingest_city jaipur --fast
python -m scripts.build_heatmaps jaipur
11. Local Installation & Setup (Ubuntu / Linux / macOS)
Prerequisites
Python 3.11 (Note: Python 3.11 is required so pre-compiled wheels for pandas, scipy, lightgbm, shap, and geopandas install in seconds without compiling C/Fortran from source)
Node.js 18+ & npm
uv (fast Python environment & package manager)
Step 1: Clone the Repository & Create the Python 3.11 Environment
Bash

git clone https://github.com/krrish021-ops/chhaontest1.git
cd chhaontest1

# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Create Python 3.11 virtual environment & install all dependencies
uv venv .venv --python 3.11
source .venv/bin/activate
uv pip install -r requirements.txt
Step 2: Start the FastAPI Backend Server (Terminal 1)
Bash

cd chhaontest1
source .venv/bin/activate
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
Verify health check: http://localhost:8000/health
Verify Swagger UI: http://localhost:8000/docs
Step 3: Start the Next.js GIS Frontend (Terminal 2)
Bash

cd chhaontest1/web
npm install
npm run dev
Open http://localhost:3000 in your browser.
12. Cloud Deployment Guide (Vercel + Render / Docker)
12.1 Frontend Deployment on Vercel
Push your repository to GitHub (krrish021-ops/chhaontest1).
In Vercel, import the GitHub repository and configure:
Framework Preset: Next.js
Root Directory: web
Build Command: npm run build
Environment Variable (optional if backend is hosted separately):
NEXT_PUBLIC_API_URL=https://your-fastapi-backend.onrender.com
Instant Static Fallback: Because all enriched 4-layer GeoJSON files are mirrored inside web/public/demo/, the Vercel deployment renders the All-India map, Delhi, Pune, Nagpur, all 4 thermal layers, the 110+ Indian City Directory, heat driver attribution, and cooling simulator with zero latency even if the Python backend is asleep or not yet connected.
12.2 Backend Deployment on Render / Railway
Create a new Web Service pointing to the repository root.
Configure:
Runtime: Python 3.11 (.python-version is included in root)
Build Command: pip install -r requirements.txt
Start Command: uvicorn api.main:app --host 0.0.0.0 --port $PORT
13. Core Engineering Guardrails & Data Integrity Rules
Never Fabricate a Number: If a satellite pixel or grid cell lacks cloud-free observations, Chhaon returns None / "No data" or excludes the unmonitored ocean/border cell—it never invents synthetic numbers.
Always Join on cell_id: All spatial grids (*_grid.geojson) and tabular feature matrices (*_feature_matrix.parquet) are joined strictly on cell_id (scripts/build_heatmaps.py), never by DataFrame row index.
Quarantined Legacy Scripts: scripts/rebuild_city_grids.py is intentionally quarantined (sys.exit(1)) so that real municipal polygon grids can never be overwritten by unaligned bounding-box grids.
14. Troubleshooting
Symptom	Cause	Solution
pip install hangs compiling scipy or pandas on Ubuntu	System python3 defaults to Python 3.14, which lacks pre-built wheels for pinned scientific packages.	Use uv venv .venv --python 3.11 and source .venv/bin/activate.
ModuleNotFoundError: No module named 'dotenv' when running uvicorn	Running bare uvicorn invokes the system /usr/bin/uvicorn instead of .venv.	Run python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000 inside .venv.
Port 3000 already in use on Ubuntu	Local grafana-server service is listening on port 3000.	Stop Grafana with sudo systemctl stop grafana-server, then run npm run dev.
Git merge conflict markers break next build on Vercel	Pulling unrelated git histories left <<<<<<< HEAD markers in source files.	Run git checkout --ours . && git add -A && git commit -m "fix conflicts" && git push origin main.
