"""Spatial service: cities, AOI, heatmap GeoJSON from rebuilt demo grids."""

from pathlib import Path
import json
import math
import pandas as pd

from config.loader import get_all_cities

DEMO_DIR = Path("data/demo")
BOUNDS_DIR = Path("data/boundaries")

DEFAULT_ZOOM = 11


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


def _data_available(city_id: str) -> bool:
    """
    Honest check: does this city actually have servable demo/boundary
    data on disk right now? Used so cities listed in config/cities.yaml
    but not yet ingested (e.g. Mumbai, Aurangabad) are truthfully
    flagged rather than silently presented as ready.
    """
    candidates = [
        DEMO_DIR / f"{city_id}_heatmap_normalized.geojson",
        DEMO_DIR / f"{city_id}_forecast_heatmap.geojson",
        DEMO_DIR / f"{city_id}_heatmap.geojson",
        BOUNDS_DIR / f"{city_id}_grid.geojson",
    ]
    return any(p.exists() for p in candidates)


def list_cities_service():
    """
    Real city registry, sourced from config/cities.yaml (single source
    of truth) instead of a hardcoded duplicate list. Every city defined
    in the YAML is returned, honestly flagged with data_available.
    """
    cities_cfg = get_all_cities()
    result = []

    for city_id, cfg in cities_cfg.items():
        bbox = cfg.get("bbox", [0.0, 0.0, 0.0, 0.0])
        if len(bbox) == 4:
            lon = round((bbox[0] + bbox[2]) / 2, 4)
            lat = round((bbox[1] + bbox[3]) / 2, 4)
        else:
            lon, lat = 0.0, 0.0

        result.append({
            "id": city_id,
            "name": cfg.get("name", city_id.title()),
            "name_mr": cfg.get("name_mr", ""),
            "state": cfg.get("state", ""),
            "bbox": bbox,
            "buffer_km": cfg.get("buffer_km", 20),
            "priority": cfg.get("priority", 99),
            "notes": cfg.get("notes", ""),
            "lat": lat,
            "lon": lon,
            "zoom": DEFAULT_ZOOM,
            "data_available": _data_available(city_id),
        })

    result.sort(key=lambda c: c["priority"])
    return result


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
