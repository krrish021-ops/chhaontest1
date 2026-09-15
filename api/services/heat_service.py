"""Heat service: rankings + SHAP explanations. Prefers rebuilt heatmap GeoJSON."""

from pathlib import Path
import json
import math
import pandas as pd

from models.explain import shap_explainer as _shap

TABLES_DIR = Path("data/tables")
DEMO_DIR   = Path("data/demo")
BOUNDS_DIR = Path("data/boundaries")


def safe_float(val, default=None):
    """
    Convert val to float. Returns default (None) instead of inventing
    a plausible-looking number. Callers must handle None explicitly.
    """
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


def _centroid_lon_lat(geometry: dict):
    """Compute a simple centroid (avg of vertices) from a GeoJSON geometry."""
    if not geometry or "coordinates" not in geometry:
        return 0.0, 0.0

    xs, ys = [], []

    def walk(coords):
        for c in coords:
            if isinstance(c[0], (int, float)):
                xs.append(c[0])
                ys.append(c[1])
            else:
                walk(c)

    walk(geometry["coordinates"])
    if not xs:
        return 0.0, 0.0
    return sum(xs) / len(xs), sum(ys) / len(ys)


def _heat_level(value: float | None) -> str:
    """Classify a SUHII value into a human-readable heat band."""
    if value is None:
        return "Unknown ⬜"
    if value >= 3.0:
        return "Critical 🟥"
    if value >= 1.5:
        return "High 🟧"
    if value >= 0.5:
        return "Moderate 🟨"
    return "Low ⬜"


def _records_from_geojson(city: str):
    for p in [
        DEMO_DIR  / f"{city}_heatmap_normalized.geojson",
        DEMO_DIR  / f"{city}_forecast_heatmap.geojson",
        DEMO_DIR  / f"{city}_heatmap.geojson",
        BOUNDS_DIR / f"{city}_grid.geojson",
    ]:
        if not p.exists():
            continue
        data = json.loads(p.read_text())
        feats = data.get("features", [])
        if not feats:
            continue

        records = []
        for i, feat in enumerate(feats, start=1):
            props    = feat.get("properties", {}) or {}
            geometry = feat.get("geometry",   {}) or {}
            lon, lat = _centroid_lon_lat(geometry)

            # Prefer normalized; fall back to raw; never invent a number
            suhii_night = safe_float(
                props.get("suhii_night_normalized",
                props.get("suhii_night"))
            )
            suhii_day = safe_float(props.get("suhii_day"))

            records.append({
                "rank":             i,
                "cell_id":          str(props.get("cell_id", f"C{i:04d}")),
                "lon":              round(lon, 5),
                "lat":              round(lat, 5),

                # SUHII — None when data is genuinely missing
                "suhii_night":      suhii_night,
                "suhii_day":        suhii_day,

                # LST — None when missing (not 38.2 / 28.4)
                "lst_day":          safe_float(props.get("lst_day")),
                "lst_night":        safe_float(props.get("lst_night")),

                # Heat bands — derived from real value (or "Unknown" if None)
                "heat_level_night": _heat_level(suhii_night),
                "heat_level_day":   _heat_level(suhii_day),

                # Land cover fractions — None when missing (not 0.55 / 0.12)
                "frac_built":       safe_float(props.get("frac_built")),
                "frac_tree":        safe_float(props.get("frac_tree")),
                "frac_water":       safe_float(props.get("frac_water")),
                "frac_crop":        safe_float(props.get("frac_crop")),
                "frac_grass":       safe_float(props.get("frac_grass")),
            })
        return records
    return []


def get_ranked_cells_service(
    city_id="nagpur",
    sort_by="suhii_night",
    limit=50,
    ascending=False,
):
    city = city_id.lower()
    records = _records_from_geojson(city)
    if not records:
        return []

    # Sort: push None values to the end regardless of direction
    reverse = not ascending
    key = sort_by if sort_by in (records[0] if records else {}) else "suhii_night"

    records = sorted(
        records,
        key=lambda r: (r.get(key) is None, r.get(key) or 0.0),
        reverse=reverse,
    )
    records = records[: max(1, int(limit))]
    for i, r in enumerate(records, start=1):
        r["rank"] = i
    return records


# Backwards-compatible alias
get_cell_rankings_service = get_ranked_cells_service


def get_cell_explanation_service(cell_id: str) -> dict:
    """
    Returns a REAL SHAP-based driver explanation for a cell, computed by
    models.explain.shap_explainer (LightGBM v1 TreeExplainer).

    Raises RuntimeError if required model/data files are missing
    (e.g. on a fresh clone without GEE-derived parquet tables).
    The caller must NOT fall back to fabricated numbers on this error.
    """
    try:
        result = _shap.explain_cell(cell_id)
    except FileNotFoundError as e:
        raise RuntimeError(
            f"SHAP explanation unavailable: required data/model file missing ({e})"
        )
    result.pop("_source_city", None)
    return result
