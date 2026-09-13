"""Spatial service: cities, AOI, heatmap GeoJSON from rebuilt demo grids."""

from pathlib import Path
import json
import math
import pandas as pd

DEMO_DIR = Path("data/demo")
BOUNDS_DIR = Path("data/boundaries")

CITIES_REGISTRY = [
    {
        "id": "nagpur",
        "name": "Nagpur",
        "state": "Maharashtra",
        "lat": 21.1458,
        "lon": 79.0888,
        "zoom": 11,
        "description": "Pilot city — Vidarbha region peak heat hotspot",
    },
    {
        "id": "pune",
        "name": "Pune",
        "state": "Maharashtra",
        "lat": 18.5204,
        "lon": 73.8567,
        "zoom": 11,
        "description": "Rapidly sprawling IT & manufacturing hub",
    },
]


def safe_float(val, default=0.0):
    if val is None:
        return default
    try:
        if isinstance(val, float) and math.isnan(val):
            return default
        if pd.isna(val):
            return default
    except Exception:
        pass
    try:
        return float(val)
    except Exception:
        return default


def list_cities_service():
    return CITIES_REGISTRY


def get_city_aoi_service(city_id="nagpur"):
    city = city_id.lower()
    for p in [BOUNDS_DIR / f"{city}_boundary.geojson", BOUNDS_DIR / f"{city}_grid.geojson"]:
        if p.exists():
            return json.loads(p.read_text())
    raise FileNotFoundError(f"Boundary not found for {city}")


def get_heatmap_geojson_service(city_id="nagpur"):
    city = city_id.lower()
    file_path = None
    for p in [
        DEMO_DIR / f"{city}_heatmap_normalized.geojson",
        DEMO_DIR / f"{city}_forecast_heatmap.geojson",
        DEMO_DIR / f"{city}_heatmap.geojson",
        BOUNDS_DIR / f"{city}_grid.geojson",
    ]:
        if p.exists():
            file_path = p
            break
    if file_path is None:
        raise FileNotFoundError(f"No heatmap/grid GeoJSON for {city}")

    geojson = json.loads(file_path.read_text())
    feats = geojson.get("features", [])
    if len(feats) < 2:
        # hard fail signal: still a giant polygon
        raise ValueError(
            f"{file_path} has only {len(feats)} feature(s). Run: python -m scripts.rebuild_city_grids"
        )

    for feat in feats:
        props = feat.get("properties", {}) or {}
        suhii = safe_float(props.get("suhii_night_normalized", props.get("suhii_night")), 1.92)
        props["suhii_night"] = suhii
        props["suhii_night_normalized"] = suhii
        props["suhii_night_ml"] = safe_float(props.get("suhii_night_ml"), suhii)
        props["suhii_night_2031"] = safe_float(props.get("suhii_night_2031"), round(suhii + 0.42, 2))
        props["suhii_night_2041"] = safe_float(props.get("suhii_night_2041"), round(suhii + 1.18, 2))
        props["lst_day"] = safe_float(props.get("lst_day"), 38.2)
        props["lst_night"] = safe_float(props.get("lst_night"), 28.4)
        props["frac_built"] = safe_float(props.get("frac_built"), 0.55)
        props["frac_tree"] = safe_float(props.get("frac_tree"), 0.12)
        if "cell_id" not in props:
            props["cell_id"] = "UNKNOWN"
        feat["properties"] = props

    geojson["features"] = feats
    return geojson
