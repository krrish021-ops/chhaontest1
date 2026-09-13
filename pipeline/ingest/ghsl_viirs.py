"""
GHSL Building Height + VIIRS Night Lights extraction for Nagpur grid cells.

Sources:
  - JRC/GHSL/P2023A/GHS_BUILT_H (100m, epoch 2018 ImageCollection)
    Average building height in meters. Captures canyon geometry
    that traps heat at night (TRD §B.7 Sky View Factor proxy).

  - NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG (500m, monthly ImageCollection)
    Average radiance in nanoWatts/cm²/sr. Proxy for anthropogenic
    heat (AC exhaust, industry, street lighting).

Outputs:
  data/tables/nagpur_ghsl_viirs.parquet
"""

import ee
import pandas as pd
import geopandas as gpd
import json
import numpy as np
from pathlib import Path

ee.Initialize(project="chhaon-508513")

DATA_DIR = Path("data/tables")
DATA_DIR.mkdir(parents=True, exist_ok=True)
GRID_PATH = "data/boundaries/nagpur_grid.geojson"


def main():
    print("=" * 65)
    print("  GHSL BUILDING HEIGHT + VIIRS NIGHT LIGHTS (v2)")
    print("=" * 65)

    # Load grid
    print(f"\n[1/4] Loading grid...")
    grid_gdf = gpd.read_file(GRID_PATH)
    n_cells = len(grid_gdf)
    print(f"  ✓ {n_cells} cells")
    grid_fc = ee.FeatureCollection(json.loads(grid_gdf.to_json()))

    # ── GHSL Building Height ─────────────────────────────────────────
    print(f"\n[2/4] Extracting GHSL Building Height (100m, 2018)...")
    # FIX: JRC/GHSL/P2023A/GHS_BUILT_H is an ImageCollection.
    # Take mosaic and select the first band (built_height), rename explicitly.
    ghsl_collection = ee.ImageCollection("JRC/GHSL/P2023A/GHS_BUILT_H")
    ghsl_h = ghsl_collection.mosaic().select(0).rename("built_height")

    # Mask out zeros (no buildings) to avoid diluting mean height with open space
    ghsl_h_masked = ghsl_h.updateMask(ghsl_h.gt(0))

    ghsl_extracted = ghsl_h_masked.reduceRegions(
        collection=grid_fc,
        reducer=ee.Reducer.mean().combine(ee.Reducer.max(), "", True)
        .combine(ee.Reducer.stdDev(), "", True),
        scale=100,
    )

    ghsl_info = ghsl_extracted.getInfo()
    print(f"  ✓ GHSL extraction complete")

    # ── VIIRS Night Lights ───────────────────────────────────────────
    print(f"\n[3/4] Extracting VIIRS Night Lights (500m, May 2024)...")
    viirs = (
        ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG")
        .filterDate("2024-04-01", "2024-06-01")
        .select("avg_rad")
    )

    # Median composite across pre-monsoon months, rename band explicitly
    viirs_composite = viirs.median().rename("night_lights")

    viirs_extracted = viirs_composite.reduceRegions(
        collection=grid_fc,
        reducer=ee.Reducer.mean().combine(ee.Reducer.max(), "", True),
        scale=500,
    )

    viirs_info = viirs_extracted.getInfo()
    print(f"  ✓ VIIRS extraction complete")

    # ── Merge and save ───────────────────────────────────────────────
    print(f"\n[4/4] Merging and saving...")

    all_rows = []
    for ghsl_feat, viirs_feat in zip(
        ghsl_info["features"], viirs_info["features"]
    ):
        gp = ghsl_feat["properties"]
        vp = viirs_feat["properties"]

        cell_id = gp.get("cell_id", vp.get("cell_id", ""))

        # GHSL height stats (band was renamed to "built_height")
        h_mean = gp.get("built_height_mean")
        h_max = gp.get("built_height_max")
        h_std = gp.get("built_height_stdDev")

        # VIIRS radiance stats (band was renamed to "night_lights")
        ntl_mean = vp.get("night_lights_mean")
        ntl_max = vp.get("night_lights_max")

        all_rows.append(
            {
                "cell_id": cell_id,
                "building_height_mean": round(h_mean, 2)
                if h_mean is not None else 0.0,
                "building_height_max": round(h_max, 2)
                if h_max is not None else 0.0,
                "building_height_std": round(h_std, 2)
                if h_std is not None else 0.0,
                "night_lights_mean": round(ntl_mean, 2)
                if ntl_mean is not None else 0.0,
                "night_lights_max": round(ntl_max, 2)
                if ntl_max is not None else 0.0,
            }
        )

    df = pd.DataFrame(all_rows)

    # Compute derived morphological features
    # Street canyon proxy: Height-to-Width ratio assuming ~15m street width in Indian cities
    df["height_to_width_ratio"] = (
        df["building_height_mean"] / 15.0
    ).round(3)

    # Sky View Factor proxy (TRD §B.7): SVF ≈ 1 - (H/W) * 0.5, clamped to [0.05, 1.0]
    # Lower SVF = deeper canyon = more heat trapped at night
    df["svf_proxy"] = (
        1.0 - df["height_to_width_ratio"] * 0.5
    ).clip(0.05, 1.0).round(3)

    out_path = DATA_DIR / "nagpur_ghsl_viirs.parquet"
    df.to_parquet(out_path, index=False)

    print(f"\n  ✓ Saved to {out_path}")
    print("=" * 65)
    print("  GHSL + VIIRS SUMMARY")
    print("=" * 65)
    print(f"  Rows: {len(df)}")
    print(f"\n  Building Height (GHSL, 2018):")
    print(f"    Mean height:   {df['building_height_mean'].mean():.1f} m"
          f" (range {df['building_height_mean'].min():.1f}–"
          f"{df['building_height_mean'].max():.1f} m)")
    print(f"    Max height:    {df['building_height_max'].max():.1f} m")
    print(f"    Mean SVF:      {df['svf_proxy'].mean():.3f}"
          f" (1.0 = open sky, 0.05 = deep canyon)")

    print(f"\n  Night Lights (VIIRS, May 2024):")
    print(f"    Mean radiance: {df['night_lights_mean'].mean():.1f}"
          f" nW/cm²/sr (range {df['night_lights_mean'].min():.1f}–"
          f"{df['night_lights_mean'].max():.1f})")

    print(f"\n  Urban Morphology Signals Detected:")
    print(f"    Cells with building height > 5m: {(df['building_height_mean'] > 5).sum()}")
    print(f"    Cells with high night radiance (>10): {(df['night_lights_mean'] > 10).sum()}")
    print("=" * 65)


if __name__ == "__main__":
    main()
