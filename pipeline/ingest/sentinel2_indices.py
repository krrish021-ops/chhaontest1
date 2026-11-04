"""
Sentinel-2 spectral indices extraction for Nagpur grid cells.
Computes NDVI, NDBI, MNDWI, UI, and broadband albedo from a
cloud-free May 2024 composite.

Source: COPERNICUS/S2_SR_HARMONIZED (10-20m, 5-day revisit)
Cloud mask: SCL (Scene Classification Layer) — removes clouds, shadows, cirrus
Purpose: Spectral features for ML model (TRD §5.1)

Outputs:
  data/tables/nagpur_sentinel2_indices.parquet
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

# Use May 2024 — peak heat, pre-monsoon, most cloud-free window
YEAR = 2024
MONTH_START = "2024-04-15"
MONTH_END = "2024-06-15"


def mask_clouds_scl(img):
    """
    Cloud mask using Sentinel-2 Scene Classification Layer (SCL).
    SCL classes:
      0 = No Data, 1 = Saturated/Defective
      2 = Dark Area Pixels, 3 = Cloud Shadows
      4 = Vegetation, 5 = Not Vegetated (bare soil)
      6 = Water, 7 = Unclassified
      8 = Cloud Medium Probability
      9 = Cloud High Probability
      10 = Thin Cirrus, 11 = Snow/Ice

    Keep: 2, 4, 5, 6, 7 (clear-sky surface classes)
    Remove: 0, 1, 3, 8, 9, 10, 11 (clouds, shadows, artifacts)
    """
    scl = img.select("SCL")
    clear_mask = (
        scl.eq(2).Or(scl.eq(4)).Or(scl.eq(5))
        .Or(scl.eq(6)).Or(scl.eq(7))
    )
    return img.updateMask(clear_mask)


def compute_indices(img):
    """
    Compute spectral indices from a cloud-masked Sentinel-2 image.
    All bands are surface reflectance × 10000 (harmonized).

    Band mapping (Sentinel-2 MSI):
      B2 = Blue (10m), B3 = Green (10m), B4 = Red (10m)
      B8 = NIR (10m), B11 = SWIR1 (20m), B12 = SWIR2 (20m)
    """
    blue = img.select("B2").divide(10000)
    green = img.select("B3").divide(10000)
    red = img.select("B4").divide(10000)
    nir = img.select("B8").divide(10000)
    swir1 = img.select("B11").divide(10000)
    swir2 = img.select("B12").divide(10000)

    # NDVI: Normalized Difference Vegetation Index
    # Range [-1, 1]. High = dense healthy vegetation.
    ndvi = nir.subtract(red).divide(nir.add(red)).rename("ndvi")

    # NDBI: Normalized Difference Built-up Index
    # Range [-1, 1]. High = impervious/built-up surface.
    ndbi = swir1.subtract(nir).divide(swir1.add(nir)).rename("ndbi")

    # MNDWI: Modified Normalized Difference Water Index
    # Range [-1, 1]. High = open water. Better than NDWI for urban areas.
    mndwi = green.subtract(swir1).divide(green.add(swir1)).rename("mndwi")

    # UI: Urban Index
    # Range [-1, 1]. High = dense urban fabric.
    ui = swir2.subtract(nir).divide(swir2.add(nir)).rename("ui")

    # Broadband albedo (Liang 2001, adapted for Sentinel-2)
    # Range [0, 1]. High = reflective surface (cool roof, sand).
    # Coefficients from Liang 2001 Table 3, adjusted for S2 band centers.
    albedo = (
        blue.multiply(0.356)
        .add(red.multiply(0.130))
        .add(nir.multiply(0.373))
        .add(swir1.multiply(0.085))
        .add(swir2.multiply(0.072))
        .subtract(0.0018)
        .rename("albedo")
    )

    return ndvi.addBands(ndbi).addBands(mndwi).addBands(ui).addBands(albedo)


def main():
    print("=" * 65)
    print("  SENTINEL-2 SPECTRAL INDICES EXTRACTION")
    print(f"  Source: COPERNICUS/S2_SR_HARMONIZED")
    print(f"  Period: {MONTH_START} to {MONTH_END}")
    print(f"  Indices: NDVI, NDBI, MNDWI, UI, Albedo")
    print("=" * 65)

    # Load grid
    print(f"\n[1/4] Loading grid...")
    grid_gdf = gpd.read_file(GRID_PATH)
    n_cells = len(grid_gdf)
    print(f"  ✓ {n_cells} cells")
    grid_fc = ee.FeatureCollection(json.loads(grid_gdf.to_json()))

    # Load and cloud-mask Sentinel-2
    print(f"\n[2/4] Loading Sentinel-2 imagery...")
    s2 = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(grid_fc.geometry())
        .filterDate(MONTH_START, MONTH_END)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
        .map(mask_clouds_scl)
    )

    n_images = s2.size().getInfo()
    print(f"  ✓ {n_images} cloud-filtered scenes found")

    if n_images == 0:
        print("  ⚠ No scenes available — try a different date range")
        return

    # Compute indices and take median composite
    print(f"\n[3/4] Computing indices and compositing...")
    indices_collection = s2.map(compute_indices)
    composite = indices_collection.median()

    # Also compute pixel count for quality
    count = indices_collection.select("ndvi").count().rename("n_valid_pixels")
    composite = composite.addBands(count)

    # Extract to grid cells
    # Sentinel-2 is 10-20m, but we reduce at 100m to match our modelling grid
    extracted = composite.reduceRegions(
        collection=grid_fc,
        reducer=ee.Reducer.mean(),
        scale=100,
    )

    info = extracted.getInfo()

    all_rows = []
    for feat in info["features"]:
        p = feat["properties"]
        all_rows.append(
            {
                "cell_id": p.get("cell_id", ""),
                "ndvi": round(p.get("ndvi", np.nan), 4)
                if p.get("ndvi") is not None else np.nan,
                "ndbi": round(p.get("ndbi", np.nan), 4)
                if p.get("ndbi") is not None else np.nan,
                "mndwi": round(p.get("mndwi", np.nan), 4)
                if p.get("mndwi") is not None else np.nan,
                "ui": round(p.get("ui", np.nan), 4)
                if p.get("ui") is not None else np.nan,
                "albedo": round(p.get("albedo", np.nan), 4)
                if p.get("albedo") is not None else np.nan,
                "s2_n_valid_pixels": int(p.get("n_valid_pixels", 0) or 0),
            }
        )

    df = pd.DataFrame(all_rows)

    # Save
    out_path = DATA_DIR / "nagpur_sentinel2_indices.parquet"
    df.to_parquet(out_path, index=False)

    print(f"\n[4/4] Saved to {out_path}")
    print("=" * 65)
    print("  SENTINEL-2 INDICES SUMMARY")
    print("=" * 65)
    print(f"  Rows: {len(df)}")
    for col in ["ndvi", "ndbi", "mndwi", "ui", "albedo"]:
        valid = df[col].notna().sum()
        if valid > 0:
            print(f"  {col:<8} range: {df[col].min():+.4f} to {df[col].max():+.4f}"
                  f"  (mean {df[col].mean():+.4f}, {valid}/{len(df)} valid)")
        else:
            print(f"  {col:<8} ⚠ ALL NULL")
    print("=" * 65)


if __name__ == "__main__":
    main()
