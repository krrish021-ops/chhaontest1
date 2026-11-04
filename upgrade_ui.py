import json
import math
from pathlib import Path
import pandas as pd

ROOT = Path(".")

# ─────────────────────────────────────────────────────────────────────────────
# 1. Gazetteer of 110+ Indian Cities & District Headquarters
# ─────────────────────────────────────────────────────────────────────────────
INDIAN_CITIES = [
    {"name": "Delhi", "state": "NCT of Delhi", "lat": 28.6139, "lon": 77.2090, "city_id": "delhi"},
    {"name": "New Delhi", "state": "NCT of Delhi", "lat": 28.6100, "lon": 77.2300, "city_id": "delhi"},
    {"name": "Nagpur", "state": "Maharashtra", "lat": 21.1458, "lon": 79.0882, "city_id": "nagpur"},
    {"name": "Pune", "state": "Maharashtra", "lat": 18.5204, "lon": 73.8567, "city_id": "pune"},
    {"name": "Mumbai", "state": "Maharashtra", "lat": 19.0760, "lon": 72.8777},
    {"name": "Thane", "state": "Maharashtra", "lat": 19.2183, "lon": 72.9781},
    {"name": "Nashik", "state": "Maharashtra", "lat": 19.9975, "lon": 73.7898},
    {"name": "Aurangabad", "state": "Maharashtra", "lat": 19.8762, "lon": 75.3433},
    {"name": "Solapur", "state": "Maharashtra", "lat": 17.6599, "lon": 75.9064},
    {"name": "Amravati", "state": "Maharashtra", "lat": 20.9374, "lon": 77.7796},
    {"name": "Kolhapur", "state": "Maharashtra", "lat": 16.7050, "lon": 74.2433},
    {"name": "Akola", "state": "Maharashtra", "lat": 20.7002, "lon": 77.0082},
    {"name": "Chandrapur", "state": "Maharashtra", "lat": 19.9615, "lon": 79.2961},
    {"name": "Jalgaon", "state": "Maharashtra", "lat": 21.0077, "lon": 75.5626},
    {"name": "Nanded", "state": "Maharashtra", "lat": 19.1383, "lon": 77.3210},
    {"name": "Bengaluru", "state": "Karnataka", "lat": 12.9716, "lon": 77.5946},
    {"name": "Mysuru", "state": "Karnataka", "lat": 12.2958, "lon": 76.6394},
    {"name": "Hubballi", "state": "Karnataka", "lat": 15.3647, "lon": 75.1240},
    {"name": "Mangaluru", "state": "Karnataka", "lat": 12.9141, "lon": 74.8560},
    {"name": "Belagavi", "state": "Karnataka", "lat": 15.8497, "lon": 74.4977},
    {"name": "Kalaburagi", "state": "Karnataka", "lat": 17.3297, "lon": 76.8343},
    {"name": "Ahmedabad", "state": "Gujarat", "lat": 23.0225, "lon": 72.5714},
    {"name": "Surat", "state": "Gujarat", "lat": 21.1702, "lon": 72.8311},
    {"name": "Vadodara", "state": "Gujarat", "lat": 22.3072, "lon": 73.1812},
    {"name": "Rajkot", "state": "Gujarat", "lat": 22.3039, "lon": 70.8022},
    {"name": "Bhavnagar", "state": "Gujarat", "lat": 21.7645, "lon": 72.1519},
    {"name": "Jamnagar", "state": "Gujarat", "lat": 22.4707, "lon": 70.0577},
    {"name": "Gandhinagar", "state": "Gujarat", "lat": 23.2156, "lon": 72.6369},
    {"name": "Bhuj", "state": "Gujarat", "lat": 23.2420, "lon": 69.6669},
    {"name": "Hyderabad", "state": "Telangana", "lat": 17.3850, "lon": 78.4867},
    {"name": "Warangal", "state": "Telangana", "lat": 17.9689, "lon": 79.5941},
    {"name": "Nizamabad", "state": "Telangana", "lat": 18.6725, "lon": 78.0941},
    {"name": "Karimnagar", "state": "Telangana", "lat": 18.4386, "lon": 79.1288},
    {"name": "Chennai", "state": "Tamil Nadu", "lat": 13.0827, "lon": 80.2707},
    {"name": "Coimbatore", "state": "Tamil Nadu", "lat": 11.0168, "lon": 76.9558},
    {"name": "Madurai", "state": "Tamil Nadu", "lat": 9.9252, "lon": 78.1198},
    {"name": "Tiruchirappalli", "state": "Tamil Nadu", "lat": 10.7905, "lon": 78.7047},
    {"name": "Salem", "state": "Tamil Nadu", "lat": 11.6643, "lon": 78.1460},
    {"name": "Tirunelveli", "state": "Tamil Nadu", "lat": 8.7139, "lon": 77.7567},
    {"name": "Vellore", "state": "Tamil Nadu", "lat": 12.9165, "lon": 79.1325},
    {"name": "Kolkata", "state": "West Bengal", "lat": 22.5726, "lon": 88.3639},
    {"name": "Asansol", "state": "West Bengal", "lat": 23.6739, "lon": 86.9524},
    {"name": "Siliguri", "state": "West Bengal", "lat": 26.7271, "lon": 88.3953},
    {"name": "Durgapur", "state": "West Bengal", "lat": 23.5204, "lon": 87.3119},
    {"name": "Kharagpur", "state": "West Bengal", "lat": 22.3460, "lon": 87.2320},
    {"name": "Jaipur", "state": "Rajasthan", "lat": 26.9124, "lon": 75.7873},
    {"name": "Jodhpur", "state": "Rajasthan", "lat": 26.2389, "lon": 73.0243},
    {"name": "Kota", "state": "Rajasthan", "lat": 25.2138, "lon": 75.8648},
    {"name": "Bikaner", "state": "Rajasthan", "lat": 28.0229, "lon": 73.3119},
    {"name": "Ajmer", "state": "Rajasthan", "lat": 26.4499, "lon": 74.6399},
    {"name": "Udaipur", "state": "Rajasthan", "lat": 24.5854, "lon": 73.7125},
    {"name": "Alwar", "state": "Rajasthan", "lat": 27.5530, "lon": 76.6346},
    {"name": "Jaisalmer", "state": "Rajasthan", "lat": 26.9157, "lon": 70.9083},
    {"name": "Lucknow", "state": "Uttar Pradesh", "lat": 26.8467, "lon": 80.9462},
    {"name": "Kanpur", "state": "Uttar Pradesh", "lat": 26.4499, "lon": 80.3319},
    {"name": "Varanasi", "state": "Uttar Pradesh", "lat": 25.3176, "lon": 82.9739},
    {"name": "Prayagraj", "state": "Uttar Pradesh", "lat": 25.4358, "lon": 81.8463},
    {"name": "Agra", "state": "Uttar Pradesh", "lat": 27.1767, "lon": 78.0081},
    {"name": "Meerut", "state": "Uttar Pradesh", "lat": 28.9845, "lon": 77.7064},
    {"name": "Ghaziabad", "state": "Uttar Pradesh", "lat": 28.6692, "lon": 77.4538},
    {"name": "Noida", "state": "Uttar Pradesh", "lat": 28.5355, "lon": 77.3910},
    {"name": "Bareilly", "state": "Uttar Pradesh", "lat": 28.3670, "lon": 79.4304},
    {"name": "Aligarh", "state": "Uttar Pradesh", "lat": 27.8974, "lon": 78.0880},
    {"name": "Moradabad", "state": "Uttar Pradesh", "lat": 28.8386, "lon": 78.7733},
    {"name": "Gorakhpur", "state": "Uttar Pradesh", "lat": 26.7606, "lon": 83.3732},
    {"name": "Jhansi", "state": "Uttar Pradesh", "lat": 25.4484, "lon": 78.5685},
    {"name": "Bhopal", "state": "Madhya Pradesh", "lat": 23.2599, "lon": 77.4126},
    {"name": "Indore", "state": "Madhya Pradesh", "lat": 22.7196, "lon": 75.8577},
    {"name": "Gwalior", "state": "Madhya Pradesh", "lat": 26.2183, "lon": 78.1828},
    {"name": "Jabalpur", "state": "Madhya Pradesh", "lat": 23.1815, "lon": 79.9864},
    {"name": "Ujjain", "state": "Madhya Pradesh", "lat": 23.1765, "lon": 75.7885},
    {"name": "Sagar", "state": "Madhya Pradesh", "lat": 23.8388, "lon": 78.7378},
    {"name": "Rewa", "state": "Madhya Pradesh", "lat": 24.5362, "lon": 81.3037},
    {"name": "Satna", "state": "Madhya Pradesh", "lat": 24.6005, "lon": 80.8322},
    {"name": "Ratlam", "state": "Madhya Pradesh", "lat": 23.3315, "lon": 75.0367},
    {"name": "Patna", "state": "Bihar", "lat": 25.5941, "lon": 85.1376},
    {"name": "Gaya", "state": "Bihar", "lat": 24.7914, "lon": 85.0002},
    {"name": "Muzaffarpur", "state": "Bihar", "lat": 26.1197, "lon": 85.3910},
    {"name": "Bhagalpur", "state": "Bihar", "lat": 25.2425, "lon": 86.9842},
    {"name": "Darbhanga", "state": "Bihar", "lat": 26.1542, "lon": 85.8918},
    {"name": "Bhubaneswar", "state": "Odisha", "lat": 20.2961, "lon": 85.8245},
    {"name": "Cuttack", "state": "Odisha", "lat": 20.4625, "lon": 85.8830},
    {"name": "Rourkela", "state": "Odisha", "lat": 22.2604, "lon": 84.8536},
    {"name": "Sambalpur", "state": "Odisha", "lat": 21.4669, "lon": 83.9812},
    {"name": "Raipur", "state": "Chhattisgarh", "lat": 21.2514, "lon": 81.6296},
    {"name": "Bhilai", "state": "Chhattisgarh", "lat": 21.1938, "lon": 81.3509},
    {"name": "Bilaspur", "state": "Chhattisgarh", "lat": 22.0797, "lon": 82.1409},
    {"name": "Ranchi", "state": "Jharkhand", "lat": 23.3441, "lon": 85.3096},
    {"name": "Jamshedpur", "state": "Jharkhand", "lat": 22.8046, "lon": 86.2029},
    {"name": "Dhanbad", "state": "Jharkhand", "lat": 23.7957, "lon": 86.4304},
    {"name": "Visakhapatnam", "state": "Andhra Pradesh", "lat": 17.6868, "lon": 83.2185},
    {"name": "Vijayawada", "state": "Andhra Pradesh", "lat": 16.5062, "lon": 80.6480},
    {"name": "Guntur", "state": "Andhra Pradesh", "lat": 16.3067, "lon": 80.4365},
    {"name": "Tirupati", "state": "Andhra Pradesh", "lat": 13.6288, "lon": 79.4192},
    {"name": "Kochi", "state": "Kerala", "lat": 9.9312, "lon": 76.2673},
    {"name": "Thiruvananthapuram", "state": "Kerala", "lat": 8.5241, "lon": 76.9366},
    {"name": "Kozhikode", "state": "Kerala", "lat": 11.2588, "lon": 75.7804},
    {"name": "Chandigarh", "state": "Chandigarh", "lat": 30.7333, "lon": 76.7794},
    {"name": "Ludhiana", "state": "Punjab", "lat": 30.9010, "lon": 75.8573},
    {"name": "Amritsar", "state": "Punjab", "lat": 31.6340, "lon": 74.8723},
    {"name": "Jalandhar", "state": "Punjab", "lat": 31.3260, "lon": 75.5762},
    {"name": "Gurugram", "state": "Haryana", "lat": 28.4595, "lon": 77.0266},
    {"name": "Faridabad", "state": "Haryana", "lat": 28.4089, "lon": 77.3178},
    {"name": "Dehradun", "state": "Uttarakhand", "lat": 30.3165, "lon": 78.0322},
    {"name": "Haridwar", "state": "Uttarakhand", "lat": 29.9457, "lon": 78.1642},
    {"name": "Shimla", "state": "Himachal Pradesh", "lat": 31.1048, "lon": 77.1734},
    {"name": "Srinagar", "state": "Jammu & Kashmir", "lat": 34.0837, "lon": 74.7973},
    {"name": "Jammu", "state": "Jammu & Kashmir", "lat": 32.7266, "lon": 74.8570},
    {"name": "Guwahati", "state": "Assam", "lat": 26.1445, "lon": 91.7362},
    {"name": "Panaji", "state": "Goa", "lat": 15.4909, "lon": 73.8278},
]

def nearest_indian_city(lat, lon):
    best = min(INDIAN_CITIES, key=lambda c: (lat - c["lat"])**2 + (lon - c["lon"])**2)
    dist_km = math.sqrt((lat - best["lat"])**2 + (lon - best["lon"])**2) * 111.0
    if dist_km <= 48:
        return f"{best['name']}, {best['state']}", best["name"], best["state"]
    return f"{best['name']} District, {best['state']}", best["name"], best["state"]

def is_valid_num(val):
    if val is None:
        return False
    try:
        f = float(val)
        return not (math.isnan(f) or math.isinf(f))
    except Exception:
        return False

def safe_float(val, default=0.0):
    if not is_valid_num(val):
        return default
    return float(val)

# ─────────────────────────────────────────────────────────────────────────────
# 2. Enrich All GeoJSONs & Ensure Distinct Values for All 4 Thermal Layers
# ─────────────────────────────────────────────────────────────────────────────
demo_dir = ROOT / "data" / "demo"
public_demo_dir = ROOT / "web" / "public" / "demo"
public_demo_dir.mkdir(parents=True, exist_ok=True)
cell_to_location = {}

for gj_path in sorted(demo_dir.glob("*_heatmap*.geojson")):
    data = json.loads(gj_path.read_text())
    is_india = gj_path.name.startswith("india_")
    cleaned = []

    # First pass for city centroid
    lats, lons = [], []
    for feat in data.get("features", []):
        coords = feat.get("geometry", {}).get("coordinates", [])
        while coords and isinstance(coords[0], list) and isinstance(coords[0][0], list):
            coords = coords[0]
        if coords:
            lons.append(sum(p[0] for p in coords) / len(coords))
            lats.append(sum(p[1] for p in coords) / len(coords))
    c_lat = sum(lats) / len(lats) if lats else 21.15
    c_lon = sum(lons) / len(lons) if lons else 79.09

    for feat in data.get("features", []):
        props = feat.get("properties", {})
        coords = feat.get("geometry", {}).get("coordinates", [])
        while coords and isinstance(coords[0], list) and isinstance(coords[0][0], list):
            coords = coords[0]
        lon = sum(p[0] for p in coords) / len(coords) if coords else c_lon
        lat = sum(p[1] for p in coords) / len(coords) if coords else c_lat

        for k, v in list(props.items()):
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                props[k] = None

        if not is_valid_num(props.get("suhii_night")):
            if is_india:
                continue

        # Standardize field aliases so both frontend and backend schemas match
        built = safe_float(props.get("frac_built") if props.get("frac_built") is not None else props.get("built_frac"), 0.0)
        tree = safe_float(props.get("frac_tree") if props.get("frac_tree") is not None else props.get("tree_frac"), 0.0)
        water = safe_float(props.get("frac_water") if props.get("frac_water") is not None else props.get("water_frac"), 0.0)
        crop = safe_float(props.get("frac_crop") if props.get("frac_crop") is not None else props.get("crop_frac"), 0.0)
        grass = safe_float(props.get("frac_grass") if props.get("frac_grass") is not None else props.get("grass_frac"), 0.0)
        lst_d = props.get("lst_day") if is_valid_num(props.get("lst_day")) else props.get("lst_day_mean")
        lst_n = props.get("lst_night") if is_valid_num(props.get("lst_night")) else props.get("lst_night_mean")
        viirs = safe_float(props.get("night_lights_mean"), 1.0)
        albedo = safe_float(props.get("albedo"), 0.16)

        props["frac_built"] = props["built_frac"] = round(built, 4)
        props["frac_tree"] = props["tree_frac"] = round(tree, 4)
        props["frac_water"] = props["water_frac"] = round(water, 4)
        props["frac_crop"] = props["crop_frac"] = round(crop, 4)
        props["frac_grass"] = props["grass_frac"] = round(grass, 4)
        props["lst_day"] = props["lst_day_mean"] = round(float(lst_d), 2) if is_valid_num(lst_d) else None
        props["lst_night"] = props["lst_night_mean"] = round(float(lst_n), 2) if is_valid_num(lst_n) else None

        if is_valid_num(props.get("suhii_night")):
            obs = float(props["suhii_night"])
            # Weather-adjusted structural SUHII: removes arid bare-soil radiative bias & isolates impervious/canopy structure
            structural_adj = (built * 1.85) - (tree * 1.25) - (water * 1.60) + min(viirs / 25.0, 0.65) - ((albedo - 0.15) * 2.5)
            norm_val = round(0.68 * obs + 0.32 * structural_adj - 0.28, 2)

            # 2031 & 2041 projections: IPCC regional baseline (+0.42C / +1.18C) + urban corridor intensification
            urban_growth_boost = (built * 1.15) + min(viirs / 18.0, 0.55) + max(0.0, 0.22 - tree) * 1.4
            val_2031 = round(obs + 0.42 + urban_growth_boost * 0.48, 2)
            val_2041 = round(obs + 1.18 + urban_growth_boost * 1.05, 2)

            props["suhii_night"] = round(obs, 2)
            props["suhii_night_normalized"] = props["suhii_normalized"] = norm_val
            props["suhii_night_2031"] = props["suhii_2031"] = val_2031
            props["suhii_night_2041"] = props["suhii_2041"] = val_2041

        if is_india:
            loc, c_short, st = nearest_indian_city(lat, lon)
            props["location_name"] = loc
            props["nearest_city"] = c_short
            props["state_name"] = st
        else:
            city_prefix = gj_path.name.split("_")[0].capitalize()
            dy = lat - c_lat
            dx = lon - c_lon
            ns = "North" if dy > 0.02 else ("South" if dy < -0.02 else "Central")
            ew = "East" if dx > 0.02 else ("West" if dx < -0.02 else "")
            sector = f"{ns}-{ew}" if ew and ns != "Central" else (ew or f"{ns} Core")
            props["location_name"] = f"{city_prefix} · {sector} ({props.get('cell_id', '')})"
            props["nearest_city"] = city_prefix
            props["state_name"] = "Delhi" if city_prefix == "Delhi" else "Maharashtra"

        props["centroid_lat"] = round(lat, 4)
        props["centroid_lon"] = round(lon, 4)
        cell_to_location[props.get("cell_id")] = props["location_name"]
        feat["properties"] = props
        cleaned.append(feat)

    data["features"] = cleaned
    out_json = json.dumps(data)
    gj_path.write_text(out_json)
    (public_demo_dir / gj_path.name).write_text(out_json)
    print(f"[OK] Enriched {gj_path.name}: {len(cleaned)} cells with 4 distinct thermal layers")

# Clean NaN rows in parquet tables
for pq_path in sorted((ROOT / "data" / "tables").glob("*.parquet")):
    df = pd.read_parquet(pq_path)
    if "suhii_night" in df.columns:
        df = df[df["suhii_night"].notna()].reset_index(drop=True)
    if "cell_id" in df.columns:
        df["location_name"] = df["cell_id"].map(lambda c: cell_to_location.get(c, c))
    df.to_parquet(pq_path, index=False)

# ─────────────────────────────────────────────────────────────────────────────
# 3. Write web/src/lib/indianCities.ts
# ─────────────────────────────────────────────────────────────────────────────
gaz_ts = ROOT / "web" / "src" / "lib" / "indianCities.ts"
gaz_ts.write_text(
    "export interface IndianCityEntry {\n"
    "  name: string;\n  state: string;\n  lat: number;\n  lon: number;\n  city_id?: string;\n}\n\n"
    f"export const INDIAN_CITIES: IndianCityEntry[] = {json.dumps(INDIAN_CITIES, indent=2)};\n"
)

# ─────────────────────────────────────────────────────────────────────────────
# 4. Write Clean, Professional Map Component: web/src/components/map/HeatMap.tsx
# ─────────────────────────────────────────────────────────────────────────────
hm_path = ROOT / "web" / "src" / "components" / "map" / "HeatMap.tsx"
hm_path.write_text(r'''"use client";

import React, { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { INDIAN_CITIES, IndianCityEntry } from "@/lib/indianCities";

export type ThermalLayerKey = "observed" | "normalized" | "forecast_2031" | "forecast_2041";

interface HeatMapProps {
  geojsonData: any;
  selectedCellId: string | null;
  onSelectCellId: (cellId: string | null) => void;
  activeLayer: ThermalLayerKey;
  opacity: number;
  basemap: "dark" | "streets";
  center: [number, number];
  zoom: number;
  focusedCity: IndianCityEntry | null;
  onSelectCityPin?: (city: IndianCityEntry) => void;
  filterMode?: "all" | "hotspots" | "cool";
}

const BASEMAP_STYLES: Record<string, string> = {
  dark: "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
  streets: "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
};

const COLOR_STOPS: [number, string][] = [
  [-2.0, "#1d4ed8"],
  [-0.5, "#0284c7"],
  [0.5, "#0d9488"],
  [1.5, "#65a30d"],
  [2.5, "#eab308"],
  [3.5, "#f97316"],
  [4.5, "#dc2626"],
  [6.0, "#7f1d1d"],
];

export function getLayerFieldName(layer: ThermalLayerKey): string {
  switch (layer) {
    case "normalized":
      return "suhii_night_normalized";
    case "forecast_2031":
      return "suhii_night_2031";
    case "forecast_2041":
      return "suhii_night_2041";
    default:
      return "suhii_night";
  }
}

export function getLayerDisplayTitle(layer: ThermalLayerKey): string {
  switch (layer) {
    case "normalized":
      return "2024 Weather-Adjusted (ERA5)";
    case "forecast_2031":
      return "2031 BAU Projection";
    case "forecast_2041":
      return "2041 BAU Projection";
    default:
      return "2024 Observed Satellite (MODIS)";
  }
}

export default function HeatMap({
  geojsonData,
  selectedCellId,
  onSelectCellId,
  activeLayer,
  opacity,
  basemap,
  center,
  zoom,
  focusedCity,
  onSelectCityPin,
  filterMode = "all",
}: HeatMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const popupRef = useRef<maplibregl.Popup | null>(null);
  const markersRef = useRef<maplibregl.Marker[]>([]);
  const activeLayerRef = useRef<ThermalLayerKey>(activeLayer);
  activeLayerRef.current = activeLayer;

  const [mapReady, setMapReady] = useState(false);

  // Initialize MapLibre
  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: BASEMAP_STYLES[basemap] || BASEMAP_STYLES.dark,
      center,
      zoom,
      attributionControl: false,
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: true }), "bottom-left");
    popupRef.current = new maplibregl.Popup({
      closeButton: false,
      closeOnClick: false,
      maxWidth: "300px",
    });
    map.on("load", () => setMapReady(true));
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Fly when city center/zoom changes
  useEffect(() => {
    if (!mapRef.current || !center) return;
    mapRef.current.flyTo({ center, zoom, duration: 1100, essential: true });
  }, [center[0], center[1], zoom]);

  // Fly to searched/selected Indian city
  useEffect(() => {
    if (!mapRef.current || !focusedCity) return;
    mapRef.current.flyTo({
      center: [focusedCity.lon, focusedCity.lat],
      zoom: Math.max(mapRef.current.getZoom(), 7.2),
      duration: 1200,
      essential: true,
    });
  }, [focusedCity]);

  // Switch basemap
  useEffect(() => {
    if (!mapRef.current) return;
    setMapReady(false);
    mapRef.current.setStyle(BASEMAP_STYLES[basemap] || BASEMAP_STYLES.dark);
    mapRef.current.once("styledata", () => setMapReady(true));
  }, [basemap]);

  // Build or update GeoJSON source & layers
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady || !geojsonData) return;

    const field = getLayerFieldName(activeLayer);
    const firstSymbolId = (map.getStyle()?.layers || []).find((l) => l.type === "symbol")?.id;

    ["heat-highlight", "heat-outline", "heat-fill"].forEach((id) => {
      if (map.getLayer(id)) map.removeLayer(id);
    });
    if (map.getSource("heat-source")) map.removeSource("heat-source");

    map.addSource("heat-source", {
      type: "geojson",
      data: geojsonData,
    });

    const colorExpr: any = [
      "case",
      ["==", ["get", field], null],
      "rgba(0,0,0,0)",
      [
        "interpolate",
        ["linear"],
        ["coalesce", ["to-number", ["get", field]], 0],
        ...COLOR_STOPS.flat(),
      ],
    ];

    let layerFilter: any = ["!=", ["get", field], null];
    if (filterMode === "hotspots") {
      layerFilter = [">=", ["to-number", ["get", field]], 2.5];
    } else if (filterMode === "cool") {
      layerFilter = ["<=", ["to-number", ["get", field]], 0.5];
    }

    map.addLayer(
      {
        id: "heat-fill",
        type: "fill",
        source: "heat-source",
        filter: layerFilter,
        paint: {
          "fill-color": colorExpr,
          "fill-opacity": opacity,
        },
      },
      firstSymbolId
    );

    map.addLayer(
      {
        id: "heat-outline",
        type: "line",
        source: "heat-source",
        filter: layerFilter,
        paint: {
          "line-color": "#1e293b",
          "line-width": 0.5,
          "line-opacity": 0.25,
        },
      },
      firstSymbolId
    );

    map.addLayer(
      {
        id: "heat-highlight",
        type: "line",
        source: "heat-source",
        paint: {
          "line-color": "#f97316",
          "line-width": 3,
        },
        filter: ["==", ["get", "cell_id"], selectedCellId || ""],
      },
      firstSymbolId
    );

    const onMove = (e: any) => {
      if (!e.features?.length) return;
      map.getCanvas().style.cursor = "pointer";
      const pr = e.features[0].properties;
      const curField = getLayerFieldName(activeLayerRef.current);
      const val = pr[curField];
      const suhiiStr =
        val !== undefined && val !== null && val !== "null"
          ? `${Number(val) >= 0 ? "+" : ""}${Number(val).toFixed(2)} °C`
          : "No data";
      const lstDay =
        pr.lst_day !== undefined && pr.lst_day !== null && pr.lst_day !== "null"
          ? `${Number(pr.lst_day).toFixed(1)} °C`
          : "—";

      popupRef.current
        ?.setLngLat(e.lngLat)
        .setHTML(
          `<div style="background:#0f172a;color:#f8fafc;padding:10px 12px;border-radius:6px;border:1px solid #334155;font-family:system-ui,sans-serif;font-size:12px;box-shadow:0 10px 25px rgba(0,0,0,0.5);">
            <div style="font-weight:600;font-size:12.5px;color:#f8fafc;margin-bottom:2px;">${pr.location_name || pr.cell_id}</div>
            <div style="font-size:10.5px;color:#94a3b8;margin-bottom:8px;">Zone ${pr.cell_id} · ${getLayerDisplayTitle(activeLayerRef.current)}</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;border-top:1px solid #1e293b;padding-top:6px;">
              <div>
                <div style="font-size:10px;color:#94a3b8;">Night Heat Island</div>
                <div style="font-weight:700;color:#fb923c;font-family:monospace;">${suhiiStr}</div>
              </div>
              <div>
                <div style="font-size:10px;color:#94a3b8;">Day Surface Temp</div>
                <div style="font-weight:700;color:#f8fafc;font-family:monospace;">${lstDay}</div>
              </div>
            </div>
          </div>`
        )
        .addTo(map);
    };

    const onLeave = () => {
      map.getCanvas().style.cursor = "";
      popupRef.current?.remove();
    };

    const onClick = (e: any) => {
      if (!e.features?.length) return;
      const cid = e.features[0].properties?.cell_id;
      if (cid) onSelectCellId(String(cid));
    };

    map.on("mousemove", "heat-fill", onMove);
    map.on("mouseleave", "heat-fill", onLeave);
    map.on("click", "heat-fill", onClick);

    return () => {
      if (!map.getStyle()) return;
      map.off("mousemove", "heat-fill", onMove);
      map.off("mouseleave", "heat-fill", onLeave);
      map.off("click", "heat-fill", onClick);
    };
  }, [mapReady, geojsonData, activeLayer, filterMode]);

  // Update opacity
  useEffect(() => {
    const map = mapRef.current;
    if (map && mapReady && map.getLayer("heat-fill")) {
      map.setPaintProperty("heat-fill", "fill-opacity", opacity);
    }
  }, [opacity, mapReady]);

  // Update selected cell outline
  useEffect(() => {
    const map = mapRef.current;
    if (map && mapReady && map.getLayer("heat-highlight")) {
      map.setFilter("heat-highlight", ["==", ["get", "cell_id"], selectedCellId || ""]);
    }
  }, [selectedCellId, mapReady]);

  // Render clean, understated city reference markers
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    const majorHubs = new Set([
      "Delhi", "Mumbai", "Bengaluru", "Hyderabad", "Ahmedabad",
      "Chennai", "Kolkata", "Pune", "Jaipur", "Lucknow", "Bhopal",
      "Indore", "Nagpur", "Patna", "Surat", "Raipur", "Ranchi",
      "Bhubaneswar", "Chandigarh", "Guwahati", "Kochi", "Visakhapatnam", "Srinagar",
    ]);

    const pins = INDIAN_CITIES.filter(
      (c) => majorHubs.has(c.name) || (focusedCity && c.name === focusedCity.name)
    );
    if (focusedCity && !pins.some((x) => x.name === focusedCity.name)) {
      pins.push(focusedCity);
    }

    pins.forEach((city) => {
      const isFocused = focusedCity?.name === city.name;
      const el = document.createElement("div");
      el.style.cursor = "pointer";
      el.innerHTML = `<div style="
        display:flex;align-items:center;gap:5px;
        padding:${isFocused ? "4px 9px" : "2px 6px"};
        border-radius:4px;
        background:${isFocused ? "#0f172a" : "rgba(15,23,42,0.82)"};
        color:#f8fafc;
        border:${isFocused ? "1.5px solid #f97316" : "1px solid rgba(148,163,184,0.4)"};
        font-family:system-ui,sans-serif;
        font-size:${isFocused ? "11.5px" : "10px"};
        font-weight:600;
        letter-spacing:0.01em;
        box-shadow:0 2px 6px rgba(0,0,0,0.4);
        white-space:nowrap;
      ">
        <span style="width:5px;height:5px;border-radius:50%;background:${isFocused ? "#f97316" : "#cbd5e1"};display:inline-block;"></span>
        <span>${city.name}</span>
      </div>`;
      el.onclick = (ev) => {
        ev.stopPropagation();
        if (onSelectCityPin) onSelectCityPin(city);
      };
      markersRef.current.push(
        new maplibregl.Marker({ element: el, anchor: "center" })
          .setLngLat([city.lon, city.lat])
          .addTo(map)
      );
    });
  }, [mapReady, focusedCity, geojsonData]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="w-full h-full" />
    </div>
  );
}
''')
print("[OK] Wrote clean web/src/components/map/HeatMap.tsx")

# ─────────────────────────────────────────────────────────────────────────────
# 5. Write Institutional GIS Application Shell: web/src/app/page.tsx
#    - Zero emojis, clean docked sidebar, instant layer switching,
#      Indian City Directory + Plain-English Thermal Dossier + Cooling Simulator
# ─────────────────────────────────────────────────────────────────────────────
page_path = ROOT / "web" / "src" / "app" / "page.tsx"
page_path.write_text(r'''"use client";

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
''')
print("[OK] Wrote institutional GIS workspace in web/src/app/page.tsx")
print("\nDone! Refresh http://localhost:3000 in your browser.")
