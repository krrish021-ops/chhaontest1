# Chhaon (छांव) — Pan-India Urban Heat Intelligence & Decision-Support GIS

**Chhaon** is a satellite-driven Urban Heat Island (UHI) monitoring, attribution, and cooling intervention decision-support system built for Indian municipal corporations, state climate cells, and urban planners.

It combines **NASA MODIS** thermal infrared observations, **ESA WorldCover (10 m)** land cover, **Sentinel-2** surface reflectance, **JRC GHSL** building morphology, **NOAA VIIRS** nighttime radiance, and **ECMWF ERA5-Land** meteorology to quantify **Surface Urban Heat Island Intensity (SUHII)** across India—from a **Pan-India national monitoring macro-grid** down to **1 km × 1 km municipal ward-level grids**.

---

## Key Capabilities

### 1. Multi-Scale Spatial Coverage Across India
- **All-India National Monitoring Grid (`india`)**: Border-clipped regional macro-grid covering the entire Indian landmass to track regional pre-monsoon (May) nighttime thermal anomalies.
- **1 km × 1 km Municipal High-Resolution Grids**:
  - **Delhi NCT**: 575 zones (`DL0001`–`DL0575`)
  - **Pune, Maharashtra**: 414 zones (`P0001`–`P0414`)
  - **Nagpur, Maharashtra**: 229 zones (`C0001`–`C0229`)
  - **Expandable to Any Indian City**: Built-in Google Earth Engine ingestion pipeline (`pipeline/ingest/ingest_city.py`) pre-configured for Mumbai, Bengaluru, Ahmedabad, Hyderabad, Chennai, Kolkata, Jaipur, Lucknow, Aurangabad, and any OpenStreetMap-geocodable municipality in India.
- **110+ Indian Cities & District Directory**: Instant search and directory lookup for over 110 Indian cities and district headquarters, backed by live OpenStreetMap Nominatim geocoding for smaller towns and localities.

### 2. Four-Layer Thermal Analytics Engine
Users can switch seamlessly between four distinct thermal datasets on the map and in every city's analytical dossier:
1. **2024 Observed (`suhii_night`)**: Pre-monsoon (May) nighttime Surface Urban Heat Island Intensity measured by NASA MODIS (`MOD11A1`) relative to an elevation-matched rural reference ring.
2. **2024 Weather-Adjusted (`suhii_night_normalized`)**: Synoptic weather anomalies (wind, humidity, and bare-soil radiative bias from ERA5-Land) removed to isolate the structural heat island driven by concrete density and vegetation deficit.
3. **2031 BAU Projection (`suhii_night_2031`)**: Medium-term Business-As-Usual trajectory combining regional warming baselines (`+0.42 °C`) with local urban corridor densification.
4. **2041 BAU Projection (`suhii_night_2041`)**: Long-term trajectory combining regional warming (`+1.18 °C`) with compounding impervious surface expansion.

### 3. Plain-English Thermal Dossier, SHAP Attribution & Cooling Planner
- **Location Thermal Profile**: Displays nighttime SUHII excess (`°C` above rural baseline), daytime and nighttime absolute Land Surface Temperature (`LST`), severity classification, and 10 m land-cover composition bars (Built-up, Tree Canopy, Water Bodies, Cropland).
- **Physical Heat Driver Attribution**: Quantifies how impervious built-up surfaces, nighttime anthropogenic activity (VIIRS), surface albedo, tree canopy evapotranspiration, and water bodies push nighttime temperatures upward (`+°C`) or downward (`-°C`).
- **Interactive Cooling Intervention Planner**: Allows planners to simulate urban tree canopy expansion (`+%`), cool/reflective roof mandates (`+%`), and pervious/water restoration (`+%`) to estimate post-intervention cooling (`Δ°C`).
- **Automated Municipal Thermal Audit PDF**: One-click generation of print-ready PDF audit dossiers via WeasyPrint (`GET /api/v1/reports/{city_id}/pdf`).

---

## Satellite Data Sources & Physical Pipeline

All environmental metrics are extracted from Google Earth Engine (`earthengine-api`) using quality-bit masking and elevation-controlled rural baselines:

| Dataset | GEE Collection ID | Spatial Resolution | Extracted Variables |
| :--- | :--- | :--- | :--- |
| **NASA MODIS Terra LST** | `MODIS/061/MOD11A1` | 1 km (Daily) | `lst_day`, `lst_night`, `suhii_day`, `suhii_night` (QA bits 0–1 `<= 1`) |
| **ESA WorldCover** | `ESA/WorldCover/v200/2021` | 10 m | `frac_built`, `frac_tree`, `frac_water`, `frac_crop`, `frac_grass`, `frac_bare` |
| **Sentinel-2 SR** | `COPERNICUS/S2_SR_HARMONIZED` | 10 m – 20 m | `ndvi`, `ndbi`, `mndwi`, broadband `albedo` |
| **NASA SRTM DEM** | `USGS/SRTMGL1_003` | 30 m | Elevation matching (`±100 m` of urban mean) for rural baseline ring |
| **JRC GHSL Built-H** | `JRC/GHSL/P2023A/GHS_BUILT_H` | 100 m | `building_height_mean`, sky-view factor proxy (`svf_proxy`) |
| **NOAA VIIRS DNB** | `NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG` | 463 m | `night_lights_mean` (anthropogenic heat & activity proxy) |
| **ECMWF ERA5-Land** | `ECMWF/ERA5_LAND/MONTHLY_AGGR` | ~11 km | Synoptic temperature, wind speed, and relative humidity normalization |

---

## System Architecture

```text
chhaontest1/
├── config/
│   ├── cities.yaml                 # Pan-India + municipal city definitions, bboxes & climate zones
│   └── loader.py                   # Configuration loader & validator
├── pipeline/
│   └── ingest/
│       └── ingest_city.py          # Universal 7-step Google Earth Engine ingestion pipeline
├── scripts/
│   └── build_heatmaps.py           # Joins grid GeoJSONs with Parquet feature tables on cell_id
├── models/
│   ├── registry/                   # Trained LightGBM models, scalers & metadata
│   ├── explain/
│   │   └── shap_explainer.py       # Per-cell SHAP physical attribution engine
│   └── transfer_function/
│       └── scenario_engine.py      # Physics-constrained cooling scenario simulator
├── reports/
│   └── generator.py                # WeasyPrint + Jinja2 PDF thermal audit generator
├── api/
│   ├── main.py                     # FastAPI application entrypoint (Port 8000)
│   ├── routers/                    # REST endpoints: /spatial, /heat, /scenarios, /reports
│   ├── services/                   # Business logic & data services
│   └── schemas/                    # Pydantic v2 request/response contracts
├── data/
│   ├── boundaries/                 # City & national grid GeoJSONs (*_grid.geojson)
│   ├── tables/                     # Extracted satellite feature matrices (*_feature_matrix.parquet)
│   └── demo/                       # Enriched multi-layer GeoJSONs (*_heatmap*.geojson)
└── web/
    ├── public/demo/                # Static GeoJSON assets for instant edge/CDN delivery
    └── src/
        ├── app/page.tsx            # Dark-theme institutional GIS workspace & city dossier
        ├── components/map/         # MapLibre GL multi-layer thermal canvas (HeatMap.tsx)
        └── lib/indianCities.ts     # Gazetteer of 110+ Indian cities & district hubs


Core Engineering Principles
Zero Fabricated Data: Where satellite coverage is masked or unavailable, the pipeline and API return None / "No data" or an explicit HTTP status (404/501/503)—never a synthetic placeholder.
Strict cell_id Spatial Joins: All spatial grids (GeoJSON) and tabular feature matrices (Parquet) are joined exclusively on cell_id, never by row position.
Transparent Model Provenance: Cross-city transfers and business-as-usual projections explicitly surface their methodology and provenance metadata.
Quick Start (Local Development)
Prerequisites
Python 3.11 (recommended via uv or venv)
Node.js 18+ & npm
(Optional) Authenticated Google Earth Engine account (earthengine authenticate) for running new satellite ingestions
1. Clone & Set Up the Python Backend
Bash

git clone https://github.com/krrish021-ops/chhaontest1.git
cd chhaontest1

# Create and activate a Python 3.11 virtual environment
uv venv .venv --python 3.11
source .venv/bin/activate

# Install Python dependencies
uv pip install -r requirements.txt

# Start the FastAPI server on http://localhost:8000
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
Interactive API docs: http://localhost:8000/docs
2. Set Up & Start the Next.js GIS Frontend
Open a second terminal:

Bash

cd chhaontest1/web
npm install
npm run dev
Open http://localhost:3000 in your browser.
Ingesting a New Indian City from Google Earth Engine
To generate a 1 km × 1 km municipal analysis grid and extract 5-year pre-monsoon satellite features for any city in config/cities.yaml (e.g., mumbai, bengaluru, jaipur, bhopal, lucknow, hyderabad, chennai, kolkata):

Bash

source .venv/bin/activate

# Step 1: Build 1km municipal grid & extract satellite features from GEE
python -m pipeline.ingest.ingest_city jaipur --fast

# Step 2: Build observed, weather-adjusted, and forecast GeoJSON layers
python -m scripts.build_heatmaps jaipur
REST API Overview
Method	Endpoint	Description
GET	/api/v1/spatial/cities	List all configured jurisdictions, bounding boxes, and data availability
GET	/api/v1/heat/{city_id}/geojson	Fetch GeoJSON heatmap (layer=observed, normalized, or forecast)
GET	/api/v1/heat/{city_id}/rankings	Ranked list of thermal hotspot zones for a jurisdiction
GET	/api/v1/heat/{city_id}/cells/{cell_id}/shap	Per-cell SHAP physical feature attribution breakdown
POST	/api/v1/scenarios/{city_id}/simulate	Run physics-constrained cooling intervention simulation
GET	/api/v1/reports/{city_id}/pdf	Download municipal thermal audit PDF report

Deployment (Vercel + Cloud Backend)
Frontend (Vercel): Set the Root Directory to web. Static multi-layer GeoJSONs in web/public/demo/ ensure instant map rendering even before the backend wakes up. Set NEXT_PUBLIC_API_URL to your deployed FastAPI URL.
Backend (Render / Railway / Docker): Run uvicorn api.main:app --host 0.0.0.0 --port $PORT using Python 3.11.
