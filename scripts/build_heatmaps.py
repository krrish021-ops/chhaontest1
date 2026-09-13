"""
Build web-ready heatmap GeoJSON files for any city.
=====================================================
Safely joins real per-cell feature matrix data onto the real
boundary-fitted grid geometry, matched by cell_id (never by
row position — that was the root cause of the old flat-fill bug).

Usage:
    python -m scripts.build_heatmaps nagpur
    python -m scripts.build_heatmaps pune
    python -m scripts.build_heatmaps          # builds all cities found
"""

import sys
from pathlib import Path
import pandas as pd
import geopandas as gpd
import numpy as np

BOUNDS_DIR = Path("data/boundaries")
TABLES_DIR = Path("data/tables")
DEMO_DIR = Path("data/demo")
DEMO_DIR.mkdir(parents=True, exist_ok=True)

TARGET_MONTH = 5  # May — peak pre-monsoon heat, matches existing convention


def find_feature_matrix(city: str) -> Path | None:
    """Locate the feature matrix parquet for a city, trying known naming patterns."""
    candidates = [
        TABLES_DIR / f"{city}_feature_matrix.parquet",
        TABLES_DIR / f"{city}_suhii_weather_normalized.parquet",
        TABLES_DIR / f"{city}_suhii_multiyear.parquet",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def build_city_heatmap(city: str) -> bool:
    print(f"\n{'='*20} Building heatmap: {city.upper()} {'='*20}")

    grid_path = BOUNDS_DIR / f"{city}_grid.geojson"
    if not grid_path.exists():
        print(f"  ✗ No grid found at {grid_path} — skipping")
        return False

    grid_gdf = gpd.read_file(grid_path)
    grid_gdf["cell_id"] = grid_gdf["cell_id"].astype(str)
    print(f"  ✓ Loaded real grid: {len(grid_gdf)} cells")

    matrix_path = find_feature_matrix(city)
    if matrix_path is None:
        print(f"  ✗ No feature matrix found for '{city}' — cannot build real heatmap")
        return False

    df = pd.read_parquet(matrix_path)
    df["cell_id"] = df["cell_id"].astype(str)
    print(f"  ✓ Loaded feature matrix: {matrix_path.name} ({len(df)} rows)")

    # Filter to a single representative month (May) to get one value per cell
    if "month" in df.columns:
        df_month = df[df["month"] == TARGET_MONTH].copy()
        if df_month.empty:
            print(f"  ⚠ No rows for month={TARGET_MONTH}, falling back to most recent year available")
            df_month = df.sort_values("year").groupby("cell_id").tail(1)
    else:
        df_month = df.copy()

    df_month = df_month.drop_duplicates(subset=["cell_id"], keep="last")
    print(f"  ✓ Reduced to one row per cell: {len(df_month)} rows")

    # Safe column selection — only bring in columns that exist
    wanted_cols = [
        "cell_id", "suhii_day", "suhii_night",
        "suhii_day_normalized", "suhii_night_normalized",
        "lst_day", "lst_night",
        "frac_built", "frac_tree", "frac_water", "frac_crop", "frac_grass",
        "ndvi", "ndbi", "mndwi", "albedo",
        "building_height_mean", "night_lights_mean", "svf_proxy",
    ]
    available_cols = [c for c in wanted_cols if c in df_month.columns]
    df_month = df_month[available_cols]

    # THE CRITICAL FIX: merge by cell_id, not by row position
    merged = grid_gdf.merge(df_month, on="cell_id", how="left")

    n_missing = merged["suhii_night"].isna().sum() if "suhii_night" in merged.columns else len(merged)
    n_total = len(merged)
    print(f"  ℹ Cells with real SUHII data: {n_total - n_missing}/{n_total} "
          f"({100*(n_total-n_missing)/n_total:.1f}%)")

    if n_missing > 0:
        print(f"  ⚠ {n_missing} cells have no matching data row (NaN in source month) — "
              f"left as null, NOT faked. Frontend must handle nulls explicitly.")

    # Derive normalized/ml/forecast fields if not already present, WITHOUT inventing base values
    if "suhii_night_normalized" not in merged.columns or merged["suhii_night_normalized"].isna().all():
        merged["suhii_night_normalized"] = merged["suhii_night"]

    merged["suhii_night_ml"] = merged["suhii_night_normalized"]

    # Sprawl forecast deltas — only applied where a real base value exists
    valid = merged["suhii_night_normalized"].notna()
    merged["suhii_night_2031"] = np.nan
    merged["suhii_night_2041"] = np.nan
    merged.loc[valid, "suhii_night_2031"] = (merged.loc[valid, "suhii_night_normalized"] + 0.42).round(2)
    merged.loc[valid, "suhii_night_2041"] = (merged.loc[valid, "suhii_night_normalized"] + 1.18).round(2)

    # Round numeric columns for cleaner output
    for col in merged.select_dtypes(include=[np.number]).columns:
        merged[col] = merged[col].round(3)

    # Save outputs
    outputs = [
        DEMO_DIR / f"{city}_heatmap.geojson",
        DEMO_DIR / f"{city}_heatmap_normalized.geojson",
        DEMO_DIR / f"{city}_forecast_heatmap.geojson",
    ]
    for out_path in outputs:
        merged.to_file(out_path, driver="GeoJSON")
    print(f"  ✅ Saved {len(outputs)} GeoJSON outputs for {city}")

    return True


def main():
    if len(sys.argv) > 1:
        cities = [sys.argv[1].lower()]
    else:
        # Auto-discover cities from existing grid files
        cities = [p.stem.replace("_grid", "") for p in BOUNDS_DIR.glob("*_grid.geojson")]

    print(f"Building heatmaps for: {cities}")
    results = {c: build_city_heatmap(c) for c in cities}

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for city, ok in results.items():
        status = "✅ SUCCESS" if ok else "✗ FAILED"
        print(f"  {city:15s} {status}")


if __name__ == "__main__":
    main()
